#!/usr/bin/env bash
# Package all Claude Desktop skills into ZIP files for upload.
# Each skill directory under skills/ becomes a ZIP with SKILL.md at root.
#
# Usage: ./package-skills.sh
# Output: zips/<skill-name>.zip for each skill

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/skills"
OUTPUT_DIR="$SCRIPT_DIR/zips"

mkdir -p "$OUTPUT_DIR"

if [ ! -d "$SKILLS_DIR" ]; then
  echo "No skills directory found at $SKILLS_DIR"
  exit 1
fi

count=0
for skill_dir in "$SKILLS_DIR"/*/; do
  [ -d "$skill_dir" ] || continue

  skill_name="$(basename "$skill_dir")"
  skill_file="$skill_dir/SKILL.md"

  if [ ! -f "$skill_file" ]; then
    echo "SKIP: $skill_name (no SKILL.md found)"
    continue
  fi

  output_zip="$OUTPUT_DIR/$skill_name.zip"

  # ZIP from inside the skill directory so SKILL.md is at root
  (cd "$skill_dir" && zip -r "$output_zip" . -x '.*')

  echo "OK:   $skill_name -> zips/$skill_name.zip"
  count=$((count + 1))
done

if [ "$count" -eq 0 ]; then
  echo "No skills found to package."
else
  echo ""
  echo "Packaged $count skill(s) into $OUTPUT_DIR/"
fi
