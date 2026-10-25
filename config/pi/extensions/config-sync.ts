/** Read-only configuration and background-sync status; no model calls. */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { homedir } from "node:os";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("config-sync", {
    description: "Check this Pi profile against agents-config (read only)",
    handler: async (_args, ctx) => {
      const installer = resolve(dirname(fileURLToPath(import.meta.url)), "../install.py");
      const profile = process.env.PI_CODING_AGENT_DIR || resolve(homedir(), ".pi/agent");
      const args = [installer, "--runtime-only", "--check", "--agent-dir", profile];
      if (process.env.PI_SYNC_HOST_CONFIG) args.push("--host-config", process.env.PI_SYNC_HOST_CONFIG);
      const result = await pi.exec("python3", args, { timeout: 15000 });
      const automatic = resolve(dirname(installer), "auto_sync.py");
      const status = await pi.exec("python3", [automatic, "status", "--config", resolve(profile, "auto-sync/config.json")], { timeout: 5000 });
      ctx.ui.notify((result.stdout || "Configuration check failed; run install.py --check in a terminal.") + "\nAutomatic sync: " + (status.stdout || "not configured"),
        result.code === 0 && status.code === 0 ? "info" : "warning");
    },
  });
}
