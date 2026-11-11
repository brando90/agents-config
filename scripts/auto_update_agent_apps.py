#!/usr/bin/env python3
"""Update installed Mac agent clients through their actual managers; never run a model."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import pty
import re
import select
import shlex
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import termios
import time

# These are maintenance subcommands verified against the installed clients' help.
# Do not add positional prompts, forced restarts, bulk plugin flags, or channel changes.
NATIVE = {
    "pi": ("update", "--self", "--no-approve"),
    "claude": ("update",),
    "cursor-agent": ("update",),
    "herdr": ("update",),
    "omp": ("update",),
    "droid": ("update",),
    "kimi": ("update", "--yes"),
    "hermes": ("update", "--yes", "--no-gateway-restart"),
    "agy": ("update",),
    "grok": ("update",),
    "goose": ("update",),
    "cortex": ("update",),
    "harn": ("upgrade",),
    "kimchi": ("update", "--self", "--force"),  # --force accepts confirmation here.
    "stakpak": ("update",),
    "vtcode": ("update",),  # Its updater needs a terminal confirmation, not --force.
    "pool": ("update",),
    "openclaw": ("update", "--no-restart", "--timeout", "180"),
}
NPM = {
    "codex": "@openai/codex",
    "copilot": "@github/copilot",
    "kilo": "@kilocode/cli",
    "qodercli": "@qoder-ai/qodercli",
    "qwen": "@qwen-code/qwen-code",
    "mastracode": "mastracode",
    "opencode": "opencode-ai",
    "auggie": "@augmentcode/auggie",
}
UV = {
    "crow-cli": "crow-cli",
    "fast-agent-acp": "fast-agent-mcp",  # Official distribution; exports the ACP command.
    "minion-code": "minion-code",
    "vibe": "mistral-vibe",
}
# These launchers already check for updates on ordinary startup. A version probe
# is not represented as proof that their latest release was downloaded.
ON_LAUNCH = ("junie",)
# Integration artifacts / a locally repaired build are not ordinary global installs.
PRESERVED = ("amp-acp", "corust-agent-acp", "minimax-code-repaired")
VERSION = re.compile(r"(?<![\d.])\d+\.\d+(?:\.\d+)*(?:[-+][\w.-]+)?")


@dataclass
class Target:
    name: str
    kind: str
    executable: str = ""
    command: list[str] = field(default_factory=list)
    package: str = ""
    prefix: str = ""
    package_dir: str = ""


class Deferred(Exception):
    pass


def npm_installation(executable: str, package: str):
    """Infer the real global prefix, not whichever prefix `npm` currently defaults to."""
    resolved = Path(executable).resolve()
    for directory in resolved.parents:
        manifest = directory / "package.json"
        if not manifest.is_file():
            continue
        try:
            data = json.loads(manifest.read_text())
        except (OSError, ValueError):
            continue
        if data.get("name") != package:
            continue
        modules = directory.parent.parent if package.startswith("@") else directory.parent
        if modules.name == "node_modules" and modules.parent.name == "lib":
            return str(modules.parent.parent), str(directory)
    return None


def discover(home: Path) -> list[Target]:
    targets = []
    for name, args in NATIVE.items():
        if executable := shutil.which(name):
            targets.append(Target(name, "native", executable, [executable, *args]))
    brew = shutil.which("brew")
    for name, package in NPM.items():
        if not (executable := shutil.which(name)):
            continue
        install = npm_installation(executable, package)
        if install and (npm := shutil.which("npm")):
            prefix, package_dir = install
            targets.append(Target(name, "npm", executable, [npm], package, prefix, package_dir))
        elif brew and "/Cellar/" in str(Path(executable).resolve()):
            targets.append(Target(name, "brew", executable, [brew, "upgrade", name]))
        elif brew and "/Caskroom/" in str(Path(executable).resolve()):
            targets.append(Target(name, "brew", executable, [brew, "upgrade", "--cask", name]))
        else:
            targets.append(Target(name, "unresolved", executable))
    for name, package in UV.items():
        executable, uv = shutil.which(name), shutil.which("uv")
        if not executable:
            continue
        if uv and f"/uv/tools/{package}/" in str(Path(executable).resolve()):
            targets.append(Target(name, "uv", executable, [uv, "tool", "upgrade", package],
                                  package=package, prefix=str(Path(executable).resolve().parent.parent)))
        else:
            targets.append(Target(name, "unresolved", executable))
    if (executable := shutil.which("devin")) and brew:
        if "/Caskroom/devin-cli/" in str(Path(executable).resolve()):
            targets.append(Target("devin", "brew", executable, [brew, "upgrade", "--cask", "devin-cli"]))
        else:
            targets.append(Target("devin", "unresolved", executable))
    # Desktop apps, including Homebrew-enrolled Zed, use their native updaters.
    # A separate cask upgrade could race with someone opening the app.
    if executable := shutil.which("muse"):
        targets.append(Target("muse", "launcher", executable,
                              ["/usr/bin/env", "MUSE_SYNC_UPDATE=1", "MUSE_NO_AUTO_UPDATE=0", executable, "--version"]))
    for kind, names in (("on-launch", ON_LAUNCH), ("preserved", PRESERVED)):
        for name in names:
            if executable := shutil.which(name):
                targets.append(Target(name, kind, executable))
    return targets


def atomic_json(path: Path, data):
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(data, indent=2) + "\n")
        temporary.chmod(0o600)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def lock_path(home: Path):
    # Receipt locations may vary with XDG_STATE_HOME; package-manager exclusion must not.
    return home / ".local/state/agent-cli-updates/update.flock"


@contextmanager
def update_lock(path: Path):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open("a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def due(record, now, max_age, force=False):
    if force or not record:
        return True
    interval = max_age if record.get("status") in {"checked", "updated", "on-launch", "preserved"} else 3600
    return now - record.get("attempted_at", 0) >= interval


def run_command(argv, *, cwd, log, timeout=300, env=None):
    """Bound the whole child process group, not just the npm/native parent."""
    log.write("\n$ " + shlex.join(map(str, argv)) + "\n")
    log.flush()
    proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, errors="replace",
                            start_new_session=True, env=env)
    try:
        output, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            output, _ = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            output, _ = proc.communicate()
        log.write(output + f"\nTIMEOUT after {timeout:g}s\n")
        log.flush()
        raise RuntimeError("updater timed out; its child process group was stopped")
    log.write(output)
    log.flush()
    if proc.returncode:
        raise RuntimeError(f"command exited {proc.returncode}; see private log")
    return output


def run_confirmed_command(argv, *, cwd, log, timeout, env, pattern):
    """Answer only the vendor's known install prompt, in an invisible pseudo-terminal."""
    log.write("\n$ " + shlex.join(argv) + " [terminal confirmation]\n")
    log.flush()
    master, slave = pty.openpty()
    def controlling_terminal():
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)
    try:
        # This maintenance program is single-threaded. The child obtains its own
        # session/controlling terminal; its whole group remains timeout-bounded.
        proc = subprocess.Popen(argv, cwd=cwd, stdin=slave, stdout=slave, stderr=slave,
                                start_new_session=True, preexec_fn=controlling_terminal, env=env)
    except BaseException:
        os.close(master)
        raise
    finally:
        os.close(slave)
    deadline, output, answered = time.monotonic() + timeout, bytearray(), False
    completed = False
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("terminal updater timed out or requested an unexpected confirmation")
            ready, _, _ = select.select([master], [], [], min(0.2, remaining))
            if ready:
                try:
                    chunk = os.read(master, 65536)
                except OSError as exc:
                    if exc.errno != 5:  # EIO is the usual terminal-close indication.
                        raise
                    break
                if not chunk:
                    break
                output.extend(chunk)
                log.write(chunk.decode(errors="replace"))
                log.flush()
                text = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", output.decode(errors="replace"))
                if not answered and re.search(pattern, text):
                    os.write(master, b"y\r")
                    answered = True
            # Wait for terminal closure even if the parent exits first: an
            # updater child may still hold the terminal or await confirmation.
        proc.wait(timeout=max(0.1, deadline - time.monotonic()))
        if proc.returncode:
            raise RuntimeError(f"terminal updater exited {proc.returncode}; see private log")
        # macOS can revoke the terminal when its session leader exits, while an
        # orphaned child still runs. Keep the update lock until that group ends.
        while True:
            try:
                os.killpg(proc.pid, 0)
            except ProcessLookupError:
                break
            if time.monotonic() >= deadline:
                raise TimeoutError("terminal updater timed out waiting for child processes")
            time.sleep(0.05)
        completed = True
        return output.decode(errors="replace")
    finally:
        try:
            if not completed:
                for sig in (signal.SIGTERM, signal.SIGKILL):
                    try:
                        os.killpg(proc.pid, sig)
                    except ProcessLookupError:
                        pass
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        pass
        finally:
            os.close(master)
            log.flush()


class Updater:
    def __init__(self, home, state, log, deadline):
        self.home, self.state, self.log, self.deadline = home, state, log, deadline
        self.work = state / "work"
        self.work.mkdir(exist_ok=True)
        self.brew_refreshed = False
        self.env = dict(os.environ)
        # Updaters do not need model-provider credentials from this agent session.
        for key in list(self.env):
            if key.endswith(("_API_KEY", "_SECRET", "_PASSWORD")) or key.startswith("PI_"):
                self.env.pop(key)
        self.env.update(NO_COLOR="1", HOMEBREW_NO_AUTO_UPDATE="1", npm_config_update_notifier="false")

    def run(self, command, timeout=300, confirmation=None):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise Deferred("run time budget reached; retry on the next scheduled pass")
        options = dict(cwd=self.work, log=self.log, timeout=min(timeout, remaining), env=self.env)
        if confirmation is not None:
            return run_confirmed_command(command, pattern=confirmation, **options)
        return run_command(command, **options)

    def version(self, target):
        # These clients do not implement --version. Never let that become a
        # headless agent invocation: query their installed distribution metadata.
        if target.name == "mastracode":
            self.run([target.executable, "--help"], 30)
            return json.loads((Path(target.package_dir) / "package.json").read_text())["version"]
        if target.kind == "uv":
            self.run([target.executable, "--help"], 30)
            return self.run([str(Path(target.prefix) / "bin/python"), "-c",
                             "import importlib.metadata,sys; print(importlib.metadata.version(sys.argv[1]))",
                             target.package], 30).strip()
        command = [target.executable, "--version"]
        if target.name == "muse":
            command = ["/usr/bin/env", "MUSE_NO_AUTO_UPDATE=1", *command]
        output = self.run(command, timeout=30)
        match = VERSION.search(output)
        if not match:
            raise RuntimeError("client version could not be verified; see private log")
        return match.group(0)

    def guard(self, target):
        if target.kind == "native":
            help_text = self.run([target.executable, "--help"], 30)
            help_text = re.sub(r"\x1b\[[0-9;]*m", "", help_text)
            action = re.escape(target.command[1])
            name = re.escape(Path(target.executable).name)
            if not re.search(rf"(?m)^\s*(?:{name}\s+)?(?:[\w-]+\|)*{action}(?:\|[\w-]+)*(?:\s|$)", help_text):
                raise RuntimeError("maintenance subcommand is absent from help; no prompt was submitted")
        if target.name == "openclaw":
            version = self.version(target).split("-")[0].split("+")[0]
            if tuple(map(int, version.split("."))) < (2026, 7, 0):
                raise Deferred("pre-July OpenClaw requires its documented bridge migration before unattended updates")
        if target.name == "stakpak":
            processes = self.run(["/bin/ps", "-axo", "comm="], 15)
            if any(Path(line.strip()).name == "stakpak" for line in processes.splitlines()):
                raise Deferred("Stakpak is running; its native updater would restart autopilot")
        if target.name == "vtcode":
            config = self.run([target.executable, "update", "--show-config"], 30)
            config = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", config)
            pin = re.search(r"(?m)Pinned:\s*([^\n]+)", config)
            if not pin:
                raise RuntimeError("VT Code update-pin state could not be verified")
            if pin.group(1).strip() != "No":
                raise Deferred("VT Code version pin retained")
        if target.name == "hermes":
            repo = self.home / ".hermes/hermes-agent"
            if not (repo / ".git").exists():
                raise Deferred("Hermes source location is unrecognized; leave it intact")
            if self.run(["git", "-C", str(repo), "status", "--porcelain"], 30).strip():
                raise Deferred("Hermes source has local work; no stash or reset")

    def install_stakpak_release(self, target, release):
        """Mirror the native direct-binary update using the publisher's GitHub release."""
        tag = release.get("tag_name", "")
        if not re.fullmatch(r"v\d+\.\d+\.\d+", tag) or release.get("draft") or release.get("prerelease"):
            raise RuntimeError("invalid stable Stakpak release metadata")
        destination = Path(target.executable).resolve(strict=True)
        if "/Cellar/" in str(destination) or "/Caskroom/" in str(destination):
            brew = shutil.which("brew")
            if not brew:
                raise Deferred("Stakpak's Homebrew installation manager is unavailable")
            self.run([brew, "update"])
            self.run([brew, "upgrade", "stakpak"])
            if self.version(target) != tag[1:]:
                raise RuntimeError("Homebrew has not supplied the requested Stakpak release")
            return
        architecture = {"arm64": "aarch64", "aarch64": "aarch64", "x86_64": "x86_64"}.get(platform.machine())
        name = f"stakpak-darwin-{architecture}.tar.gz"
        asset = next((a for a in release.get("assets", []) if a.get("name") == name), None)
        url = f"https://github.com/stakpak/agent/releases/download/{tag}/{name}"
        if not asset or asset.get("browser_download_url") != url:
            raise RuntimeError("the official Stakpak release has no matching Mac binary")
        original_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix=".stakpak-update-", dir=destination.parent) as temporary:
            temporary = Path(temporary)
            archive, staged, backup = temporary / name, temporary / "stakpak", temporary / "previous"
            self.run(["curl", "-fLsS", "--connect-timeout", "10", "--max-time", "180", "-o", str(archive), url], 200)
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            if asset.get("digest") and asset["digest"] != "sha256:" + digest:
                raise RuntimeError("Stakpak release checksum mismatch; existing binary retained")
            self.log.write(f"Official Stakpak archive SHA-256: {digest}\n")
            with tarfile.open(archive, "r:gz") as source:
                members = [m for m in source.getmembers() if m.isfile() and Path(m.name).name == "stakpak"]
                if len(members) != 1:
                    raise RuntimeError("Stakpak archive does not contain exactly one regular binary")
                # Copy only this regular member; never extract archive paths or links.
                with source.extractfile(members[0]) as incoming, staged.open("xb") as outgoing:
                    shutil.copyfileobj(incoming, outgoing)
            staged.chmod(destination.stat().st_mode & 0o777)
            observed = self.run([str(staged), "--version"], 30)
            match = VERSION.search(observed)
            if not match or match.group(0) != tag[1:]:
                raise RuntimeError("downloaded Stakpak binary failed version verification")
            self.guard(target)  # Recheck active autopilot/sessions immediately before replacement.
            if Path(target.executable).resolve() != destination or hashlib.sha256(destination.read_bytes()).hexdigest() != original_hash:
                raise Deferred("Stakpak installation changed concurrently; existing binary retained")
            if staged.read_bytes() == destination.read_bytes():
                return
            shutil.copy2(destination, backup)
            staged.replace(destination)  # Same-filesystem atomic replacement, as in its native updater.
            try:
                if self.version(target) != tag[1:]:
                    raise RuntimeError("active Stakpak binary failed version verification")
            except BaseException:
                backup.replace(destination)
                raise

    def update(self, target):
        if target.kind == "preserved":
            return {"status": "preserved", "detail": "pinned integration/repaired build; not overwritten"}
        if target.kind == "on-launch":
            if target.name == "junie":
                with Path(target.executable).open("rb") as handle:
                    if b"JUNIE_MANAGED_SHIM" not in handle.read(4096):
                        raise Deferred("Junie's managed updater shim is absent; startup updates are not verified")
            return {"status": "on-launch", "detail": "vendor startup updater; not claimed updated by this job"}
        if target.kind == "unresolved":
            raise RuntimeError("installation manager is unrecognized; no replacement was attempted")
        self.guard(target)
        detail = None
        try:
            before = self.version(target)
        except (RuntimeError, OSError):
            if target.kind not in {"npm", "uv", "brew"}:
                raise
            # A broken client must not prevent its independent package manager
            # from repairing/upgrading it once a fixed release is available.
            self.log.write("Pre-update health probe failed; proceeding through the existing package manager.\n")
            before = "unavailable"
        if target.kind == "npm":
            current = json.loads((Path(target.package_dir) / "package.json").read_text())["version"]
            latest = self.run([target.command[0], "view", target.package, "dist-tags.latest", "--json",
                               "--fetch-retries=1", "--fetch-timeout=30000"], 60)
            latest = json.loads(latest)
            if not isinstance(latest, str) or not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][\w.-]+)?", latest):
                raise RuntimeError("registry returned an invalid stable version")
            if "-" in current:
                raise Deferred("prerelease installation retained; do not change its channel")
            current_parts = tuple(map(int, current.split("+")[0].split(".")))
            latest_parts = tuple(map(int, latest.split("-")[0].split("+")[0].split(".")))
            if current_parts > latest_parts:
                raise Deferred("installed version is newer than registry latest; no downgrade")
            if current != latest or before == "unavailable":
                self.run([target.command[0], "install", "--global", "--prefix", target.prefix,
                          "--no-audit", "--no-fund", f"{target.package}@{latest}"])
            observed = json.loads((Path(target.package_dir) / "package.json").read_text())["version"]
            if observed != latest:
                raise RuntimeError("installed package metadata does not match the requested release")
        else:
            if target.kind == "brew" and not self.brew_refreshed:
                self.run([target.command[0], "update"])
                self.brew_refreshed = True
            if target.kind == "uv":
                environment, bin_dir = Path(target.prefix), Path(target.executable).parent
                if not target.prefix or bin_dir.resolve() == (environment / "bin").resolve():
                    raise Deferred("uv executable export directory could not be verified")
                self.run(["/usr/bin/env", f"UV_TOOL_DIR={environment.parent}",
                          f"UV_TOOL_BIN_DIR={bin_dir}", *target.command])
            elif target.name == "vtcode":
                command = list(target.command)
                update_help = self.run([target.executable, "update", "--help"], 30)
                if "--without-desktop" in update_help:
                    # Newer versions otherwise offer to install an additional app,
                    # including when the command-line binary is already current.
                    command.append("--without-desktop")
                self.run(command, confirmation=r"Install VT Code v[0-9A-Za-z.+-]+ now\? This will replace the current binary\.")
            elif target.name == "stakpak":
                try:
                    self.run(target.command)
                except RuntimeError:
                    # The vendor's release-cache endpoint can fail even though the
                    # official GitHub release is available. Never call a stale binary current.
                    release = json.loads(self.run(["curl", "-fLsS", "--connect-timeout", "10", "--max-time", "40",
                                                   "https://api.github.com/repos/stakpak/agent/releases/latest"], 45))
                    current, latest = self.version(target), release.get("tag_name", "").removeprefix("v")
                    if not re.fullmatch(r"\d+\.\d+\.\d+", current) or not re.fullmatch(r"\d+\.\d+\.\d+", latest):
                        raise Deferred("Stakpak version/channel is unrecognized; existing installation retained")
                    if tuple(map(int, latest.split("."))) > tuple(map(int, current.split("."))):
                        self.install_stakpak_release(target, release)
                        detail = "updated from the official GitHub binary after the vendor release-cache endpoint failed"
                    elif latest == current:
                        detail = "official GitHub release matches; vendor release-cache endpoint unavailable"
                    else:
                        raise Deferred("Stakpak is newer than the official stable release; no downgrade")
                    self.log.write(detail + "\n")
            else:
                self.run(target.command)
        after = self.version(target)
        if target.kind == "npm" and after != latest:
            raise RuntimeError("active executable version does not match the installed npm release")
        result = {"status": "updated" if before != after else "checked", "before": before, "after": after}
        if detail:
            result["detail"] = detail
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="inventory installed targets without updating")
    parser.add_argument("--only", action="append", default=[], help="update one installed target; repeatable")
    parser.add_argument("--force", action="store_true", help="ignore freshness, not pins or running-session guards")
    parser.add_argument("--max-age-minutes", type=float, default=1440)
    parser.add_argument("--max-runtime-seconds", type=float, default=900)
    args = parser.parse_args(argv)
    if args.max_age_minutes < 0 or args.max_runtime_seconds <= 0:
        parser.error("freshness must be non-negative and runtime must be positive")
    if sys.platform != "darwin":
        parser.error("this is the Mac updater; use auto-update-tools.sh on Linux")
    if os.environ.get("AGENT_CLI_UPDATE_SKIP") == "1" and not args.list:
        return 0
    home = Path.home()
    targets = discover(home)
    if unknown := set(args.only) - {target.name for target in targets}:
        parser.error("unknown/uninstalled targets: " + ", ".join(sorted(unknown)))
    targets = [target for target in targets if not args.only or target.name in args.only]
    if args.list:
        for target in targets:
            print(f"{target.name:24} {target.kind:14} {shlex.join(target.command) or target.executable}")
        return 0
    os.umask(0o077)
    state = Path(os.environ.get("XDG_STATE_HOME", home / ".local/state")) / "agent-cli-updates"
    state.mkdir(parents=True, exist_ok=True)
    state.chmod(0o700)
    with update_lock(lock_path(home)) as acquired:
        if not acquired:
            print("Another updater owns the lock; no duplicate update started.")
            return 0
        status_file = state / "status.json"
        # A malformed existing receipt is an error, not permission to forget its state.
        records = json.loads(status_file.read_text()) if status_file.exists() else {}
        selected = [target for target in targets if due(records.get(target.name), time.time(),
                                                       args.max_age_minutes * 60, args.force)]
        if not selected:
            print("Agent update checks are fresh; nothing to do.")
            return 0
        run_id = datetime.now().strftime("%m-%d-%Y_%H%M%S") + f"_{os.getpid()}"
        run_dir = state / "runs" / run_id
        run_dir.mkdir(parents=True)
        deadline = time.monotonic() + args.max_runtime_seconds
        failed = False
        with (state / "update.log").open("a") as summary:
            updater = Updater(home, state, summary, deadline)
            for target in selected:
                record = {"attempted_at": time.time(), "kind": target.kind,
                          "log": str(run_dir / (target.name + ".log"))}
                with Path(record["log"]).open("w") as log:
                    updater.log = log
                    try:
                        record.update(updater.update(target))
                    except Deferred as exc:
                        record.update(status="deferred", detail=str(exc))
                    except Exception as exc:
                        record.update(status="failed", detail=str(exc))
                        failed = True
                records[target.name] = record
                atomic_json(status_file, records)
                message = f"{target.name}: {record['status']}"
                if "before" in record:
                    message += f" ({record['before']} -> {record['after']})"
                if "detail" in record:
                    message += "; " + record["detail"]
                print(message, flush=True)
                summary.write(f"[{datetime.now():%m-%d-%Y %H:%M:%S}] {message}\n")
                summary.flush()
        atomic_json(run_dir / "receipt.json", {name: records[name] for name in [t.name for t in selected]})
        return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
