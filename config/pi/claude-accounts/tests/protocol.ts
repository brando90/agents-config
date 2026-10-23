// Run: pi --offline --no-extensions -e ./tests/protocol.ts --no-mcp --list-models
import assert from 'node:assert/strict';
import { validateClaudeInitialization } from 'pi-claude-code-provider/src/claude-protocol.ts';
export default function () {
  const base = { type: 'system', subtype: 'init', tools: [], permissionMode: 'dontAsk', slash_commands: [], skills: [], plugins: [{ name: 'cc-plugin-sec-default' }], apiKeySource: 'none', mcp_servers: [], model: 'fixture-model' };
  const expected = { tools: new Set(), mcpServer: 'none' as const };
  assert.equal(validateClaudeInitialization(base, expected), 'fixture-model');
  assert.throws(() => validateClaudeInitialization({ ...base, plugins: [{name: 'unknown-plugin'}] }, expected));
  assert.throws(() => validateClaudeInitialization({ ...base, tools: ['Bash'] }, expected));
  assert.throws(() => validateClaudeInitialization({ ...base, apiKeySource: 'user' }, expected));
  assert.throws(() => validateClaudeInitialization({ ...base, skills: ['unexpected-skill'] }, expected));
  console.error('PASS: security plugin retained; unexpected tools, credentials, skills and plugins rejected');
}
