#!/bin/bash
# Bootstrap the agentic coding config on a new machine.
#
# This runs the reconcile step (sync.sh) — which regenerates config, applies
# symlinks, and links skills — and then the ONE-TIME
# interactive setup: registering MCP servers and sourcing .airc from .zshrc.
#
# For routine changes (new skill/permission/fragment/setting), run ./sync.sh
# instead — it's non-interactive and skips all the one-time bootstrap below.
#
# Usage: ./install.sh [--autonomous]
#   --autonomous   install the autonomous-dev profile (broader git/permissions)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Profile selection. Default is the normal profile; --autonomous selects the
# more-permissive autonomous-dev profile. The choice is passed to sync.sh, which
# records it in loadout's machine config so later bare `./sync.sh` runs reuse it.
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

# --- Reconcile (regenerate, symlink, link skills) ---
"$SCRIPT_DIR/sync.sh" "--$PROFILE"

# --- One-time interactive bootstrap ---
# MCP servers are written by loadout from loadout/mcp.toml.

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

add_airc_to_zshrc

echo ""
echo "Done! Run 'source ~/.airc' or restart your shell to load AI aliases."
echo "For routine config changes from now on, run ./sync.sh (no prompts)."
