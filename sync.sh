#!/bin/bash
# Reconcile this machine's agentic-coding config with the repo.
#
# Idempotent and non-interactive: safe to re-run any time config changes
# (a new skill, permission, global fragment, or settings edit). This is the
# "run more than once" half of setup. install.sh calls it, then layers the
# one-time interactive bootstrap (MCP servers, .zshrc, agy check) on top.
#
# What it does:
#   - regenerate permission + global-instruction files from their sources
#   - apply all symlinks (skip-if-correct; back up a real file, never clobber)
#   - merge repo-managed keys into ~/.claude/settings.json (see merge_settings)
#   - relink the Codex/Pi skill subset and Pi permission policy
#
# Usage: ./sync.sh [--autonomous | --normal]
#   With no flag it uses the persisted profile (written by install.sh or a prior
#   run), defaulting to "normal". An explicit flag overrides AND is persisted.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROFILE_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/aiconf/profile"

# --- Profile resolution ---
EXPLICIT_PROFILE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --autonomous) EXPLICIT_PROFILE="autonomous" ;;
    --normal)     EXPLICIT_PROFILE="normal" ;;
    -h|--help)
      echo "Usage: $0 [--autonomous | --normal]"
      echo "  Reconciles machine config with the repo. Uses the persisted"
      echo "  profile when no flag is given (default: normal)."
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
  shift
done

if [[ -n "$EXPLICIT_PROFILE" ]]; then
  PROFILE="$EXPLICIT_PROFILE"
  mkdir -p "$(dirname "$PROFILE_FILE")"
  echo "$PROFILE" > "$PROFILE_FILE"          # persist explicit choice for future runs
elif [[ -f "$PROFILE_FILE" ]]; then
  PROFILE="$(cat "$PROFILE_FILE")"
else
  PROFILE="normal"
fi

if [[ "$PROFILE" == "autonomous" ]]; then
  SETTINGS_SRC="$SCRIPT_DIR/claude/settings.autonomous.json"
  CLAUDEMD_SRC="$SCRIPT_DIR/claude/CLAUDE.autonomous.md"
else
  SETTINGS_SRC="$SCRIPT_DIR/claude/settings.json"
  CLAUDEMD_SRC="$SCRIPT_DIR/claude/CLAUDE.md"
fi

# --- Symlinks: "source:destination" ---
# NOTE: ~/.claude/settings.json is intentionally NOT symlinked — Claude Code
# writes to it (survey state, etc.) and an atomic write would clobber the link.
# It is reconciled by merge_settings instead.
SYMLINKS=(
  # Claude
  "$SCRIPT_DIR/claude/skills:$HOME/.claude/skills"
  "$SCRIPT_DIR/claude/hooks:$HOME/.claude/hooks"
  "$SCRIPT_DIR/claude/mcp-permissions.json:$HOME/.claude/mcp-permissions.json"
  "$CLAUDEMD_SRC:$HOME/.claude/CLAUDE.md"
  # Codex
  "$SCRIPT_DIR/codex/rules:$HOME/.codex/rules"
  "$SCRIPT_DIR/global/AGENTS.md:$HOME/.codex/AGENTS.md"
  # Antigravity (agy) — replaced Gemini CLI in May 2026
  "$SCRIPT_DIR/antigravity/settings.json:$HOME/.gemini/antigravity-cli/settings.json"
  "$SCRIPT_DIR/antigravity/mcp_config.json:$HOME/.gemini/config/mcp_config.json"
  # agy reads global instructions from ~/.gemini/GEMINI.md — same shared file as Codex
  "$SCRIPT_DIR/global/AGENTS.md:$HOME/.gemini/GEMINI.md"
  # OpenCode (reads global config from XDG ~/.config/opencode, not legacy ~/.opencode)
  "$SCRIPT_DIR/opencode/opencode.json:$HOME/.config/opencode/opencode.json"
  # Pi (pi-coding-agent) — settings.json holds packages and enabledModels;
  # permissions.json is generated for @gotgenes/pi-permission-system.
  # AGENTS.md is the same shared global-instructions file Codex/Antigravity use.
  # Skills need no wiring: pi auto-discovers ~/.agents/skills (populated by
  # install_codex_skills below).
  "$SCRIPT_DIR/pi/settings.json:$HOME/.pi/agent/settings.json"
  "$SCRIPT_DIR/pi/permissions.json:$HOME/.pi/agent/extensions/pi-permission-system/config.json"
  "$SCRIPT_DIR/pi/mcp.json:$HOME/.pi/agent/mcp.json"
  "$SCRIPT_DIR/global/AGENTS.md:$HOME/.pi/agent/AGENTS.md"
  # Shell
  "$SCRIPT_DIR/.airc:$HOME/.airc"
)

# Skills shared with Codex (subset of claude/skills/). A name with a real dir
# in codex/skills/ uses that override; otherwise it links from claude/skills/.
CODEX_SKILLS=(
  check-claude-projects check-notes commit
  code-review debug-log deslop doc evaluate-tech explain guide ideation
  library-docs pdf
  perf-test permission read-docs resolve-conflicts review-architecture review-cleancode review-comments
  review-history review-interfaces review-library-use review-perf review-plan review-product
  review-security review-swift review-typescript research-general research-tech second-opinion skill-creator
  squash-commits temp test
)

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

# Merge the repo's managed settings into the real ~/.claude/settings.json,
# preserving keys Claude Code writes itself (survey state, etc.). Repo keys win
# on conflict; keys only in the live file are kept. Writes a real file (breaking
# any leftover symlink once), so future app writes never clobber a link.
merge_settings() {
  local overlay="$SETTINGS_SRC"
  local dest="$HOME/.claude/settings.json"

  if [[ ! -f "$overlay" ]]; then
    echo "⚠️  Settings source not found: $overlay (skipping merge)"
    return
  fi
  if ! command -v python3 &>/dev/null; then
    echo "⚠️  python3 not found — settings merge skipped"
    return
  fi

  python3 - "$overlay" "$dest" <<'PY'
import json, os, sys, tempfile
overlay_path, dest_path = sys.argv[1], sys.argv[2]

with open(overlay_path) as f:
    overlay = json.load(f)

base = {}
if os.path.exists(dest_path):
    try:
        with open(dest_path) as f:
            base = json.load(f)
    except Exception:
        base = {}   # corrupt/empty live file → repo overlay becomes the file

def deep_merge(b, o):
    if isinstance(b, dict) and isinstance(o, dict):
        out = dict(b)
        for k, v in o.items():
            out[k] = deep_merge(b[k], v) if k in b else v
        return out
    return o   # overlay wins for scalars and lists

merged = deep_merge(base, overlay)

d = os.path.dirname(dest_path)
os.makedirs(d, exist_ok=True)
fd, tmp = tempfile.mkstemp(dir=d)
with os.fdopen(fd, "w") as f:
    json.dump(merged, f, indent=2, ensure_ascii=False)
    f.write("\n")
os.replace(tmp, dest_path)     # replaces a symlink with a real file, atomically
print(f"✓  Merged settings -> {dest_path} (repo keys applied, app keys preserved)")
PY
}

generate_permissions() {
  local script="$SCRIPT_DIR/permissions/sync.py"

  if [[ ! -f "$script" ]]; then
    echo "⚠️  Permission generator not found: $script (skipping)"
    return
  fi
  if ! command -v python3 &>/dev/null; then
    echo "⚠️  python3 not found — skipping permission generation"
    echo "    (the committed permission files will be used as-is)"
    return
  fi

  echo "Generating agent permission config from permissions/permissions.toml..."
  if python3 "$script"; then
    echo "✓  Permission config up to date"
  else
    echo "⚠️  Permission generation failed — using committed permission files"
  fi
}

generate_global() {
  local script="$SCRIPT_DIR/global/sync.py"

  if [[ ! -f "$script" ]]; then
    echo "⚠️  Global-instructions generator not found: $script (skipping)"
    return
  fi
  if ! command -v python3 &>/dev/null; then
    echo "⚠️  python3 not found — skipping global-instructions generation"
    echo "    (the committed instruction files will be used as-is)"
    return
  fi

  echo "Generating global agent instructions from global/fragments/..."
  if python3 "$script"; then
    echo "✓  Global instructions up to date"
  else
    echo "⚠️  Global-instructions generation failed — using committed files"
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

generate_permissions
echo ""
generate_global
echo ""
generate_skills
echo ""
generate_mcp
echo ""

sync_codex_config
echo ""

for entry in "${SYMLINKS[@]}"; do
  source="${entry%%:*}"
  dest="${entry##*:}"
  create_symlink "$source" "$dest"
done
echo ""

merge_settings

sync_claude_mcp

install_codex_skills

echo ""
echo "✓  Sync complete (${PROFILE} profile)."
