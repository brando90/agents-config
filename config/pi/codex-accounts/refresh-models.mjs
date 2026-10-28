import { homedir } from 'node:os';
import { join } from 'node:path';
import { refreshCatalog } from './catalog.mjs';

const [account, version] = process.argv.slice(2);
const profiles = { 'personal-codex': '.codex', 'vals-codex': '.codex-vals' };
if (!profiles[account] || !version) {
  console.error('Usage: node refresh-models.mjs personal-codex|vals-codex <current-codex-client-version>');
  process.exit(2);
}
try {
  const models = await refreshCatalog(join(homedir(), profiles[account]),
    process.env.PI_CODING_AGENT_DIR || join(homedir(), '.pi/agent'), account, version);
  console.log(`${account}: ${models.length} account-verified models cached; no inference`);
  console.log(models.join('\n'));
} catch (error) {
  // Never print a response body or credential-bearing request object.
  console.error(error instanceof Error && /^Codex model discovery HTTP \d+$/.test(error.message)
    ? error.message : 'Codex model discovery failed; existing catalog retained');
  process.exit(1);
}
