import { readFileSync } from 'node:fs';

// Read on every request; Codex remains the sole owner of login/refresh writes.
export function readSubscription(path, now = Date.now()) {
  let auth;
  try { auth = JSON.parse(readFileSync(path, 'utf8')); }
  catch { throw new Error(`Cannot read Codex subscription login: ${path}`); }
  if (auth.auth_mode !== 'chatgpt' || !auth.tokens?.access_token) {
    throw new Error(`ChatGPT subscription login required in ${path}; no API-key fallback`);
  }
  const token = auth.tokens.access_token;
  let claims;
  try { claims = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString()); }
  catch { throw new Error('Invalid Codex subscription token; sign in again with Codex'); }
  const accountId = claims['https://api.openai.com/auth']?.chatgpt_account_id;
  if (!accountId || !claims.exp || claims.exp * 1000 <= now) {
    throw new Error(`Codex subscription token missing identity or expired: ${path}. Refresh this profile with Codex, then retry; no account fallback.`);
  }
  if (auth.tokens.account_id && auth.tokens.account_id !== accountId) {
    throw new Error('Codex subscription account identity mismatch');
  }
  return { token, accountId };
}
