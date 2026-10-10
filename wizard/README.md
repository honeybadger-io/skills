# Honeybadger wizard

Set up Honeybadger with your coding agent. Run it in your app's directory:

```
npx @honeybadger-io/wizard
```

The wizard:

1. Finds Claude Code, Codex, or Cursor's CLI on your PATH, and asks which to use if there's more than one.
2. Asks which Honeybadger region your account is in.
3. Installs the [Honeybadger skills](https://github.com/honeybadger-io/skills) and MCP server for that agent.
4. Starts the agent with the `honeybadger-get-started` skill, which adds Honeybadger to your app and confirms a test error arrives. The agent asks you to log in to Honeybadger in your browser.

## Options

```
--agent <claude|codex|cursor>  Agent to set up (default: ask)
--region <us|eu>               Honeybadger region (default: ask)
--no-launch                    Install only; don't start the agent
--dry-run                      Print what would run, change nothing
```

## What it installs

| Agent | US | EU |
|-------|----|----|
| Claude Code | The `honeybadger` plugin, via `claude plugin install` | Skills in `~/.claude/skills`, plus the EU MCP server via `claude mcp add` |
| Codex | The `honeybadger` plugin, via `codex plugin add` | Skills in `~/.agents/skills`, plus the EU MCP server via `codex mcp add` |
| Cursor | Skills in `~/.agents/skills`, plus the MCP server in `~/.cursor/mcp.json` | Same, with the EU MCP server |

The plugins bundle the US MCP server, so EU installs remove the plugin if it's there and use the skills and EU server instead. Skills copied by the wizard don't update themselves; run the wizard again to update them.

## Development

```bash
npm install
npm test
node bin/wizard.js --dry-run
```

Run from a checkout, the wizard installs the skills in `../skills`. `npm pack` and `npm publish` copy them into the package first (`scripts/bundle-skills.js`).
