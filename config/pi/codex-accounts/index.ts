import type { ExtensionAPI } from '@earendil-works/pi-coding-agent';
import { getModels, openAICodexResponsesApi } from '@earendil-works/pi-ai/compat';
const { streamSimple } = openAICodexResponsesApi();
import { homedir } from 'node:os';
import { join } from 'node:path';
import { readSubscription } from './auth.mjs';
import { readCatalog } from './catalog.mjs';

export default function (pi: ExtensionAPI) {
  const accounts = [
    { id: 'personal-codex', label: 'Personal Codex subscription', dir: '.codex' },
    { id: 'vals-codex', label: 'Vals Codex subscription', dir: '.codex-vals' },
  ];
  for (const account of accounts) {
    const path = join(homedir(), account.dir, 'auth.json');
    let slugs: Set<string>;
    try {
      const { accountId } = readSubscription(path);
      slugs = readCatalog(join(homedir(), account.dir),
        process.env.PI_CODING_AGENT_DIR || join(homedir(), '.pi/agent'), account.id, accountId);
    } catch {
      // Missing or expired login must not prevent the other account loading.
      continue;
    }
    const api = `${account.id}-subscription`;
    const models = getModels('openai').filter(m => slugs.has(m.id)).map(m => ({
      ...m, api, baseUrl: 'https://chatgpt.com/backend-api',
      name: `${m.name} · ${account.label}`,
    }));
    pi.registerProvider(account.id, {
      name: account.label,
      api, baseUrl: 'https://chatgpt.com/backend-api',
      // Availability marker only; always replaced by the profile's subscription token.
      apiKey: 'codex-subscription-profile', models,
      streamSimple: (model, context, options) => {
        const { token } = readSubscription(path);
        return streamSimple({ ...model, api: 'openai-codex-responses' }, context, { ...options, apiKey: token });
      },
    });
  }
  pi.registerCommand('codex-accounts', {
    description: 'Check personal and Vals Codex subscription profiles (no inference)',
    handler: async (_args, ctx) => {
      for (const a of accounts) {
        try {
          readSubscription(join(homedir(), a.dir, 'auth.json'));
          ctx.ui.notify(`${a.id}: subscription token locally valid; /model → ${a.id}`, 'info');
        } catch (e) { ctx.ui.notify(`${a.id}: ${(e as Error).message}`, 'error'); }
      }
    },
  });
}
