#!/bin/bash
set -euo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
SKILLS_DIR="$ROOT/.claude/skills"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Cloud sessions don't install plugins, so every session fetches the Orchestra skills instead.
if git clone --depth 1 -q https://github.com/orchestra-hq/orchestra-skills.git "$TMP/src"; then
  PLUGIN="$TMP/src/skills/orchestra"
  mkdir -p "$SKILLS_DIR"
  cp -R "$PLUGIN/skills/." "$SKILLS_DIR/"
  # Skills link to ../references/..., which resolves to .claude/skills/references.
  cp -R "$PLUGIN/references" "$SKILLS_DIR/references"
  echo "orchestra skills ready"
else
  echo "orchestra skills: clone failed"
fi

# Cloud only: the VM has no venv, so build it from pyproject.toml (CLI + oml validator).
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
  python3 -m venv "$ROOT/.venv"
  "$ROOT/.venv/bin/pip" install -q "$ROOT"
  echo "venv ready: use .venv/bin/orchestra and .venv/bin/python"
fi
