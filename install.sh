#!/bin/bash
# Install script for agentic coding config
# Symlinks config files to their correct locations

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Define symlinks: "source:destination"
SYMLINKS=(
  # Claude
  "$SCRIPT_DIR/claude/commands:$HOME/.claude/commands"
  "$SCRIPT_DIR/claude/hooks:$HOME/.claude/hooks"
  "$SCRIPT_DIR/claude/settings.json:$HOME/.claude/settings.json"
  # Codex
  "$SCRIPT_DIR/codex/config.toml:$HOME/.codex/config.toml"
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

echo ""
add_airc_to_zshrc

echo ""
echo "Done! Run 'source ~/.airc' or restart your shell to load AI aliases."
