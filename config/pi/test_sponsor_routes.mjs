// TLDR: Offline tests for sponsor deduplication, payer preservation, and session migration.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const source = readFileSync(new URL('./extensions/sponsor-routes.ts', import.meta.url), 'utf8');
const { applySponsorRoutes } = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));

async function run(options = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'pi-sponsor-test-'));
  try {
    writeFileSync(join(dir, 'fake.txt'), 'fake-key\n');
    const generic = { provider: 'openai', id: 'sol', type: 'chat' };
    const named = { ...generic, provider: 'koyejolab-openai-bm' };
    const other = { ...generic, id: 'unaliased' };
    const image = { ...generic, id: 'image', type: 'image' };
    const classifier = { ...generic, id: 'classifier', type: 'classifier' };
    const changes = [];
    const registry = {
      getAll: () => [generic, other, named],
      getAvailable: () => options.missing ? [generic] : [generic, named],
      isUsingOAuth: () => options.oauth || false,
      getApiKeyForProvider: async () => options.different ? 'other-key' : 'fake-key',
      find: () => named,
      getModelsOfType: (type) => type === 'image' ? [image] : [classifier],
    };
    const pi = {
      setModel: async (model) => { changes.push(['switch', model]); return !options.failed; },
      registerProvider: (id, config) => changes.push(['register', id, config]),
    };
    await applySponsorRoutes(pi, { modelRegistry: registry, model: generic },
      { providers: [{ provider: 'openai', id: named.provider, keyFile: 'fake.txt' }] }, dir);
    return changes;
  } finally { rmSync(dir, { recursive: true }); }
}

test('migrates same model and credential before hiding duplicate; preserves other model types', async () => {
  const changes = await run();
  assert.equal(changes[0][1], 'koyejolab-openai-bm');
  assert.deepEqual(changes[0][2].models.map(m => m.id), ['sol', 'unaliased']);
  assert.equal(changes[1][0], 'switch');
  assert.equal(changes[1][1].provider, 'koyejolab-openai-bm');
  assert.equal(changes[1][1].id, 'sol');
  assert.equal(changes[2][1], 'openai');
  assert.deepEqual(changes[2][2].models.map(m => m.id), ['image', 'classifier']);
});
for (const option of ['different', 'missing', 'oauth']) {
  test(`preserves generic route when ${option}`, async () => assert.deepEqual(await run({ [option]: true }), []));
}
test('failed migration does not remove the active route', async () => {
  const changes = await run({ failed: true });
  assert.deepEqual(changes.map(c => c[0]), ['register', 'switch']);
  assert.equal(changes[0][1], 'koyejolab-openai-bm');
});
