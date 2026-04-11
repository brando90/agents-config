#!/usr/bin/env bash
# Setup script for Google Gemini CLI
# Ref: https://github.com/google-gemini/gemini-cli
# Tracks: https://github.com/brando90/agents-config/issues/17
#
# Usage:
#   bash setup_gemini_cli.sh              # interactive OAuth (opens browser once)
#   bash setup_gemini_cli.sh --api-key    # headless-friendly, uses API key
#
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { printf "${GREEN}[INFO]${NC}  %s\n" "$*"; }
warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$*"; }
err()   { printf "${RED}[ERR]${NC}   %s\n" "$*" >&2; }

# ---------- 1. Check prerequisites ----------
check_prereqs() {
    info "Checking prerequisites..."

    if ! command -v node &>/dev/null; then
        err "Node.js is not installed. Install it first:"
        echo "  https://nodejs.org  or  'sudo apt install nodejs npm'  or  'brew install node'"
        exit 1
    fi

    NODE_VER=$(node -v | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_VER" -lt 18 ]; then
        err "Node.js >= 18 required (found v${NODE_VER}). Please upgrade."
        exit 1
    fi
    info "Node.js $(node -v) found."

    if ! command -v npm &>/dev/null; then
        err "npm is not installed. It usually ships with Node.js."
        exit 1
    fi
    info "npm $(npm -v) found."
}

# ---------- 2. Install gemini-cli ----------
install_gemini() {
    if command -v gemini &>/dev/null; then
        info "gemini-cli is already installed: $(gemini --version 2>/dev/null || echo 'unknown version')"
        read -rp "Reinstall/upgrade? [y/N] " ans
        if [[ ! "$ans" =~ ^[Yy] ]]; then
            info "Skipping install."
            return
        fi
    fi

    info "Installing @google/gemini-cli globally..."
    npm install -g @google/gemini-cli
    info "Installed: $(gemini --version 2>/dev/null || echo 'ok')"
}

# ---------- 3a. OAuth login (browser) ----------
setup_oauth() {
    info "--- OAuth Login (Sign in with Google) ---"
    echo ""
    echo "This will open a browser window. Sign in with your Google account and"
    echo "authorize the CLI. After that, credentials are cached — you won't need"
    echo "to do this again on this machine."
    echo ""
    echo ">>> YOUR ONLY INTERACTION: click 'Allow' in the browser. <<<"
    echo ""
    read -rp "Press Enter to open the browser login... "
    gemini --login 2>/dev/null || gemini  # --login flag may not exist; fallback to interactive
}

# ---------- 3b. API key login (headless) ----------
setup_api_key() {
    info "--- API Key Setup (headless-friendly) ---"
    echo ""

    # Check if key already set
    if [ -n "${GEMINI_API_KEY:-}" ]; then
        info "GEMINI_API_KEY is already set in this shell."
        read -rp "Overwrite? [y/N] " ans
        [[ ! "$ans" =~ ^[Yy] ]] && return
    fi

    echo "Get your API key from: https://aistudio.google.com/apikey"
    echo ""
    read -rsp "Paste your Gemini API key (input hidden): " api_key
    echo ""

    if [ -z "$api_key" ]; then
        err "No key provided. Aborting."
        exit 1
    fi

    # Persist to .gemini/.env
    GEMINI_ENV_DIR="${HOME}/.gemini"
    GEMINI_ENV_FILE="${GEMINI_ENV_DIR}/.env"
    mkdir -p "$GEMINI_ENV_DIR"

    if [ -f "$GEMINI_ENV_FILE" ] && grep -q "GEMINI_API_KEY" "$GEMINI_ENV_FILE"; then
        # Update existing key
        sed -i "s|^GEMINI_API_KEY=.*|GEMINI_API_KEY=${api_key}|" "$GEMINI_ENV_FILE"
    else
        echo "GEMINI_API_KEY=${api_key}" >> "$GEMINI_ENV_FILE"
    fi
    chmod 600 "$GEMINI_ENV_FILE"
    info "Key saved to ${GEMINI_ENV_FILE} (mode 600)."

    # Also export for this session
    export GEMINI_API_KEY="$api_key"
    info "GEMINI_API_KEY exported for this shell session."
}

# ---------- 4. Verify ----------
verify() {
    info "Verifying gemini-cli works..."
    if gemini -p "Say exactly: hello world" 2>/dev/null | head -5; then
        echo ""
        info "Gemini CLI is working!"
    else
        warn "Could not verify. You may need to run 'gemini' interactively to finish setup."
    fi
}

# ---------- 5. Print summary ----------
summary() {
    echo ""
    echo "=========================================="
    info "Setup complete!"
    echo "=========================================="
    echo ""
    echo "Quick commands:"
    echo "  gemini                  # start interactive session"
    echo "  gemini -p 'question'   # one-shot prompt"
    echo "  gemini /stats           # check token usage"
    echo ""
    echo "Config location:  ~/.gemini/settings.json"
    echo "Auth cache:       ~/.gemini/"
    echo ""
}

# ---------- Main ----------
main() {
    echo "============================================="
    echo "  Gemini CLI Setup"
    echo "============================================="
    echo ""

    check_prereqs
    install_gemini

    if [[ "${1:-}" == "--api-key" ]]; then
        setup_api_key
    else
        setup_oauth
    fi

    verify
    summary
}

main "$@"
