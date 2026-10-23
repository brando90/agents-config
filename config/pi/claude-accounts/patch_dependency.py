"""Narrow, hash-checked compatibility patch for Claude Code 2.1.309.

The native sec-default security plugin remains loaded and active. Only the
adapter's metadata rejection is relaxed for this exact built-in name. Tool,
MCP, permission, credential-source, skill and other-plugin checks stay intact.
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BEFORE_SHA256 = 'ea10cd1eebd47499c4145f9a11806b7cfd5307d52d2284004ee2708c4201d3aa'
OLD = '  if (record.slash_commands.length > 0 || record.skills.length > 0 || record.plugins.length > 0) {'
NEW = '''  // Brando compatibility: retain Claude's built-in security plugin; it is
  // not an unexpected user customization. Do not disable its security behavior.
  const unexpectedPlugins = record.plugins.filter((plugin) => {
    const name = typeof plugin === "string" ? plugin : (plugin as { name?: unknown } | null)?.name;
    return name !== "cc-plugin-sec-default";
  });
  if (record.slash_commands.length > 0 || record.skills.length > 0 || unexpectedPlugins.length > 0) {'''


def apply():
    path = ROOT/'node_modules/pi-claude-code-provider/src/claude-protocol.ts'
    text = path.read_text()
    if NEW in text:
        original = text.replace(NEW, OLD)
        if hashlib.sha256(original.encode()).hexdigest() != BEFORE_SHA256:
            raise ValueError('Unexpected patched dependency drift')
        return
    if hashlib.sha256(text.encode()).hexdigest() != BEFORE_SHA256 or text.count(OLD) != 1:
        raise ValueError('Pinned dependency changed: review patch before installing')
    path.write_text(text.replace(OLD, NEW))


if __name__ == '__main__':
    apply()
