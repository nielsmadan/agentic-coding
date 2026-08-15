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

# --- Symlinks: "source:destination" ---
# Only files this repo still stages. Everything loadout generates is written
# straight to its destination (see the [instructions.*] and [permissions.*]
# blocks in loadout.toml), so it needs no link.
SYMLINKS=(
  # Claude
  "$SCRIPT_DIR/claude/skills:$HOME/.claude/skills"
  "$SCRIPT_DIR/claude/hooks:$HOME/.claude/hooks"
  # Pi (pi-coding-agent) — settings.json holds packages and enabledModels.
  # Skills need no wiring: pi auto-discovers ~/.agents/skills (populated by
  # install_codex_skills below).
  "$SCRIPT_DIR/pi/settings.json:$HOME/.pi/agent/settings.json"
  "$SCRIPT_DIR/pi/mcp.json:$HOME/.pi/agent/mcp.json"
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
  # source no shell config, so jina-fetch is also linked into ~/.local/bin,
  # which their plists put on PATH.
  "$SCRIPT_DIR/bin/jina-fetch:$HOME/.local/bin/jina-fetch"
)

# Destinations loadout now writes directly, which earlier versions of this
# script symlinked back into the repo. Left in place, a link would make loadout
# write through it and recreate the staged copy.
RETIRED_LINKS=(
  "$HOME/.claude/CLAUDE.md"
  "$HOME/.claude/mcp-permissions.json"
  "$HOME/.claude/settings.json"
  "$HOME/.codex/rules"
  "$HOME/.codex/AGENTS.md"
  "$HOME/.pi/agent/AGENTS.md"
  "$HOME/.pi/agent/extensions/pi-permission-system/config.json"
  "$HOME/.config/opencode/opencode.json"
)

# Skills shared with Codex (subset of claude/skills/). A name with a real dir
# in codex/skills/ uses that override; otherwise it links from claude/skills/.
CODEX_SKILLS=(
  check-agent-logs check-notes commit
  code-review debug-log deslop doc evaluate-tech explain guide huh ideation
  library-docs nono-sandbox pdf
  perf-test permission read-docs resolve-conflicts review-architecture review-cleancode review-comments
  review-history review-interfaces review-library-use review-perf review-plan review-product
  review-security review-swift review-todo review-typescript research-general research-tech second-opinion skill-creator
  squash-commits temp test
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

generate_skills() {
  local script="$SCRIPT_DIR/skills/sync.py"

  if [[ ! -f "$script" ]]; then
    echo "⚠️  Skills generator not found: $script (skipping)"
    return
  fi
  if ! command -v python3 &>/dev/null; then
    echo "⚠️  python3 not found — skipping skills generation"
    echo "    (the committed skill files will be used as-is)"
    return
  fi

  echo "Generating multi-harness skill files from skills/..."
  if python3 "$script"; then
    echo "✓  Skill files up to date"
  else
    echo "⚠️  Skills generation failed — using committed files"
  fi
}

generate_mcp() {
  local script="$SCRIPT_DIR/mcp/sync.py"

  if [[ ! -f "$script" ]]; then
    echo "⚠️  MCP generator not found: $script (skipping)"
    return
  fi
  if ! command -v python3 &>/dev/null; then
    echo "⚠️  python3 not found — skipping MCP server generation"
    echo "    (the committed MCP files will be used as-is)"
    return
  fi

  echo "Generating agent MCP server config from mcp/servers.toml..."
  if python3 "$script"; then
    echo "✓  MCP server config up to date"
  else
    echo "⚠️  MCP server generation failed — using committed files"
  fi
}

# Claude Code has no user-scope MCP file we can symlink: ~/.claude.json is
# runtime state and ~/.claude/settings.json has no mcpServers key. So register
# missing servers through the CLI instead. Add-only — `claude mcp add-json`
# has no overwrite flag, so a changed url/args needs a manual remove + re-add.
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

install_codex_skills() {
  local dest_dir="$HOME/.agents/skills"
  local claude_src="$SCRIPT_DIR/claude/skills"
  local override_src="$SCRIPT_DIR/codex/skills"

  mkdir -p "$dest_dir"

  echo ""
  echo "Installing Codex skills to $dest_dir..."

  local wanted=" ${CODEX_SKILLS[*]} "

  # Stale cleanup: only remove symlinks pointing into this repo whose target
  # is gone or whose basename is no longer in CODEX_SKILLS. Links pointing
  # outside this repo (e.g. find-skills from the npx skills CLI) are untouched.
  for dest in "$dest_dir"/*; do
    if [[ ! -L "$dest" ]]; then
      continue
    fi

    local target
    local name
    target="$(readlink "$dest")"
    name="$(basename "$dest")"

    if [[ "$target" == "$SCRIPT_DIR/"* ]]; then
      if [[ ! -e "$dest" ]] || [[ "$wanted" != *" $name "* ]]; then
        rm -f "$dest"
        echo "✓  Removed stale skill link: $dest"
      fi
    fi
  done

  for name in "${CODEX_SKILLS[@]}"; do
    local source="$claude_src/$name"
    # Prefer a real override dir in codex/skills/ (ignore lingering symlinks).
    if [[ -d "$override_src/$name" && ! -L "$override_src/$name" ]]; then
      source="$override_src/$name"
    fi

    if [[ ! -e "$source" ]]; then
      echo "⚠️  Source for skill '$name' does not exist (skipping): $source"
      continue
    fi

    create_symlink "$source" "$dest_dir/$name"
  done

  # Legacy cleanup: remove repo-pointing symlinks from the old ~/.codex/skills/
  # (Codex now reads ~/.agents/skills/). Leaves .system/ and non-ours untouched.
  local legacy_dir="$HOME/.codex/skills"
  if [[ -d "$legacy_dir" ]]; then
    for dest in "$legacy_dir"/*; do
      if [[ ! -L "$dest" ]]; then
        continue
      fi
      local target
      target="$(readlink "$dest")"
      if [[ "$target" == "$SCRIPT_DIR/"* ]]; then
        rm -f "$dest"
        echo "✓  Removed legacy Codex skill link: $dest"
      fi
    done
  fi
}

# --- Reconcile ---
echo "Syncing agentic coding config... (${PROFILE} profile)"
echo ""

retire_links
generate_skills
echo ""
# Before loadout: mcp/sync.py owns the `mcp` key of ~/.config/opencode/opencode.json
# and loadout preserves it, so the key has to be current when loadout renders.
generate_mcp
echo ""
generate_loadout
echo ""

sync_codex_config
echo ""
sync_codex_superpowers
echo ""
seed_private_profile


for entry in "${SYMLINKS[@]}"; do
  source="${entry%%:*}"
  dest="${entry##*:}"
  create_symlink "$source" "$dest"
done
echo ""

sync_claude_mcp

install_codex_skills

echo ""
echo "✓  Sync complete (${PROFILE} profile)."
