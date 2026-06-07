#!/bin/bash
# Install script for agentic coding config
# Symlinks config files to their correct locations

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Define symlinks: "source:destination"
SYMLINKS=(
  # Claude
  "$SCRIPT_DIR/claude/skills:$HOME/.claude/skills"
  "$SCRIPT_DIR/claude/hooks:$HOME/.claude/hooks"
  "$SCRIPT_DIR/claude/settings.json:$HOME/.claude/settings.json"
  "$SCRIPT_DIR/claude/CLAUDE.md:$HOME/.claude/CLAUDE.md"
  # Codex
  "$SCRIPT_DIR/codex/rules:$HOME/.codex/rules"
  # Antigravity (agy) — replaced Gemini CLI in May 2026
  "$SCRIPT_DIR/antigravity/settings.json:$HOME/.gemini/antigravity-cli/settings.json"
  # OpenCode
  "$SCRIPT_DIR/opencode/opencode.json:$HOME/.opencode/opencode.json"
  # Shell
  "$SCRIPT_DIR/.airc:$HOME/.airc"
)

# Skills shared with Codex (subset of claude/skills/). A name with a real dir
# in codex/skills/ uses that override; otherwise it links from claude/skills/.
CODEX_SKILLS=(
  code-review debug-log doc explain frontend-design ideation optimize-seo pdf
  perf-test read-docs review-architecture review-cleancode review-comments
  review-history review-interfaces review-perf review-plan review-product
  review-security skill-creator squash-commits temp test theme-factory
)

create_symlink() {
  local source="$1"
  local dest="$2"

  # Check if source exists
  if [[ ! -e "$source" ]]; then
    echo "⚠️  Source does not exist: $source (skipping)"
    return
  fi

  # Check if destination already exists
  if [[ -e "$dest" || -L "$dest" ]]; then
    # Check if it's already the correct symlink
    if [[ -L "$dest" && "$(readlink "$dest")" == "$source" ]]; then
      echo "✓  Already linked: $dest"
      return
    fi

    echo ""
    echo "File already exists: $dest"
    if [[ -L "$dest" ]]; then
      echo "   (symlink to: $(readlink "$dest"))"
    fi
    echo ""
    read -p "Replace with symlink to $source? [y/n/q] " choice
    case "$choice" in
      y|Y)
        rm -rf "$dest"
        ;;
      q|Q)
        echo "Aborted."
        exit 0
        ;;
      *)
        echo "⏭️  Skipped: $dest"
        return
        ;;
    esac
  fi

  # Ensure parent directory exists
  mkdir -p "$(dirname "$dest")"

  # Create symlink
  ln -s "$source" "$dest"
  echo "✓  Linked: $dest -> $source"
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

echo "Installing agentic coding config..."
echo ""

generate_permissions
echo ""

for entry in "${SYMLINKS[@]}"; do
  source="${entry%%:*}"
  dest="${entry##*:}"
  create_symlink "$source" "$dest"
done

install_codex_skills

install_claude_mcp_servers() {
  echo ""
  echo "Installing Claude MCP servers..."

  if ! command -v claude &>/dev/null; then
    echo "⚠️  Claude CLI not found, skipping MCP server setup"
    return
  fi

  # Todoist MCP (requires TODOIST_API_TOKEN env var at runtime)
  local existing
  existing="$(claude mcp list 2>/dev/null)"
  if echo "$existing" | grep -q "todoist"; then
    echo "✓  Todoist MCP server already configured"
  else
    echo ""
    read -p "Add Todoist MCP server? (requires TODOIST_API_TOKEN env var) [y/n] " choice
    case "$choice" in
      y|Y)
        claude mcp add --transport http --scope user todoist https://ai.todoist.net/mcp \
          --header 'Authorization: Bearer ${TODOIST_API_TOKEN}'
        echo "✓  Added Todoist MCP server"
        ;;
      *)
        echo "⏭️  Skipped Todoist MCP server"
        ;;
    esac
  fi
}

install_claude_mcp_servers

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

check_agy_installed

echo ""
add_airc_to_zshrc

echo ""
echo "Done! Run 'source ~/.airc' or restart your shell to load AI aliases."
