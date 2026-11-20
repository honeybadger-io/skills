#!/usr/bin/env python3
"""Set the plugin version in every manifest. usage: python3 scripts/bump.py X.Y.Z"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Same pattern and manifest list as validate.py, which checks the result.
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$")
VERSIONED = ["plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".cursor-plugin/plugin.json"]

if len(sys.argv) != 2:
    sys.exit("usage: python3 scripts/bump.py X.Y.Z")
new = sys.argv[1]
if not VERSION_RE.match(new):
    sys.exit(f"not a semver version: {new!r}")

for path in VERSIONED:
    file = ROOT / path
    text = file.read_text()
    old = json.loads(text)["version"]
    # Replace the line in place rather than re-dumping the JSON, so each file keeps its formatting.
    text, count = re.subn(rf'"version": "{re.escape(old)}"', f'"version": "{new}"', text)
    if count != 1:
        sys.exit(f"{path}: expected one \"version\": \"{old}\", found {count}")
    file.write_text(text)
    print(f"{path}: {old} -> {new}")

sys.stdout.flush()  # keep this script's lines ahead of validate.py's when piped
sys.exit(subprocess.run([sys.executable, str(ROOT / "scripts/validate.py")]).returncode)
