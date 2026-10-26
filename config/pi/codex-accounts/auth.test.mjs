import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { readSubscription } from './auth.mjs';

test('subscription-only, identity isolation, expiry, reread, malformed/missing login', () => {
  const dir = mkdtempSync(join(tmpdir(), 'pi-codex-auth-'));
  const path = join(dir, 'auth.json');
  const make = (id, exp = 200) => ({auth_mode:'chatgpt', tokens:{account_id:id, access_token:`test.${Buffer.from(JSON.stringify({exp,'https://api.openai.com/auth':{chatgpt_account_id:id}})).toString('base64url')}.test`}});
  try {
    assert.throws(() => readSubscription(path, 100000), /Cannot read/);
    writeFileSync(path, JSON.stringify({auth_mode:'apikey', OPENAI_API_KEY:'fake'}));
    assert.throws(() => readSubscription(path, 100000), /no API-key fallback/);
    writeFileSync(path, JSON.stringify(make('personal')));
    assert.equal(readSubscription(path,100000).accountId,'personal');
    writeFileSync(path, JSON.stringify(make('vals')));
    assert.equal(readSubscription(path,100000).accountId,'vals');
    assert.throws(() => readSubscription(path,300000), /expired/);
    const mismatch = make('personal'); mismatch.tokens.account_id = 'vals';
    writeFileSync(path, JSON.stringify(mismatch));
    assert.throws(() => readSubscription(path,100000), /mismatch/);
    writeFileSync(path, JSON.stringify({auth_mode:'chatgpt',tokens:{access_token:'bad'}}));
    assert.throws(() => readSubscription(path,100000), /Invalid/);
  } finally { rmSync(dir, {recursive:true}); }
});
