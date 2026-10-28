import test from "node:test";
import assert from "node:assert/strict";
import { server, missingConfig } from "./server.mjs";

test("missingConfig lists absent keys", () => {
  assert.deepEqual(missingConfig({ PIPEDREAM_PROJECT_ID: "p" }), ["PIPEDREAM_CLIENT_ID", "PIPEDREAM_CLIENT_SECRET"]);
});

test("token endpoint without keys answers a clear 500, page serves", async () => {
  for (const k of ["PIPEDREAM_CLIENT_ID", "PIPEDREAM_CLIENT_SECRET", "PIPEDREAM_PROJECT_ID"]) delete process.env[k];
  await new Promise((r) => server.listen(0, r));
  const base = `http://localhost:${server.address().port}`;
  const t = await fetch(`${base}/api/connect-token?app=toggl_track`, { method: "POST" });
  assert.equal(t.status, 500);
  assert.match((await t.json()).error, /Missing PIPEDREAM_CLIENT_ID/);
  assert.match(await (await fetch(base)).text(), /Connect Toggl/);
  server.close();
});
