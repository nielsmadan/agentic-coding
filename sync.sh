#!/bin/bash
# Reconcile this machine's agentic-coding config with the repo.
#
# Idempotent and non-interactive: safe to re-run any time config changes
# (a new skill, permission, global fragment, or settings edit). This is the
# "run more than once" half of setup. install.sh calls it, then layers the
# one-time interactive bootstrap (MCP servers, .zshrc) on top.
#
# What it does:
#   - regenerate permission + global-instruction files straight to the paths the
#     agents read (loadout owns those; nothing is staged in this repo first)
#   - apply the remaining symlinks (skip-if-correct; back up a real file, never
#     clobber) for the files other generators still stage here
#   - make installed Codex Superpowers skills explicit-invocation only
#   - relink the Codex/Pi skill subset and Pi permission policy
#
# Usage: ./sync.sh [--autonomous | --normal]
#   With no flag it uses the profile recorded in loadout's machine config,
#   defaulting to "default". An explicit flag overrides AND is persisted there.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MACHINE_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/loadout/config.toml"

# --- Profile resolution ---
# loadout's machine config is the only store: it names this machine's source and
# profile, and `loadout sync --global` reads both. Selecting a profile is now
# entirely "write it here" — nothing downstream picks between staged files.
write_machine_config() {
  mkdir -p "$(dirname "$MACHINE_CONFIG")"
  printf 'source = "%s"\nprofile = "%s"\n' "$SCRIPT_DIR" "$1" > "$MACHINE_CONFIG"
}

EXPLICIT_PROFILE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --autonomous) EXPLICIT_PROFILE="autonomous" ;;
    --normal)     EXPLICIT_PROFILE="default" ;;
    -h|--help)
      echo "Usage: $0 [--autonomous | --normal]"
      echo "  Reconciles machine config with the repo. Uses the profile in"
      echo "  $MACHINE_CONFIG when no flag is given (default: default)."
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
  shift
done

if [[ -n "$EXPLICIT_PROFILE" ]]; then
  write_machine_config "$EXPLICIT_PROFILE"
elif [[ ! -f "$MACHINE_CONFIG" ]]; then
  write_machine_config "default"
fi

PROFILE="$(sed -n 's/^profile *= *"\(.*\)"/\1/p' "$MACHINE_CONFIG" | tail -1)"
PROFILE="${PROFILE:-default}"

# --- Locally-developed Claude plugins: "name:built-marketplace-path" ---
# Only the marketplace registration lives here. `~/.claude/plugins/known_marketplaces.json`
# is an install registry Claude rewrites itself, so loadout cannot render it (ADR 0015).
# The enabling half is `enabledPlugins` in loadout/settings/claude.json.
LOCAL_MARKETPLACES=(
  "mouthfeel:$HOME/wrksp/oss/mouthfeel/dist/claude"
)

# --- Symlinks: "source:destination" ---
# Only files this repo still stages. Everything loadout generates is written
# straight to its destination (see the [instructions.*] and [permissions.*]
# blocks in loadout.toml), so it needs no link.
SYMLINKS=(
  # nono sandbox. Each <agent>-local profile extends its nolabs-ai pack, which
  # must be pulled first (`nono pull nolabs-ai/<agent>`) — without the pack the
  # profile is inert. agent-common carries the grants they all share.
  "$SCRIPT_DIR/nono/agent-common.json:$HOME/.config/nono/profiles/agent-common.json"
  "$SCRIPT_DIR/nono/agent-private.json:$HOME/.config/nono/profiles/agent-private.json"
  "$SCRIPT_DIR/nono/claude-local.json:$HOME/.config/nono/profiles/claude-local.json"
  "$SCRIPT_DIR/nono/codex-local.json:$HOME/.config/nono/profiles/codex-local.json"
  "$SCRIPT_DIR/nono/opencode-local.json:$HOME/.config/nono/profiles/opencode-local.json"
  "$SCRIPT_DIR/nono/pi-local.json:$HOME/.config/nono/profiles/pi-local.json"
  # Shell
  "$SCRIPT_DIR/.airc:$HOME/.airc"
  # bin/ is on PATH in interactive shells via .airc.d/00-path.zsh. launchd jobs
  # source no shell config, so these are also linked into ~/.local/bin, which
  # their plists put on PATH. sops-exec is additionally what ~/rc's editor
  # wrappers call, so it must resolve without ~/.airc having been sourced.
  "$SCRIPT_DIR/bin/jina-fetch:$HOME/.local/bin/jina-fetch"
  "$SCRIPT_DIR/bin/sops-exec:$HOME/.local/bin/sops-exec"
)

# Destinations loadout now writes directly, which earlier versions of this
# script symlinked back into the repo. Left in place, a link would make loadout
# write through it and recreate the staged copy.
RETIRED_LINKS=(
  "$HOME/.claude/CLAUDE.md"
  "$HOME/.claude/mcp-permissions.json"
  "$HOME/.claude/settings.json"
  "$HOME/.claude/hooks"
  "$HOME/.codex/rules"
  "$HOME/.codex/AGENTS.md"
  "$HOME/.pi/agent/AGENTS.md"
  "$HOME/.pi/agent/extensions/pi-permission-system/config.json"
  "$HOME/.pi/agent/settings.json"
  "$HOME/.config/opencode/opencode.json"
  "$HOME/.pi/agent/mcp.json"
)

# agent-private.json holds machine-specific grants (client names, private paths)
# and is gitignored, so a fresh clone has none. Every <agent>-local profile
# extends it, so it must exist — create an empty one rather than fail.
seed_private_profile() {
  local target="$SCRIPT_DIR/nono/agent-private.json"
  [[ -f "$target" ]] && return
  printf '%s\n' '{' '  "meta": { "name": "agent-private" },' '  "filesystem": {}' '}' > "$target"
  echo "✓  Created empty $target (gitignored; add machine-specific grants here)"
}

# nono ignores a grant whose path does not exist ("... does not exist and will be
# ignored"), so a tool that creates its state directory lazily can never create
# it: the grant is skipped for being absent, and the mkdir is then denied. Only
# an unsandboxed step can break that cycle. List directories granted in
# nono/agent-common.json that nothing else creates first.
seed_granted_state_dirs() {
  local dir
  for dir in "$HOME/.local/state/mouthfeel"; do
    [[ -d "$dir" ]] && continue
    mkdir -p "$dir"
    echo "✓  Created $dir (granted in nono/agent-common.json; nono skips absent paths)"
  done
}

# Non-interactive symlink: correct link → skip; wrong link → silently relink
# (a symlink holds no data); a real file/dir where a link belongs → back it up
# (never rm -rf unattended), then link.
create_symlink() {
  local source="$1"
  local dest="$2"

  if [[ ! -e "$source" ]]; then
    echo "⚠️  Source does not exist: $source (skipping)"
    return
  fi

  if [[ -L "$dest" ]]; then
    if [[ "$(readlink "$dest")" == "$source" ]]; then
      echo "✓  Already linked: $dest"
      return
    fi
    rm -f "$dest"                              # wrong symlink — no data to lose
  elif [[ -e "$dest" ]]; then
    local bak="$dest.bak.$(date +%Y%m%d%H%M%S)"
    mv "$dest" "$bak"                          # real file/dir — preserve it
    echo "↩  Backed up existing $dest -> $bak"
  fi

  mkdir -p "$(dirname "$dest")"
  ln -s "$source" "$dest"
  echo "✓  Linked: $dest -> $source"
}

# Replace a repo-pointing symlink with a real file holding the same content, so
# the destination is never empty for even an instant and a machine without
# loadout keeps the config it already had. loadout overwrites it next.
materialise_link() {
  local dest="$1"

  if [[ ! -L "$dest" ]]; then
    return
  fi
  if [[ "$(readlink "$dest")" != "$SCRIPT_DIR/"* ]]; then
    return    # someone else's link — not ours to break
  fi
  if [[ ! -e "$dest" ]]; then
    rm -f "$dest"                              # dangling; nothing to preserve
    echo "✓  Removed dangling link: $dest"
    return
  fi

  cp -RL "$dest" "$dest.materialising"
  rm -f "$dest"
  mv "$dest.materialising" "$dest"
  echo "✓  Unlinked from repo, now written directly: $dest"
}

materialise_nono_skill_link() {
  local dest="$HOME/.config/opencode/skills/nono-sandbox"

  # `return 0`, not a bare `return`: a bare one inherits the failed test's status,
  # and under `set -e` that aborts the whole sync. This function converts the link
  # into a real directory, so from its second run onwards the first test is false —
  # which silently killed every sync after the first successful materialisation.
  [[ -L "$dest" ]] || return 0
  [[ "$(readlink "$dest")" == "$HOME/.config/nono/packages/"* ]] || return 0

  if [[ -e "$dest" ]]; then
    cp -RL "$dest" "$dest.materialising"
    rm -f "$dest"
    mv "$dest.materialising" "$dest"
  else
    rm -f "$dest"
    mkdir -p "$dest"
  fi
  echo "✓  Detached generated OpenCode skill from nono's signed package store"
}

retire_links() {
  for dest in "${RETIRED_LINKS[@]}"; do
    materialise_link "$dest"
  done
}

generate_loadout() {
  if ! command -v loadout &>/dev/null; then
    echo "⚠️  loadout not found on PATH — instructions and permission config NOT regenerated"
    echo "    (this repo no longer stages copies of them, so whatever is already on"
    echo "     this machine stays as-is; install loadout from its repo with 'just install')"
    return
  fi

  echo "Generating global instructions and agent permission config with loadout..."
  if loadout sync --global; then
    echo "✓  Instructions and permission config up to date"
  else
    echo "⚠️  loadout sync failed — this machine's existing config is unchanged"
  fi
}

# Claude Code has no user-scope MCP file we can symlink: ~/.claude.json is
# runtime state and ~/.claude/settings.json has no mcpServers key. So register
# missing servers through the CLI instead. Add-only — `claude mcp add-json`
# has no overwrite flag, so a changed url/args needs a manual remove + re-add.
sync_claude_plugins() {
  echo ""
  echo "Registering local Claude plugin marketplaces..."

  if ! command -v claude &>/dev/null; then
    echo "⚠️  Claude CLI not found — skipping marketplace registration"
    return
  fi
  if ! command -v python3 &>/dev/null; then
    echo "⚠️  python3 not found — skipping marketplace registration"
    return
  fi

  local entry name path
  for entry in "${LOCAL_MARKETPLACES[@]}"; do
    name="${entry%%:*}"
    path="${entry#*:}"

    if [[ ! -d "$path" ]]; then
      echo "⚠️  $name not built yet: $path (skipping)"
      continue
    fi
    if python3 -c 'import json, os, sys
registry = os.path.expanduser("~/.claude/plugins/known_marketplaces.json")
known = json.load(open(registry)) if os.path.exists(registry) else {}
sys.exit(0 if sys.argv[1] in known else 1)' "$name"; then
      echo "✓  $name marketplace already configured"
      continue
    fi
    if claude plugin marketplace add "$path"; then
      echo "✓  Added $name marketplace"
    else
      echo "⚠️  Failed to add $name marketplace"
    fi
  done
}

sync_claude_mcp() {
  local source="$SCRIPT_DIR/claude/mcp-servers.generated.json"

  echo ""
  echo "Registering Claude MCP servers..."

  if [[ ! -f "$source" ]]; then
    echo "⚠️  MCP server list not found: $source (skipping)"
    return
  fi
  if ! command -v claude &>/dev/null; then
    echo "⚠️  Claude CLI not found — skipping MCP server registration"
    return
  fi
  if ! command -v python3 &>/dev/null; then
    echo "⚠️  python3 not found — skipping MCP server registration"
    return
  fi

  local existing
  existing="$(claude mcp list 2>/dev/null)"

  local name json
  while IFS=$'\t' read -r name json; do
    if echo "$existing" | grep -q "^$name:"; then
      echo "✓  $name MCP server already configured"
      continue
    fi
    if claude mcp add-json "$name" "$json" --scope user; then
      echo "✓  Added $name MCP server"
    else
      echo "⚠️  Failed to add $name MCP server"
    fi
  done < <(python3 -c '
import json, sys
with open(sys.argv[1]) as f:
    for name, entry in json.load(f).items():
        print(name, json.dumps(entry), sep="\t")
' "$source")
}

sync_codex_config() {
  local script="$SCRIPT_DIR/codex/sync_config.py"

  if [[ ! -f "$script" ]]; then
    echo "⚠️  Codex config sync not found: $script (skipping)"
    return
  fi
  if ! command -v python3 &>/dev/null; then
    echo "⚠️  python3 not found — skipping Codex config sync"
    return
  fi

  echo "Merging repo-managed Codex config..."
  python3 "$script"
}

sync_codex_superpowers() {
  local script="$SCRIPT_DIR/codex/sync_superpowers.py"

  if [[ ! -f "$script" ]]; then
    echo "⚠️  Codex Superpowers sync not found: $script (skipping)"
    return
  fi
  if ! command -v python3 &>/dev/null; then
    echo "⚠️  python3 not found — skipping Codex Superpowers policy sync"
    return
  fi

  echo "Making Codex Superpowers skills explicit-invocation only..."
  python3 "$script"
}

# --- Reconcile ---
echo "Syncing agentic coding config... (${PROFILE} profile)"
echo ""

retire_links
materialise_nono_skill_link
echo ""
generate_loadout
echo ""

sync_codex_config
echo ""
sync_codex_superpowers
echo ""
seed_private_profile
seed_granted_state_dirs

for entry in "${SYMLINKS[@]}"; do
  source="${entry%%:*}"
  dest="${entry##*:}"
  create_symlink "$source" "$dest"
done
echo ""

sync_claude_mcp
sync_claude_plugins

echo ""
echo "✓  Sync complete (${PROFILE} profile)."
