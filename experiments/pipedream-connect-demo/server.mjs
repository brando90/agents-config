import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { PipedreamClient } from "@pipedream/sdk";

const REQUIRED = ["PIPEDREAM_CLIENT_ID", "PIPEDREAM_CLIENT_SECRET", "PIPEDREAM_PROJECT_ID"];
const port = Number(process.env.PORT || 3000);
const projectEnvironment = process.env.PIPEDREAM_PROJECT_ENVIRONMENT || "production";
const externalUserId = process.env.EXTERNAL_USER_ID || "brando";

export function missingConfig(env = process.env) {
  return REQUIRED.filter((k) => !env[k]);
}

let client;
function pd() {
  client ??= new PipedreamClient({
    clientId: process.env.PIPEDREAM_CLIENT_ID,
    clientSecret: process.env.PIPEDREAM_CLIENT_SECRET,
    projectId: process.env.PIPEDREAM_PROJECT_ID,
    projectEnvironment,
  });
  return client;
}

const json = (res, status, body) => {
  res.writeHead(status, { "content-type": "application/json" });
  res.end(JSON.stringify(body));
};

export const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  try {
    if (url.pathname === "/") {
      res.writeHead(200, { "content-type": "text/html" });
      return res.end(await readFile(new URL("./public/index.html", import.meta.url)));
    }
    if (url.pathname === "/api/connect-token" && req.method === "POST") {
      const missing = missingConfig();
      if (missing.length) return json(res, 500, { error: `Missing ${missing.join(", ")}; see .env.example` });
      const app = url.searchParams.get("app") || undefined;
      const t = await pd().tokens.create({ externalUserId, ...(app ? { appId: app } : {}) });
      // The hosted Connect Link takes the app slug as a query parameter.
      const link = new URL(t.connectLinkUrl);
      if (app) link.searchParams.set("app", app);
      return json(res, 200, { connectLinkUrl: link.toString(), expiresAt: t.expiresAt });
    }
    if (url.pathname === "/api/accounts") {
      const missing = missingConfig();
      if (missing.length) return json(res, 500, { error: `Missing ${missing.join(", ")}; see .env.example` });
      const page = await pd().accounts.list({ externalUserId });
      const accounts = [];
      for await (const a of page) accounts.push({ id: a.id, name: a.name, app: a.app?.nameSlug, healthy: a.healthy });
      return json(res, 200, { externalUserId, accounts });
    }
    json(res, 404, { error: "not found" });
  } catch (e) {
    json(res, 500, { error: String(e?.message || e) });
  }
});

if (import.meta.url === `file://${process.argv[1]}`) {
  const missing = missingConfig();
  if (missing.length) console.warn(`Warning: missing ${missing.join(", ")}; copy .env.example to .env`);
  server.listen(port, () => console.log(`Pipedream Connect demo on http://localhost:${port}`));
}
