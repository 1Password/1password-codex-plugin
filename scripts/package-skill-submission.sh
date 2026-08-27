#!/usr/bin/env bash
#
# Builds a ZIP for an OpenAI "Skills Only" plugin submission.
#
# Skills-only bundles must exclude mcpServers, .mcp.json, apps, .app.json, and
# interface.screenshots, but this repo keeps .mcp.json so the plugin still works
# as a local/GitHub install. So we stage a copy, strip the disallowed pieces
# there, and zip that -- the working tree is never modified.
#
# Usage: scripts/package-skill-submission.sh [plugin-name]

set -euo pipefail

PLUGIN="${1:-1password}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/plugins/$PLUGIN"
DIST="$REPO_ROOT/dist"
ZIP="$DIST/$PLUGIN-skill-submission.zip"

[ -d "$SRC" ] || { echo "error: no plugin at $SRC" >&2; exit 1; }

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

# Copy, then drop the MCP config and macOS cruft.
cp -R "$SRC" "$STAGE/$PLUGIN"
rm -f "$STAGE/$PLUGIN/.mcp.json" "$STAGE/$PLUGIN/.app.json"
find "$STAGE" \( -name '.DS_Store' -o -name '__MACOSX' \) -exec rm -rf {} + 2>/dev/null || true

# Strip the keys a skills-only bundle may not declare.
python3 - "$STAGE/$PLUGIN/.codex-plugin/plugin.json" <<'PY'
import json, sys

path = sys.argv[1]
with open(path) as f:
    manifest = json.load(f)

for key in ("mcpServers", "apps"):
    manifest.pop(key, None)
manifest.get("interface", {}).pop("screenshots", None)

with open(path, "w") as f:
    json.dump(manifest, f, indent=2)
    f.write("\n")
PY

mkdir -p "$DIST"
rm -f "$ZIP"
# Zip from the staging dir so the archive has exactly one top-level directory.
(cd "$STAGE" && zip -r -X "$ZIP" "$PLUGIN" -x '*.DS_Store' > /dev/null)

python3 "$REPO_ROOT/scripts/validate_submission_zip.py" "$ZIP"
echo
echo "Built $ZIP"
