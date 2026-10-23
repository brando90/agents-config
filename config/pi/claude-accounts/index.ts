import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { getAgentDir } from "@earendil-works/pi-coding-agent";
import { getModels } from "@earendil-works/pi-ai";
import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { promisify } from "node:util";
import { createClaudeStream } from "pi-claude-code-provider/src/provider.ts";
import { parseAuthStatus, validateClaudeCapabilities } from "pi-claude-code-provider/src/auth.ts";
import { probeBridge } from "pi-claude-code-provider/src/doctor.ts";
import { SessionImageStore } from "pi-claude-code-provider/src/session-image-store.ts";
import { resolveSession, sessionRegistry } from "pi-claude-code-provider/src/session-registry.ts";
import { normalizeClaudeOverflow } from "pi-claude-code-provider/src/errors.ts";

const exec = promisify(execFile);
const MODEL_IDS = ["claude-fable-5-1", "claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-4-5"];

export default async function (pi: ExtensionAPI) {
  const config = JSON.parse(await readFile(join(getAgentDir(), "claude-accounts.json"), "utf8"));
  const sessions = sessionRegistry();
  const imageStore = new SessionImageStore();
  let ownId: string | undefined;
  const ids = new Set<string>(config.accounts.map((a: any) => a.id));
  const compat = await import("@earendil-works/pi-ai/compat").catch(() => undefined);
  const registrations: Array<() => void> = [];
  const { stdout: versionText } = await exec(config.claude, ["--version"], { timeout: 15000 });
  const version = versionText.match(/\d+\.\d+\.\d+/)?.[0];
  if (!version) throw new Error("Cannot determine Claude Code version");
  const { stdout: help } = await exec(config.claude, ["--help"], { timeout: 15000 });
  validateClaudeCapabilities(help);

  for (const account of config.accounts) {
    const api = `${account.id}-headless`;
    const streamSimple = createClaudeStream({ executable: account.executable, version, subscriptionType: account.subscriptionType }, {
      resolveSession: request => resolveSession(sessions, request),
    });
    const models = getModels("anthropic").filter(m => MODEL_IDS.includes(m.id)).map(m => ({
      id: m.id, name: `${m.name} · ${account.label}`,
      // CLI transport uses its own effort support and output limits.
      reasoning: m.id !== "claude-haiku-4-5", input: m.input,
      contextWindow: m.contextWindow,
      maxTokens: m.id === "claude-haiku-4-5" ? 32000 : m.id === "claude-opus-5-5" ? 128000 : 64000,
      thinkingLevelMap: m.id === "claude-haiku-4-5" ? undefined : { off: null, minimal: null, low: "low", medium: "medium", high: "high", xhigh: "xhigh", max: "max" },
      // Catalog-equivalent estimates, NOT subscription billing or remaining quota.
      cost: m.cost,
    }));
    pi.registerProvider(account.id, {
      name: account.label, api, baseUrl: "claude-code://local",
      apiKey: "cli-owned-subscription", models, streamSimple,
    });
    const register = () => {
      if (compat && !compat.getApiProvider(api)) compat.registerApiProvider({ api, stream: streamSimple, streamSimple }, account.id);
    };
    registrations.push(register);
    register();
  }
  pi.on("session_start", (_event, ctx) => {
    imageStore.open();
    registrations.forEach(register => register());
    if (ownId) sessions.delete(ownId);
    ownId = ctx.sessionManager.getSessionId();
    sessions.set(ownId, { cwd: ctx.cwd, imageStore, onRateLimitNotice: notice => {
      const reset = notice.resetsAt ? `; reset ${new Date(notice.resetsAt).toLocaleString()}` : "";
      ctx.ui.notify(`${ctx.model?.provider}: ${notice.rateLimitType} ${notice.status}${reset}. Switch account with /model.`, "warning");
    }});
  });
  pi.on("session_shutdown", async () => {
    if (ownId) sessions.delete(ownId);
    ownId = undefined;
    await imageStore.close();
    if (!sessions.size) for (const id of ids) compat?.unregisterApiProviders(id);
  });
  pi.on("message_end", event => {
    const m = event.message;
    if (m.role !== "assistant" || m.stopReason !== "error" || !ids.has(m.provider)) return;
    const errorMessage = normalizeClaudeOverflow(m.errorMessage ?? "");
    if (errorMessage !== m.errorMessage) return { message: { ...m, errorMessage } };
  });
  pi.registerCommand("claude-accounts", {
    description: "Check the three Claude subscription identities and tool bridge (no inference)",
    handler: async (_args, ctx) => {
      for (const account of config.accounts) {
        try {
          const { stdout } = await exec(account.executable, ["auth", "status"], { timeout: 25000 });
          const plan = parseAuthStatus(stdout);
          ctx.ui.notify(`${account.id}: authenticated (${plan}); /model → ${account.id}`, "info");
        } catch {
          ctx.ui.notify(`${account.id}: authentication/identity check failed; no fallback`, "error");
        }
      }
      const bridge = await probeBridge().catch(() => ({ ok: false }));
      ctx.ui.notify(`Claude ${version}; tool bridge ${bridge.ok ? "OK" : "FAILED"}. Cost display is a catalog estimate, not quota or charges.`, bridge.ok ? "info" : "error");
    },
  });
}
