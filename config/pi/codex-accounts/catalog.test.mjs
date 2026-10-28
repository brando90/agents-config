import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, readFileSync, rmSync, statSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { readCatalog, refreshCatalog } from './catalog.mjs';

test('account catalog survives stale CLI writes and rejects another account', async () => {
  const directory = mkdtempSync(join(tmpdir(), 'pi-codex-catalog-'));
  try {
    const token = `test.${Buffer.from(JSON.stringify({exp:4102444800,
      'https://api.openai.com/auth':{chatgpt_account_id:'vals'}})).toString('base64url')}.test`;
    writeFileSync(join(directory,'auth.json'), JSON.stringify({auth_mode:'chatgpt',tokens:{access_token:token,account_id:'vals'}}));
    writeFileSync(join(directory,'models_cache.json'),JSON.stringify({models:[{slug:'old-model'}]}));
    const request = async (url, options) => {
      assert.match(url,/client_version=0\.165\.0$/);
      assert.equal(options.headers['ChatGPT-Account-Id'],'vals');
      assert.equal(options.headers.Authorization,`Bearer ${token}`);
      return {ok:true,json:async()=>({models:[{slug:'gpt-6.1-sol'}]})};
    };
    await refreshCatalog(directory,directory,'vals-codex','0.165.0',request);
    assert.deepEqual([...readCatalog(directory,directory,'vals-codex','vals')],['gpt-6.1-sol']);
    assert.deepEqual([...readCatalog(directory,directory,'vals-codex','other')],['old-model']);
    const target = join(directory,'codex-account-models/vals-codex.json');
    const saved = readFileSync(target,'utf8');
    assert.equal(saved.includes(token),false);
    assert.equal(statSync(target).mode & 0o777,0o600);
    await assert.rejects(refreshCatalog(directory,directory,'vals-codex','0.165.0',async()=>({ok:false,status:401})),/HTTP 401/);
    assert.equal(readFileSync(target,'utf8'),saved);
    await assert.rejects(refreshCatalog(directory,directory,'../escape','0.165.0',request),/Invalid account/);
  } finally { rmSync(directory,{recursive:true}); }
});
