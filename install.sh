#!/bin/bash
# Bootstrap the agentic coding config on a new machine.
#
# This runs the reconcile step (sync.sh) — which regenerates config, applies
# symlinks, merges settings, and links skills — and then the ONE-TIME
# interactive setup: registering MCP servers, sourcing .airc from .zshrc, and
# checking for the Antigravity CLI.
#
# For routine changes (new skill/permission/fragment/setting), run ./sync.sh
# instead — it's non-interactive and skips all the one-time bootstrap below.
#
# Usage: ./install.sh [--autonomous]
#   --autonomous   install the autonomous-dev profile (broader git/permissions)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Profile selection. Default is the normal profile; --autonomous selects the
# more-permissive autonomous-dev profile. The choice is passed to (and persisted
# by) sync.sh so later bare `./sync.sh` runs reuse it.
PROFILE="normal"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --autonomous)
      PROFILE="autonomous"
      ;;
    -h|--help)
      echo "Usage: $0 [--autonomous]"
      echo "  --autonomous   install the autonomous-dev profile (broader git/permissions)"
      echo ""
      echo "For routine config changes, run ./sync.sh instead."
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: $0 [--autonomous]" >&2
      exit 1
      ;;
  esac
  shift
done

echo "Bootstrapping agentic coding config... (${PROFILE} profile)"
echo ""

# --- Reconcile (regenerate, symlink, merge settings, link skills) ---
"$SCRIPT_DIR/sync.sh" "--$PROFILE"

# --- One-time interactive bootstrap ---

# HTTP MCP servers to register at user scope. Each entry is
# "name|url|ENV_VAR" — the token is read from ENV_VAR at runtime via Claude
# Code's ${...} header interpolation (the value is never stored in config).
# The matching secret must be in the SOPS store so the claude wrapper injects
# it; see ~/rc/CLAUDE.md.
CLAUDE_MCP_SERVERS=(
  "todoist|https://ai.todoist.net/mcp|TODOIST_API_TOKEN"
  "jina|https://mcp.jina.ai/v1|JINA_API_KEY"
)

install_claude_mcp_servers() {
  echo ""
  echo "Installing Claude MCP servers..."

  if ! command -v claude &>/dev/null; then
    echo "⚠️  Claude CLI not found, skipping MCP server setup"
    return
  fi

  local existing
  existing="$(claude mcp list 2>/dev/null)"

  local entry name url var
  for entry in "${CLAUDE_MCP_SERVERS[@]}"; do
    name="${entry%%|*}"
    var="${entry##*|}"
    url="${entry#*|}"; url="${url%|*}"

    if echo "$existing" | grep -q "^$name:"; then
      echo "✓  $name MCP server already configured"
      continue
    fi

    echo ""
    read -p "Add $name MCP server? (requires \$$var env var) [y/n] " choice
    case "$choice" in
      y|Y)
        claude mcp add --transport http --scope user "$name" "$url" \
          --header "Authorization: Bearer \${$var}"
        echo "✓  Added $name MCP server"
        ;;
      *)
        echo "⏭️  Skipped $name MCP server"
        ;;
    esac
  done
}

check_agy_installed() {
  echo ""
  if command -v agy &>/dev/null; then
    echo "✓  Antigravity CLI (agy) is installed"
  else
    echo "⚠️  Antigravity CLI (agy) is not on PATH."
    echo "   Install with: curl -fsSL https://antigravity.google/cli/install.sh | bash"
    echo "   (then run 'agy' once to complete OAuth)"
  fi
}

add_airc_to_zshrc() {
  local zshrc="$HOME/.zshrc"
  local source_line='[ -f ~/.airc ] && source ~/.airc'

  if [[ ! -f "$zshrc" ]]; then
    echo "⚠️  No .zshrc found, skipping airc import"
    return
  fi

  # Check if already sourced
  if grep -qF '.airc' "$zshrc"; then
    echo "✓  .airc already sourced in .zshrc"
    return
  fi

  echo ""
  read -p "Add 'source ~/.airc' to .zshrc? [y/n] " choice
  case "$choice" in
    y|Y)
      echo "" >> "$zshrc"
      echo "# AI tools (Claude, etc.)" >> "$zshrc"
      echo "$source_line" >> "$zshrc"
      echo "✓  Added .airc import to .zshrc"
      ;;
    *)
      echo "⏭️  Skipped adding to .zshrc"
      ;;
  esac
}

install_claude_mcp_servers
check_agy_installed
echo ""
add_airc_to_zshrc

echo ""
echo "Done! Run 'source ~/.airc' or restart your shell to load AI aliases."
echo "For routine config changes from now on, run ./sync.sh (no prompts)."
