#!/bin/bash
set -euo pipefail

# Cloud sessions don't install plugins, so every session fetches the Orchestra skills instead.
SKILLS_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/skills"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

if git clone --depth 1 -q https://github.com/orchestra-hq/orchestra-skills.git "$TMP/src"; then
  mkdir -p "$SKILLS_DIR"
  PLUGIN="$TMP/src/skills/orchestra"
  cp -R "$PLUGIN/skills/." "$SKILLS_DIR/"
  # Skills link to ../references/..., which resolves to .claude/skills/references.
  cp -R "$PLUGIN/references" "$SKILLS_DIR/references"
  echo "orchestra skills ready"
else
  echo "orchestra skills: clone failed"
fi
