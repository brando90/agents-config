#!/usr/bin/env python3
"""Exercise dispatch commands and false-success paths without SSH or agent calls."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPTS = Path(__file__).resolve().parent


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dispatch checks ")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}",
                        TEST_ROOT=str(self.root))
        # A site BASH_ENV can prepend real agent binaries ahead of our mocks.
        self.env.pop("BASH_ENV", None)
        self.env.pop("ENV", None)
        self.runbook = self.root / "task brief.md"
        self.runbook.write_text("# Probe\nTL;DR: Test dispatch without calling a model.\n")
        self.command("tmux", '''import json, os, sys
from pathlib import Path
root = Path(os.environ["TEST_ROOT"])
a = sys.argv[1:]
with (root / "tmux.jsonl").open("a") as f: f.write(json.dumps(a) + "\\n")
if a[0] == "has-session": sys.exit(int(os.environ.get("TEST_DUPLICATE", "1")))
if a[0] == "display-message": print("900" if "pane_pid" in a[-1] else "zsh")
if a[0] == "capture-pane": print("worker exited")
if a[0] == "new-session":
    rc = int(os.environ.get("TEST_LAUNCH_RC", "0"))
    if rc: sys.exit(rc)
    if os.environ.get("TEST_RUNNER"):
        import subprocess, shlex
        # Execute only the harmless shell fixture, recording the asynchronous job status.
        command = a[a.index("-s") + 2]
        runner = shlex.split(command)[-1]
        result = subprocess.run(["bash", runner])
        (root / "job.rc").write_text(str(result.returncode))
''')
        self.command("byobu", '''import os, sys
os.execvp("tmux", ["tmux", *sys.argv[1:]])
''')
        self.command("ps", '''import os
from pathlib import Path
print((Path(os.environ["TEST_ROOT"]) / "processes").read_text())
''')
        self.command("ssh", '''import json, os, subprocess, sys
from pathlib import Path
root = Path(os.environ["TEST_ROOT"])
a = sys.argv[1:]
with (root / "ssh.jsonl").open("a") as f: f.write(json.dumps(a) + "\\n")
if a[-1] == "true": sys.exit(0)
if "bash" in a:
    i = a.index("bash")
    args = a[i:]
    if len(args) > 3:
        # Substitute only the node-local directory: the transmitted program is unchanged.
        name, old_dir, old_log, payload = args[3:]
        logdir = root / "remote"
        args = ["bash", "-s", "--", name, str(logdir), str(logdir / Path(old_log).name), payload]
    sys.exit(subprocess.run(args, input=sys.stdin.read(), text=True).returncode)
if "has-session" in a[-1]: sys.exit(int(os.environ.get("TEST_DUPLICATE", "1")))
sys.exit(0)
''')

    def command(self, name, body):
        path = self.bin / name
        path.write_text(f"#!{sys.executable}\n{body}")
        path.chmod(0o755)

    def run_script(self, script, *args, **extra):
        return subprocess.run(["bash", str(SCRIPTS / script), *args], env=dict(self.env, **extra),
                              text=True, capture_output=True, timeout=15)

    def deploy(self, *args):
        return self.run_script("deploy_cc.sh", "--name", "qa-probe", "--cwd", str(self.root),
                               "--prompt-file", str(self.runbook), *args)

    def test_dry_run_replays_exact_typed_command_with_spaces(self):
        result = self.deploy("--profile", "codex", "--wait", "08", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = [shlex.split(line) for line in result.stdout.splitlines() if not line.startswith("#")]
        self.assertEqual(commands[0][commands[0].index("-c") + 1], str(self.root))
        typed = commands[1][-1]
        argv = shlex.split(typed)
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", argv)
        self.assertEqual(argv[argv.index("-m") + 1], "gpt-6-astra")
        self.assertEqual(argv[argv.index("-c") + 1], 'model_reasoning_effort="ultra"')
        self.assertIn("CKPT_qa-probe.md", argv[-1])
        self.assertIn(str(self.runbook), argv[-1])
        self.assertEqual(commands[1][:3], ["tmux", "send-keys", "-l"])
        for line in result.stdout.splitlines():
            if not line.startswith("#"):
                subprocess.run(["bash", "-c", line], env=self.env, check=True)
        actual = [json.loads(line) for line in (self.root / "tmux.jsonl").read_text().splitlines()]
        self.assertEqual(actual[1], commands[1][1:])
        self.assertEqual(actual[2], ["send-keys", "-t", "=qa-probe:", "Enter"])

    def test_deploy_profiles_and_invalid_flags(self):
        for profile, wrapper in [("cc", "clauded"), ("ccv", "clauded-vals")]:
            result = self.deploy("--profile", profile, "--no-rc", "--model", "claude-fable-5-1[1m]", "--effort", "max", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            typed = shlex.split(result.stdout.splitlines()[1])[-1]
            self.assertEqual(shlex.split(typed)[0], wrapper)
            self.assertNotIn("--remote-control", typed)
        for args in [("--model",), ("--effort", "bogus"), ("--profile", "bad"), ("--wait", "-1")]:
            self.assertEqual(self.deploy(*args).returncode, 2)
        result = self.run_script("deploy_cc.sh", "--dry-run", "--name", "qa-probe", "--cwd", "/tmp", "--prompt-file", "/dev/null")
        self.assertEqual(result.returncode, 2)

    def process_line(self, pid, parent, command, state="S", started=None):
        stamp = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime(started or time.time()))
        return f"{pid} {parent} {state} {stamp} {command}\n"

    def identity(self, lines, registry=None):
        (self.root / "processes").write_text("".join(lines))
        source = (SCRIPTS / "deploy_cc.sh").read_text().split("<<'PYTHON'\n", 1)[1].split("\nPYTHON\n", 1)[0]
        return subprocess.run([sys.executable, "-c", source, "900", "clauded" if registry else "codex",
                               str(self.runbook), str(registry or ""), "qa-probe"],
                              text=True, capture_output=True, env=self.env, timeout=5)

    def test_codex_identity_rejects_unrelated_zombie_wrong_parent_and_missing_marker(self):
        good = self.process_line("901", "900", f"/opt/codex {self.runbook}")
        self.assertEqual(self.identity([good]).returncode, 0)
        for line in [self.process_line("901", "900", f"cat {self.runbook}"),
                     self.process_line("901", "900", f"/opt/codex {self.runbook}", "Z"),
                     self.process_line("901", "1", f"/opt/codex {self.runbook}"),
                     self.process_line("901", "900", "/opt/codex --version"),
                     self.process_line("901", "900", f"bash -c 'echo codex {self.runbook}'")]:
            self.assertEqual(self.identity([line]).returncode, 1, line)
        self.assertEqual(self.identity([self.process_line("900", "1", f"codex {self.runbook}")]).returncode, 0)
        for executable in ["/opt/codex.exe", "node /opt/lib/node_modules/@openai/codex/bin/codex.js"]:
            self.assertEqual(self.identity([self.process_line("901", "900", f"{executable} {self.runbook}")]).returncode, 0)

    def test_claude_registry_rejects_stale_recycled_and_zombie_processes(self):
        registry = self.root / "registry"
        registry.mkdir()
        stamp = int(time.time())
        entry = {"pid": 901, "sessionId": "abcdefgh-1234", "tmux": "qa-probe:@1.%1", "startedAt": stamp * 1000}
        path = registry / "901.json"
        path.write_text(json.dumps(entry))
        good = self.process_line("901", "900", "claude --model claude-fable-5-1", started=stamp)
        self.assertEqual(self.identity([good], registry).returncode, 0)
        for line in [self.process_line("901", "1", "claude", started=stamp),
                     self.process_line("901", "900", "sleep 100", started=stamp),
                     self.process_line("901", "900", "claude", "Z", stamp),
                     self.process_line("901", "900", "claude", started=stamp-300)]:
            self.assertEqual(self.identity([line], registry).returncode, 1, line)
        for executable in ["/opt/claude.exe", "node /opt/lib/node_modules/@anthropic-ai/claude-code/cli.js"]:
            self.assertEqual(self.identity([self.process_line("901", "900", executable, started=stamp)], registry).returncode, 0)
        fallback = dict(entry)
        fallback.pop("startedAt")
        fallback["procStart"] = time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(stamp))
        path.write_text(json.dumps(fallback))
        self.assertEqual(self.identity([good], registry).returncode, 0)
        path.write_text(json.dumps(dict(entry, tmux="other:@1.%1")))
        self.assertEqual(self.identity([good], registry).returncode, 1)

    def test_registered_rechecks_process_identity_after_startup(self):
        source = (SCRIPTS / "deploy_cc.sh").read_text()
        functions = "worker_identity() {" + source.split("worker_identity() {", 1)[1].split("deadline=$((SECONDS + WAIT))", 1)[0]
        first = self.process_line("901", "900", f"codex {self.runbook}")
        second = self.process_line("901", "900", f"codex {self.runbook}", "Z")
        (self.root / "processes").write_text(first)
        self.command("ps", '''import os
from pathlib import Path
root = Path(os.environ["TEST_ROOT"])
flag = root / "ps-read"
print((root / ("second-processes" if flag.exists() else "processes")).read_text())
flag.touch()
''')
        for stable in [True, False]:
            (self.root / "ps-read").unlink(missing_ok=True)
            (self.root / "second-processes").write_text(first if stable else second)
            env = dict(self.env, NAME="qa-probe", WRAPPER="codex", PROMPT=str(self.runbook), REG_DIR="")
            result = subprocess.run(["bash", "-c", functions + "registered"], env=env,
                                    text=True, capture_output=True, timeout=8)
            self.assertEqual(result.returncode, 0 if stable else 1, result.stderr)

    def test_dead_deploy_returns_one_and_preserves_diagnostics(self):
        (self.root / "processes").write_text("")
        result = self.deploy("--profile", "codex", "--wait", "1")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("NOT verified", result.stderr)
        self.assertIn("discard:", result.stderr)








if __name__ == "__main__":
    unittest.main(verbosity=2)
