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

    def test_identity_accepts_pinned_copies_and_quoted_prompts(self):
        """Trigger Rule 46 runs a worker from a private per-node COPY of the binary
        (`claude-pinned`), and a prompt routinely contains an apostrophe. Neither may
        make a live worker read as dead; a merely similar name still must not pass."""
        registry = self.root / "registry"
        registry.mkdir()
        stamp = int(time.time())
        (registry / "901.json").write_text(json.dumps(
            {"pid": 901, "sessionId": "abcdefgh-1234", "tmux": "qa-probe:@1.%1",
             "startedAt": stamp * 1000}))
        for command in ["/lfs/h/0/u/bin/claude-pinned --dangerously-skip-permissions",
                        "claude -p Brando's task, the one he didn't finish",
                        "/lfs/h/0/u/bin/claude-pinned -p Brando's task"]:
            self.assertEqual(
                self.identity([self.process_line("901", "900", command, started=stamp)],
                              registry).returncode, 0, command)
        for command in ["/opt/claudette --model claude-fable-5-1", "/opt/notclaude -p x"]:
            self.assertEqual(
                self.identity([self.process_line("901", "900", command, started=stamp)],
                              registry).returncode, 1, command)
        for command in [f"/opt/codex-pinned {self.runbook}",
                        f"/opt/codex {self.runbook} finish Brando's task"]:
            self.assertEqual(self.identity([self.process_line("901", "900", command)]).returncode,
                             0, command)
        self.assertEqual(self.identity(
            [self.process_line("901", "900", f"/opt/codexicon {self.runbook}")]).returncode, 1)

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

    def test_snap_rejects_invalid_names_and_hosts_before_ssh(self):
        for action in ["run", "tail", "log", "attach", "kill"]:
            for name in ["qa.probe", "qa'probe", "-qa", "qa:1"]:
                args = [action, name] + (["true"] if action == "run" else [])
                self.assertEqual(self.run_script("snap_dispatch.sh", *args).returncode, 1)
        self.assertEqual(self.run_script("snap_dispatch.sh", "run", "qa-probe", "true", SNAP_HOST="unknown").returncode, 1)
        self.assertFalse((self.root / "ssh.jsonl").exists())

    def test_snap_duplicate_and_remote_failure_are_not_success(self):
        duplicate = self.run_script("snap_dispatch.sh", "run", "qa-probe", "true", TEST_DUPLICATE="0")
        self.assertEqual(duplicate.returncode, 1)
        self.assertIn("already running", duplicate.stderr)
        failed = self.run_script("snap_dispatch.sh", "run", "qa-probe", "true", TEST_LAUNCH_RC="43")
        self.assertEqual(failed.returncode, 43, failed.stderr)
        self.assertNotIn("Safe to close", failed.stdout)
        self.assertFalse((self.root / "remote" / "qa-probe_latest.log").exists())

    def test_snap_preserves_explicit_failure_status_and_remote_log(self):
        result = self.run_script("snap_dispatch.sh", "run", "qa-probe", "exit 7", TEST_RUNNER="1")
        self.assertEqual(result.returncode, 0, result.stderr)  # Detached launch succeeded; job failed.
        self.assertEqual((self.root / "job.rc").read_text(), "7")
        log = (self.root / "remote" / "qa-probe_latest.log").read_text()
        self.assertIn("exit=7", log)
        self.assertIn("/lfs/skampere1/0/brando9/snap_jobs/", result.stdout)
        self.assertFalse((self.root / "remote" / ".qa-probe.launch-lock").exists())

    def test_snap_argv_and_exact_targets(self):
        result = self.run_script("snap_dispatch.sh", "run", "qa-probe", "printf", "%s", "a b; literal", TEST_RUNNER="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("a b; literal", (self.root / "remote" / "qa-probe_latest.log").read_text())
        for action in ["tail", "log", "attach", "kill"]:
            self.assertEqual(self.run_script("snap_dispatch.sh", action, "qa-probe").returncode, 0)
        calls = [json.loads(line) for line in (self.root / "ssh.jsonl").read_text().splitlines()]
        self.assertTrue(all("brando9@skampere1.stanford.edu" in call for call in calls))
        self.assertTrue(any("tmux attach -t '=qa-probe'" == call[-1] for call in calls))
        self.assertTrue(any("tmux kill-session -t '=qa-probe'" in call[-1] for call in calls))
        for account in ["brando9", "qa-account"]:
            result = self.run_script("snap_dispatch.sh", "run", "qa-account-probe", "true", SNAP_SSH_USER=account)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"/lfs/skampere1/0/{account}/snap_jobs/", result.stdout)
            for action in ["tail", "attach", "kill"]:
                self.assertIn(f"SNAP_HOST=skampere1 SNAP_SSH_USER={account} {SCRIPTS / 'snap_dispatch.sh'} {action} qa-account-probe", result.stdout)
            latest_call = json.loads((self.root / "ssh.jsonl").read_text().splitlines()[-1])
            self.assertIn(f"{account}@skampere1.stanford.edu", latest_call)

    def test_snap_remote_duplicate_race_keeps_existing_files(self):
        # Local preflight says absent, but remote recheck sees an existing session.
        self.command("ssh", '''import os, subprocess, sys
from pathlib import Path
a = sys.argv[1:]
if a[-1] == "true" or "has-session" in a[-1]: sys.exit(0 if a[-1] == "true" else 1)
i = a.index("bash")
name, logdir, log, payload = a[i+3:]
root = Path(os.environ["TEST_ROOT"]) / "remote"
args = ["bash", "-s", "--", name, str(root), str(root / "new.log"), payload]
sys.exit(subprocess.run(args, input=sys.stdin.read(), text=True).returncode)
''')
        remote = self.root / "remote"
        remote.mkdir()
        old = remote / "qa-probe_latest.log"
        old.write_text("existing job log")
        result = self.run_script("snap_dispatch.sh", "run", "qa-probe", "true", TEST_DUPLICATE="0")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(old.read_text(), "existing job log")
        self.assertEqual([path.name for path in remote.iterdir()], [old.name])

    def test_health_smoke_uses_current_models_without_model_calls(self):
        for name in ["claude", "codex"]:
            self.command(name, '''import json, os, sys
from pathlib import Path
root = Path(os.environ["TEST_ROOT"])
a = sys.argv[1:]
(root / (Path(sys.argv[0]).name + ".args")).write_text(json.dumps(a))
if "--output-last-message" in a:
    Path(a[a.index("--output-last-message") + 1]).write_text("SNAP_CODEX_OK")
else: print("SNAP_CLAUDE_OK")
''')
        source = (SCRIPTS / "snap_health.sh").read_text()
        smoke = source.split("smoke_test() {", 1)[1].split("\nworker_main()", 1)[0]
        script = 'set -u\nDO_SMOKE=1\nemit() { printf "%s\\n" "$*"; }\ntool_repair() { :; }\nsmoke_test() {' + smoke + '\nsmoke_test fixture codex\nsmoke_test fixture claude\n'
        result = subprocess.run(["bash", "-c", script], env=self.env, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("PASS"), 2, result.stdout)
        claude = json.loads((self.root / "claude.args").read_text())
        # A liveness ping is not reasoning work, so it runs on Hard Rule 8's regular tier;
        # pinning the flagship here fails the whole node whenever its allowance is spent.
        self.assertEqual(claude[claude.index("--model")+1], "claude-sonnet-5")
        self.assertNotIn("--effort", claude)
        codex = json.loads((self.root / "codex.args").read_text())
        self.assertEqual(codex[codex.index("-m")+1], "gpt-6-astra")
        self.assertEqual(codex[codex.index("-c")+1], 'model_reasoning_effort="ultra"')


if __name__ == "__main__":
    unittest.main(verbosity=2)
