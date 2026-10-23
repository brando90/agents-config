#!/usr/bin/env python3
"""Account-specific Claude CLI launcher. Credentials remain owned by Claude Code."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def account_env(account, source=None, home=None):
    env = dict(os.environ if source is None else source)
    # Do not let a Pi API key, another Claude profile, or a gateway change payer.
    for key in list(env):
        if key.startswith("ANTHROPIC_") or key.startswith("CLAUDE_CODE_USE_") or key in {
            "CLAUDE_CONFIG_DIR", "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDECODE",
            "CLAUDE_CODE_API_KEY_HELPER_TTL_MS",
        }:
            env.pop(key, None)
    if account["configDir"] is not None:
        env["CLAUDE_CONFIG_DIR"] = str(Path(home or Path.home()) / account["configDir"])
    return env


def validate_identity(account, status):
    if not (status.get("loggedIn") and status.get("authMethod") == "claude.ai"
            and status.get("apiProvider") == "firstParty"
            and status.get("subscriptionType") in {"pro", "max", "team", "enterprise"}
            and status.get("email") == account["email"]
            and status.get("orgId") == account["orgId"]):
        raise ValueError(f"{account['id']}: expected subscription identity is not signed in; no fallback was attempted")


def transport_args(args):
    args = list(args)
    if '--settings' in args:
        i = args.index('--settings') + 1
        settings = json.loads(args[i])
        # Claude 2.1.309 adds this built-in plugin even with empty setting sources.
        # Keep the upstream proposal-only transport's no-hidden-customization contract.
        settings.setdefault('enabledPlugins', {})['plugin-authoring@builtin'] = False
        args[i] = json.dumps(settings)
    return args


def main():
    account_id, executable, *args = sys.argv[1:]
    account = next(a for a in json.loads((ROOT / "accounts.json").read_text()) if a["id"] == account_id)
    env = account_env(account)
    # Version/help never generate. All other calls verify the intended payer first.
    if args not in (["--version"], ["--help"]):
        result = subprocess.run([executable, "auth", "status"], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=20)
        try:
            status = json.loads(result.stdout)
            validate_identity(account, status)
        except (ValueError, TypeError):
            print(f"{account_id}: subscription login/identity check failed. Use the matching Claude profile to sign in, then /reload. No account fallback.", file=sys.stderr)
            return 1
        if args == ["auth", "status"]:
            print(json.dumps(status))
            return 0
    os.execve(executable, [executable, *transport_args(args)], env)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"Claude account launcher: {type(exc).__name__}", file=sys.stderr)
        sys.exit(1)
