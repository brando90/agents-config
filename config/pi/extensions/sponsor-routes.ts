// TLDR: Hide duplicate generic chat routes and migrate sessions only after verifying the same credential.
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join, resolve } from "node:path";

export async function applySponsorRoutes(pi, ctx, manifest, keysDir) {
  const registry = ctx.modelRegistry;
  const available = registry.getAvailable();
  for (const source of new Set(manifest.providers.map((entry) => entry.provider))) {
    const original = registry.getAll().filter((model) => model.provider === source);
    if (!original.length || original.some((model) => registry.isUsingOAuth(model))) continue;
    const credential = await registry.getApiKeyForProvider(source);
    if (!credential) continue;
    let alias;
    let allowedModels;
    for (const entry of manifest.providers.filter((entry) => entry.provider === source)) {
      if (!available.some((model) => model.provider === entry.id)) continue;
      try {
        if (readFileSync(join(keysDir, entry.keyFile), "utf8").trim() === credential.trim()) {
          alias = entry.id;
          allowedModels = entry.models;
          break;
        }
      } catch { /* An unavailable key cannot establish the funding identity. */ }
    }
    if (!alias) continue;
    // Keep newly discovered upstream chat models under the same verified sponsor too.
    const namedModels = new Map(available.filter((model) => model.provider === alias).map((model) => [model.id, model]));
    for (const model of original) {
      if (allowedModels && !allowedModels.includes(model.id)) continue;
      namedModels.set(model.id, { ...model, provider: alias, name: `${model.name || model.id} [${alias}]` });
    }
    pi.registerProvider(alias, { models: [...namedModels.values()] });
    // Move the current session before removing its old route. Never change payer or model.
    if (ctx.model?.provider === source) {
      if (!namedModels.has(ctx.model.id)) continue;
      const replacement = registry.find(alias, ctx.model.id);
      if (!replacement || !(await pi.setModel(replacement))) continue;
    }
    const models = [
      ...registry.getModelsOfType("image", source),
      ...registry.getModelsOfType("classifier", source),
    ];
    pi.registerProvider(source, { models });
  }
}

export default function sponsorRoutes(pi) {
  pi.on("session_start", async (_event, ctx) => {
    const manifest = JSON.parse(readFileSync(resolve(import.meta.dirname, "../providers.json"), "utf8"));
    await applySponsorRoutes(pi, ctx, manifest, join(homedir(), "keys"));
  });
}
