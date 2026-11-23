#!/usr/bin/env python3
"""Deterministic and live verification for Eight Sleep MCP plugin configs."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import pathlib
import re
import secrets
import shutil
import subprocess
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

MCP_URL = "https://public-api.8slp.net/mcp"
AUTH_BASE = "https://auth-api.8slp.net"
ANTIGRAVITY_CIMD = "https://antigravity.google/oauth/client-metadata.json"
ANTIGRAVITY_CALLBACK = "https://antigravity.google/oauth-callback"

READ_TOOLS = (
    "get_sleep_days",
    "get_sleep_sessions",
    "get_sleep_session",
    "get_device_status",
    "get_temperature_settings",
    "list_alarms",
)
WRITE_TOOLS = (
    "create_alarm",
    "update_alarm",
    "delete_alarm",
    "set_pod_power",
    "set_temperature",
    "update_temperature_schedule",
)
ALL_TOOLS = READ_TOOLS + WRITE_TOOLS

ALLOWED_AGY_MANIFEST_KEYS = {
    "name",
    "displayName",
    "version",
    "description",
    "logo",
    "suggestedPrompts",
    "author",
    "homepage",
    "repository",
    "disabled",
}

SECRET_PATTERNS = (
    re.compile(r"GOCSPX-[A-Za-z0-9_-]{10,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(
        r"(client_?secret|access_?token|refresh_?token|api_?key|bearer)\s*[:=]\s*[\"']?[A-Za-z0-9_\-/+.]{16,}",
        re.IGNORECASE,
    ),
)


def _read_json(path: pathlib.Path) -> Any:
    """Parse a JSON file and return the decoded object."""
    return json.loads(path.read_text(encoding="utf-8"))


def _http_request(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], str]:
    """Send an HTTP request and return (status, lower-case headers, text)."""
    req_headers = dict(headers or {})
    data: bytes | None = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status, raw_hdrs, raw_body = resp.status, resp.headers, resp.read()
    except urllib.error.HTTPError as err:
        status, raw_hdrs, raw_body = err.code, err.headers, err.read()
    hdrs = {k.lower(): v for k, v in raw_hdrs.items()} if raw_hdrs else {}
    return status, hdrs, raw_body.decode("utf-8", errors="replace")


def _get_json(url: str, label: str) -> dict[str, Any]:
    """Fetch a JSON object from url, failing on non-200 status before decoding."""
    status, _, body = _http_request(url)
    if status != 200:
        raise AssertionError(f"Unexpected {label} response: http={status} body={body[:200]}")
    data = json.loads(body)
    if not isinstance(data, dict):
        raise AssertionError(f"Expected JSON object from {label}, got {type(data).__name__}")
    return data


def check_json_configs(root: pathlib.Path) -> None:
    """Validate all plugin JSON manifests and MCP endpoint URLs."""
    json_files = (
        root / "antigravity" / "plugin.json",
        root / "antigravity" / "mcp_config.json",
        root / "claude-code" / ".mcp.json",
        root / "claude-code" / ".claude-plugin" / "plugin.json",
        root / ".claude-plugin" / "marketplace.json",
        root / "cursor" / "mcp.json",
    )
    decoded = {rel: _read_json(rel) for rel in json_files}

    mcp_checks = (
        (decoded[root / "antigravity" / "mcp_config.json"], "serverUrl"),
        (decoded[root / "claude-code" / ".mcp.json"], "url"),
        (decoded[root / "cursor" / "mcp.json"], "url"),
    )
    for cfg, key in mcp_checks:
        entry = cfg.get("mcpServers", {}).get("eight-sleep", {})
        if entry.get(key) != MCP_URL:
            raise AssertionError(f"Expected eight-sleep.{key} == {MCP_URL}, got {entry!r}")


def check_antigravity_bundle(root: pathlib.Path) -> None:
    """Validate Antigravity plugin schema, rules file, and prompt count."""
    manifest = _read_json(root / "antigravity" / "plugin.json")
    extra = set(manifest) - ALLOWED_AGY_MANIFEST_KEYS
    if extra:
        raise AssertionError(f"Unsupported Antigravity plugin.json keys: {sorted(extra)}")
    prompts = manifest.get("suggestedPrompts", [])
    if not isinstance(prompts, list) or not (1 <= len(prompts) <= 3):
        raise AssertionError(f"suggestedPrompts must contain 1..3 strings, got {prompts!r}")
    if any(not isinstance(p, str) or not p.strip() for p in prompts):
        raise AssertionError("suggestedPrompts must contain non-empty strings")

    rules_path = root / "antigravity" / "rules" / "AGENTS.md"
    rules_text = rules_path.read_text(encoding="utf-8")
    if not rules_text.strip():
        raise AssertionError(f"Empty rules file: {rules_path}")
    if rules_text.lstrip().startswith("---"):
        raise AssertionError(f"Antigravity plugin rules must omit YAML frontmatter: {rules_path}")


def _check_secret_hygiene(root: pathlib.Path) -> None:
    """Fail if any non-bytecode file under root matches a secret literal pattern."""
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix == ".pyc":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(pat.search(text) for pat in SECRET_PATTERNS):
            raise AssertionError(f"Potential secret literal matched in {path}")


def check_codex_and_docs(root: pathlib.Path) -> None:
    """Validate Codex TOML config, README tool list, and secret hygiene."""
    toml_data = tomllib.loads((root / "codex" / "config.toml.snippet").read_text(encoding="utf-8"))
    codex_entry = toml_data.get("mcp_servers", {}).get("eight-sleep", {})
    if codex_entry.get("url") != MCP_URL:
        raise AssertionError(f"Unexpected Codex URL: {codex_entry!r}")
    if codex_entry.get("scopes") != ["read_sleep", "read_device"]:
        raise AssertionError(f"Expected read-only Codex scopes, got {codex_entry.get('scopes')!r}")

    readme_text = (root / "README.md").read_text(encoding="utf-8")
    if "The last 7 change things" in readme_text:
        raise AssertionError("Stale 'The last 7 change things' typo still present in README.md")
    missing_tools = [tool for tool in ALL_TOOLS if tool not in readme_text]
    if missing_tools:
        raise AssertionError(f"README.md missing official tools: {missing_tools}")

    _check_secret_hygiene(root)


def _run_validator(cmd: list[str], label: str) -> str:
    """Execute a CLI validator command and return stdout on exit 0."""
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise AssertionError(f"{label} failed: {proc.stdout}\n{proc.stderr}")
    return proc.stdout


def _check_agy_validator(root: pathlib.Path) -> None:
    """Run strict Antigravity plugin validation when agy is installed."""
    if not shutil.which("agy"):
        return
    stdout = _run_validator(
        ["agy", "plugin", "validate", "--strict", "--json", str(root / "antigravity")],
        "agy plugin validate",
    )
    report = json.loads(stdout)
    bad = [f for f in report.get("findings", []) if f.get("severity") in ("error", "warning")]
    if bad:
        raise AssertionError(f"agy plugin validate reported findings: {bad}")
    comps = report.get("components", {})
    if comps.get("mcpServers") != 1 or comps.get("rules") != 1:
        raise AssertionError(f"Unexpected agy component counts: {comps}")


def check_cli_validators(root: pathlib.Path) -> None:
    """Run installed agy and claude plugin validators strictly when present."""
    _check_agy_validator(root)
    if not shutil.which("claude"):
        return
    for target in (root / "claude-code", root):
        _run_validator(
            ["claude", "plugin", "validate", "--strict", str(target)],
            f"claude plugin validate for {target}",
        )


def _check_mcp_resource_server() -> None:
    """Verify Eight Sleep health, PRM discovery, and unauthenticated /mcp challenge."""
    health = _get_json("https://public-api.8slp.net/v1", "/v1 health")
    if health.get("status") != "healthy":
        raise AssertionError(f"Unexpected /v1 health response: {health}")

    prm = _get_json("https://public-api.8slp.net/.well-known/oauth-protected-resource/mcp", "PRM")
    if prm.get("resource") != MCP_URL:
        raise AssertionError(f"PRM resource mismatch: {prm}")
    if prm.get("authorization_servers") != [AUTH_BASE]:
        raise AssertionError(f"Unexpected authorization_servers: {prm}")
    if not {"read_sleep", "read_device", "write_device"}.issubset(set(prm.get("scopes_supported", []))):
        raise AssertionError(f"Missing expected scopes in PRM: {prm}")

    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "eight-sleep-connector-test", "version": "0.1"},
        },
    }
    status, hdrs, _ = _http_request(
        MCP_URL,
        method="POST",
        payload=init_payload,
        headers={"Accept": "application/json, text/event-stream"},
    )
    www_auth = hdrs.get("www-authenticate", "")
    if status != 401 or "oauth-protected-resource/mcp" not in www_auth:
        raise AssertionError(f"Expected 401 + PRM challenge on POST /mcp, got {status} {www_auth!r}")


def _check_connectors_page() -> None:
    """Verify Eight Sleep /connectors page is live and documents all 12 tools."""
    status, _, connectors_html = _http_request("https://public-api.8slp.net/connectors")
    if status != 200:
        raise AssertionError(f"GET /connectors returned {status}")
    missing = [tool for tool in ALL_TOOLS if tool not in connectors_html]
    if missing:
        raise AssertionError(f"/connectors missing tools: {missing}")


def _check_oauth_metadata() -> None:
    """Verify Eight Sleep OAuth AS metadata and Antigravity CIMD metadata."""
    auth_meta = _get_json(f"{AUTH_BASE}/.well-known/oauth-authorization-server", "auth-server metadata")
    if not auth_meta.get("client_id_metadata_document_supported"):
        raise AssertionError(f"Unexpected auth-server metadata: {auth_meta}")
    if "S256" not in auth_meta.get("code_challenge_methods_supported", []):
        raise AssertionError(f"Missing S256 PKCE support: {auth_meta}")
    if not auth_meta.get("registration_endpoint"):
        raise AssertionError(f"Missing registration_endpoint: {auth_meta}")

    cimd = _get_json(ANTIGRAVITY_CIMD, "Antigravity CIMD metadata")
    if cimd.get("redirect_uris") != [ANTIGRAVITY_CALLBACK]:
        raise AssertionError(f"Unexpected Antigravity CIMD metadata: {cimd}")


def check_live_endpoints() -> list[str]:
    """Verify live Eight Sleep discovery/connector endpoints and report OAuth allowlist status."""
    _check_mcp_resource_server()
    _check_connectors_page()
    _check_oauth_metadata()
    return _probe_sanctioned_oauth_status()


def _probe_sanctioned_oauth_status() -> list[str]:
    """Check whether Eight Sleep currently accepts Antigravity CIMD or DCR loopback URIs."""
    verifier = secrets.token_urlsafe(32)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    query = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": ANTIGRAVITY_CIMD,
            "redirect_uri": ANTIGRAVITY_CALLBACK,
            "scope": "read_sleep read_device",
            "state": secrets.token_urlsafe(16),
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "resource": MCP_URL,
        }
    )
    status, _, html = _http_request(
        f"{AUTH_BASE}/v1/ui/authorize?{query}",
        headers={"Accept": "text/html", "User-Agent": "Mozilla/5.0"},
    )
    cimd_blocked = "eight - uh, oh" in html.lower() or "something seems off" in html.lower()
    cimd_state = "BLOCKED_UPSTREAM (Eight - Uh, oh)" if cimd_blocked else ("RENDERED_LOGIN" if status == 200 else f"HTTP_{status}")
    lines = [f"LIVE_OAUTH_STATUS cimd_authorize: http={status} status={cimd_state}"]
    for uri in (ANTIGRAVITY_CALLBACK, "http://127.0.0.1:8765/callback", "http://localhost:8765/callback"):
        reg_status, _, reg_body = _http_request(
            f"{AUTH_BASE}/v1/oauth/register",
            method="POST",
            payload={
                "client_name": "Antigravity Eight Sleep Verification",
                "redirect_uris": [uri],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
            },
            headers={"Accept": "application/json"},
        )
        lines.append(f"LIVE_OAUTH_STATUS dcr({uri}): http={reg_status} body={reg_body[:160]}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Eight Sleep MCP plugin bundle and endpoints.")
    parser.add_argument("--live", action="store_true", help="Also probe live Eight Sleep endpoints.")
    args = parser.parse_args()

    plugin_root = pathlib.Path(__file__).resolve().parent.parent
    check_json_configs(plugin_root)
    check_antigravity_bundle(plugin_root)
    check_codex_and_docs(plugin_root)
    check_cli_validators(plugin_root)
    print(f"OFFLINE_CHECKS_PASS: {plugin_root}")

    if args.live:
        for line in check_live_endpoints():
            print(line)
        print("LIVE_ENDPOINT_CHECKS_PASS: 6/6 core endpoints verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
