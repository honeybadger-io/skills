#!/usr/bin/env python3
"""Check skills and plugin manifests. Run from anywhere: python3 scripts/validate.py"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$")
MANIFESTS = [
    "plugin.json",
    "mcp.json",
    ".mcp.json",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".codex-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    ".cursor-plugin/marketplace.json",
]
VERSIONED = ["plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".cursor-plugin/plugin.json"]

errors = []


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        return None
    closing = re.search(r"\n---(?=\n|$)", text[3:])
    if closing is None:
        return None
    lines = text[4 : 3 + closing.start()].splitlines()
    fields = {}
    key = None
    for line in lines:
        if line.startswith((" ", "\t")) or not line.strip():
            # Continuation of a block scalar (|, >) or a wrapped plain value
            if key is not None and line.strip():
                fields[key] = (fields[key] + " " + line.strip()).strip()
            continue
        key, sep, value = line.partition(":")
        if not sep:
            key = None
            continue
        key = key.strip()
        value = value.strip()
        fields[key] = "" if re.fullmatch(r"[|>][+-]?", value) else value.strip("\"'")
    return fields

for skill_md in sorted(ROOT.glob("skills/*/SKILL.md")):
    rel = skill_md.relative_to(ROOT)
    fields = parse_frontmatter(skill_md.read_text())
    if fields is None:
        errors.append(f"{rel}: missing YAML frontmatter")
        continue
    name = fields.get("name", "")
    description = fields.get("description", "")
    if name != skill_md.parent.name:
        errors.append(f"{rel}: name '{name}' does not match directory '{skill_md.parent.name}'")
    if not NAME_RE.match(name) or len(name) > 64:
        errors.append(f"{rel}: name must be kebab-case, 64 chars max")
    if not name.startswith("honeybadger-"):
        errors.append(f"{rel}: name must start with 'honeybadger-'")
    if not description:
        errors.append(f"{rel}: description is required")
    elif len(description) > 1024:
        errors.append(f"{rel}: description is {len(description)} chars, 1024 max")

for skill_dir in sorted(p for p in ROOT.glob("skills/*") if p.is_dir()):
    if not (skill_dir / "SKILL.md").exists():
        errors.append(f"{skill_dir.relative_to(ROOT)}: missing SKILL.md")

versions = {}
for path in MANIFESTS:
    try:
        data = json.loads((ROOT / path).read_text())
    except FileNotFoundError:
        errors.append(f"{path}: missing")
        continue
    except json.JSONDecodeError as e:
        errors.append(f"{path}: invalid JSON ({e})")
        continue
    if not isinstance(data, dict):
        errors.append(f"{path}: top-level JSON value must be an object")
        continue
    if path in VERSIONED:
        version = data.get("version")
        if not isinstance(version, str) or not VERSION_RE.match(version):
            errors.append(f"{path}: version must be semver (got {version!r})")
        versions[path] = version

if len(set(versions.values())) > 1:
    errors.append("manifest versions differ: " + ", ".join(f"{p}={v}" for p, v in versions.items()))

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"ok: {len(list(ROOT.glob('skills/*/SKILL.md')))} skills, {len(MANIFESTS)} manifests")
