import { readFileSync, mkdirSync, writeFileSync, renameSync } from 'node:fs';
import { join } from 'node:path';
import { readSubscription } from './auth.mjs';

export function readCatalog(profile, agentDir, account, accountId) {
  try {
    const saved = JSON.parse(readFileSync(join(agentDir, 'codex-account-models', `${account}.json`), 'utf8'));
    if (saved.accountId === accountId && Array.isArray(saved.models)) {
      return new Set(saved.models.map(m => m.slug));
    }
  } catch { /* First installation can use the CLI-owned catalog. */ }
  const saved = JSON.parse(readFileSync(join(profile, 'models_cache.json'), 'utf8'));
  return new Set(saved.models.map(m => m.slug));
}

export async function refreshCatalog(profile, agentDir, account, version, request = fetch) {
  if (!/^[a-z][a-z0-9-]*$/.test(account) || !/^\d+\.\d+\.\d+$/.test(version)) {
    throw new Error('Invalid account or Codex client version');
  }
  const { token, accountId } = readSubscription(join(profile, 'auth.json'));
  const response = await request(`https://chatgpt.com/backend-api/codex/models?client_version=${version}`, {
    headers: { Authorization: `Bearer ${token}`, 'ChatGPT-Account-Id': accountId,
      'User-Agent': `codex_cli_rs/${version}`, originator: 'codex_cli_rs' },
    signal: AbortSignal.timeout(30000),
  });
  if (!response.ok) throw new Error(`Codex model discovery HTTP ${response.status}`);
  const data = await response.json();
  if (!Array.isArray(data.models) || !data.models.length || data.models.some(m => typeof m.slug !== 'string')) {
    throw new Error('Invalid Codex model catalog');
  }
  const directory = join(agentDir, 'codex-account-models');
  mkdirSync(directory, { recursive: true, mode: 0o700 });
  const path = join(directory, `${account}.json`);
  const temporary = `${path}.${process.pid}.tmp`;
  writeFileSync(temporary, JSON.stringify({ accountId, clientVersion: version,
    fetchedAt: new Date().toISOString(), models: data.models.map(({ slug }) => ({ slug })) })+'\n', { mode: 0o600 });
  renameSync(temporary, path);
  return data.models.map(m => m.slug);
}
