#!/usr/bin/env python3
"""Build the plugin that Anthropic's directory reads from the claude-directory branch.

usage: python3 scripts/build_claude_directory.py OUT_DIR [--version X.Y.Z]

The directory accepts only Markdown, text, JSON, YAML and images from organizations
it hasn't verified, and only a fixed MCP server URL. So the build holds the tracked
files in skills/, the license, the icon, the directory README, and a plugin.json
whose MCP servers come from .mcp.json instead of the US/EU mcp_url option.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

parser = argparse.ArgumentParser()
parser.add_argument("out", type=Path, help="empty or missing directory to build into")
parser.add_argument("--version", help="fail unless .claude-plugin/plugin.json has this version")
args = parser.parse_args()

out = args.out.resolve()
if out.exists() and any(out.iterdir()):
    sys.exit(f"{out} is not empty")

manifest = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
if args.version and manifest.get("version") != args.version:
    sys.exit(f".claude-plugin/plugin.json has version {manifest.get('version')}, expected {args.version}")

# Tracked files only, so local clutter such as .DS_Store never ships.
tracked = subprocess.run(
    ["git", "ls-files", "-z", "skills"], cwd=ROOT, capture_output=True, text=True, check=True
).stdout.split("\0")
copies = {path: path for path in tracked if path}
copies["LICENSE"] = "LICENSE"
copies[".claude-plugin/icon.png"] = ".claude-plugin/icon.png"
copies[".claude-plugin/directory-README.md"] = "README.md"

for source, dest in copies.items():
    (out / dest).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / source, out / dest)

manifest.pop("userConfig", None)
manifest["mcpServers"] = json.loads((ROOT / ".mcp.json").read_text())["mcpServers"]
(out / ".claude-plugin/plugin.json").write_text(json.dumps(manifest, indent=2) + "\n")

print(f"built {manifest['name']} {manifest['version']} in {out}")
