# Pipedream Connect demo

What it is: a "Connect your account" button. You click it, sign in to Toggl (or Google Sheets) once on Pipedream's page, and Pipedream keeps the login. Code can then use that account through Pipedream without a password or API token.

Follows https://pipedream.com/docs/connect/quickstart for project `proj_YRs7KDz`, production. Standalone: it touches no live site.

## Run

1. Pipedream > project proj_YRs7KDz > Settings > API: create or reuse an OAuth client. Copy its client ID and secret.
2. `cp .env.example .env` and paste the two values. `.env` is git-ignored; never commit it or paste it anywhere.
3. `npm install && npm start`, open http://localhost:3000.
4. Press **Connect Toggl**, sign in in the new tab, then **List connected accounts**: Toggl should appear with `healthy: true`.

`npm test` checks the server without keys (clear error, page serves).

## How it works

- `POST /api/connect-token?app=toggl_track` (server.mjs) calls `tokens.create` with the project's client credentials and returns Pipedream's hosted Connect Link. The secret stays on the server.
- `GET /api/accounts` lists accounts connected for `EXTERNAL_USER_ID` (default `brando`).
- `public/index.html` is the Connect page; it only ever sees the short-lived link.

## Reconnect

If an account shows `healthy: false` or was revoked, press its Connect button again with the same `EXTERNAL_USER_ID`. Other app slugs: add a button with `data-app="<slug>"` (slugs are in Pipedream's app list).
