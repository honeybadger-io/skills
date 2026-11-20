# Agent Instructions

## Project overview

Honeybadger skills for AI coding agents (Claude Code, Codex, and Cursor). The repo root is one plugin named `honeybadger`. It ships every skill in `skills/` plus the Honeybadger MCP server.

## Repository structure

```
skills/<name>/SKILL.md          # One skill per directory; name must match the directory
skills/<name>/references/       # Optional detail the agent loads only when needed
.claude-plugin/                 # Claude Code plugin + marketplace manifests, and the Claude directory README
.codex-plugin/plugin.json       # Codex plugin manifest
.cursor-plugin/                 # Cursor plugin + marketplace manifests
plugin.json, mcp.json           # Agent Plugins standard (agent-plugins.org) manifests
.mcp.json                       # MCP server config used by Codex and the Claude directory build (Claude Code's is in .claude-plugin/plugin.json, with a US/EU mcp_url option)
scripts/validate.py             # Lint for skills and manifests (runs in CI)
scripts/bump.py                 # Sets the version in all four versioned manifests
scripts/build_claude_directory.py  # Builds the claude-directory branch for Anthropic's plugin directory
evals/                          # claude plugin eval suite: mock Honeybadger server + fixture app
wizard/                         # npx @honeybadger-io/wizard: installs the skills + MCP server, offers to start the agent
```

## Writing skills

- Every skill name starts with `honeybadger-` (for example `honeybadger-debug-errors`). Codex, Cursor, and plain skill folders have no plugin namespace, so the prefix keeps our skills apart from other vendors'.
- Each skill is one task a user would ask for ("debug this error", "add Honeybadger to my app"). Do not make one skill per SDK or language; put per-SDK detail in `references/`.
- Frontmatter is `name` and `description` only. The description says what the skill does and when to use it, because agents pick skills from the description alone.
- Skills hold only Markdown, text, JSON, YAML and images. No scripts or other executables: Anthropic's plugin directory refuses them from organizations it hasn't verified.
- Keep `SKILL.md` short. Move long detail into `references/` and link to it from `SKILL.md`.
- Do not copy the docs. Link to https://docs.honeybadger.io, and use the MCP server's `get_reference` tool for BadgerQL, dashboards, alarms, and check-ins.
- Use the MCP tools for live data. Name the exact tool (for example `list_faults`, `get_fault`).
- Remember EU accounts. Anything that uses a hostname must also work for the EU region (`eu-app.honeybadger.io`, `eu-mcp.honeybadger.io`).

## Versioning

The version lives in four manifests: `plugin.json`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, and `.cursor-plugin/plugin.json`. Bump them together with `python3 scripts/bump.py X.Y.Z`; `scripts/validate.py` fails if they differ.

## Releasing

Anthropic's plugin directory tracks the `claude-directory` branch, which holds only the files the directory accepts. Don't edit it; `.github/workflows/claude-directory.yml` rebuilds it with `scripts/build_claude_directory.py`.

To release:

1. Merge a PR that bumps the version in all four manifests.
2. Tag that commit and push the tag: `git tag vX.Y.Z && git push origin vX.Y.Z`. `v*` tags are for plugin releases only.
3. The workflow fails unless the tag matches the manifests, then commits the new build to `claude-directory`. The directory scans it, and a reviewer publishes it.

To see what the directory gets, run `python3 scripts/build_claude_directory.py <empty-dir>`.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`,
`docs:`, `chore:`, `refactor:`, `test:`. Scope is optional and is usually the skill name
(`fix(get-started): ...`). Imperative subject, no trailing period.

## Wizard

`wizard/` is the npm package `@honeybadger-io/wizard`. It publishes a copy of `skills/`, so a skill change reaches wizard users only after a new wizard release. When you rename a skill, the plugin, or the marketplace, update `wizard/src/agents.js` to match. The wizard doesn't remove a renamed skill's old folder from users' machines, so a rename needs a plan for that. Run `npm test` in `wizard/` after changing it.

## Checks

Run before committing:

```bash
python3 scripts/validate.py
claude plugin validate .
```

When you change a skill, run its evals (see `evals/README.md`) and add a case for any new behavior.
