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
  # Codex
  "$SCRIPT_DIR/codex/rules:$HOME/.codex/rules"
  # Gemini
  "$SCRIPT_DIR/gemini/settings.json:$HOME/.gemini/settings.json"
  # Shell
  "$SCRIPT_DIR/.airc:$HOME/.airc"
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

install_codex_config() {
  local source="$SCRIPT_DIR/codex/config.toml"
  local dest="$HOME/.codex/config.toml"
  local rendered

  if [[ ! -f "$source" ]]; then
    echo "⚠️  Codex config template does not exist: $source (skipping)"
    return
  fi

  mkdir -p "$(dirname "$dest")"
  rendered="$(sed "s|__PROJECT_ROOT__|$SCRIPT_DIR|g" "$source")"

  if [[ -e "$dest" || -L "$dest" ]]; then
    if [[ ! -L "$dest" && -f "$dest" ]] && diff -q "$dest" <(printf '%s\n' "$rendered") >/dev/null 2>&1; then
      echo "✓  Codex config already up to date: $dest"
      return
    fi

    echo ""
    echo "File already exists: $dest"
    if [[ -L "$dest" ]]; then
      echo "   (symlink to: $(readlink "$dest"))"
    fi
    echo ""
    read -p "Replace with generated Codex config for $SCRIPT_DIR? [y/n/q] " choice
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

  printf '%s\n' "$rendered" > "$dest"
  echo "✓  Wrote: $dest"
}

install_codex_skills() {
  local source_dir="$SCRIPT_DIR/codex/skills"
  local dest_dir="$HOME/.codex/skills"

  if [[ ! -d "$source_dir" ]]; then
    echo "⚠️  Codex skills directory does not exist: $source_dir (skipping)"
    return
  fi

  mkdir -p "$dest_dir"

  echo ""
  echo "Installing Codex skills..."

  for dest in "$dest_dir"/*; do
    if [[ ! -L "$dest" ]]; then
      continue
    fi

    local target
    local name
    target="$(readlink "$dest")"
    name="$(basename "$dest")"

    if [[ "$target" == "$source_dir/"* && ! -e "$source_dir/$name" ]]; then
      rm -f "$dest"
      echo "✓  Removed stale Codex skill link: $dest"
    fi
  done

  for source in "$source_dir"/*; do
    if [[ ! -e "$source" ]]; then
      continue
    fi

    local name
    local dest
    name="$(basename "$source")"
    dest="$dest_dir/$name"

    create_symlink "$source" "$dest"
  done
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

echo "Installing agentic coding config..."
echo ""

for entry in "${SYMLINKS[@]}"; do
  source="${entry%%:*}"
  dest="${entry##*:}"
  create_symlink "$source" "$dest"
done

install_codex_config
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

echo ""
add_airc_to_zshrc

echo ""
echo "Done! Run 'source ~/.airc' or restart your shell to load AI aliases."
