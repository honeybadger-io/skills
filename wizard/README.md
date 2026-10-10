# Honeybadger wizard

Set up Honeybadger with your coding agent. Run it in your app's directory:

```
npx @honeybadger-io/wizard
```

The wizard:

1. Checks for uncommitted changes and asks before going on, so you can review the agent's changes on their own.
2. Asks which agents to set up: Claude Code, Codex, Cursor, OpenCode, Gemini CLI, GitHub Copilot CLI, Amp, or Pi. Agents with their CLI on your PATH start checked.
3. Asks which Honeybadger region your account is in.
4. Installs the [Honeybadger skills](https://github.com/honeybadger-io/skills) and MCP server for each agent.
5. Offers to start an agent with the `honeybadger-get-started` skill, which adds Honeybadger to your app and confirms a test error arrives. The agent asks you to log in to Honeybadger in your browser. If you'd rather start it yourself, the wizard prints the prompt to use.

## Options

```
--agent <id>       Agent to set up; repeat for more than one (default: ask)
                   claude, codex, cursor, opencode, gemini, copilot, amp, pi
--region <us|eu>   Honeybadger region (default: ask)
--no-launch        Install only; don't start an agent
--dry-run          Print what would run, change nothing
-y, --yes          Don't ask: set up every agent on your PATH and start the first
```

## What it installs

| Agent | Skills | MCP server |
|-------|--------|------------|
| Claude Code, US | The `honeybadger` plugin, via `claude plugin install` | Bundled with the plugin |
| Claude Code, EU | Copied to `~/.claude/skills` | `claude mcp add` |
| Everything else | Copied to `~/.agents/skills`, which they all read | [add-mcp](https://github.com/neondatabase/add-mcp) writes each agent's config; Amp uses `amp mcp add` |

The Claude Code plugin bundles the US MCP server, so EU installs remove it and use the copied skills and EU server instead. Codex also reads `~/.agents/skills`, so the wizard removes the Codex plugin if you have it, to keep the skills from loading twice. Copied skills don't update themselves; run the wizard again to update them.

Pi has no built-in MCP support. To use the MCP server there, install [pi-mcp-adapter](https://github.com/nicobailon/pi-mcp-adapter): `pi install npm:pi-mcp-adapter`.

Amp can't start with a prompt, so for Amp the wizard prints the prompt to paste.

You can pick an agent whose CLI isn't on your PATH. It gets the skills and MCP config files, and the wizard prints the prompt instead of starting it. Claude Code without its CLI gets copied skills instead of the plugin, and Amp without its CLI gets the `amp mcp add` command to run.

## Development

```bash
npm install
npm test
node bin/wizard.js --dry-run
```

Run from a checkout, the wizard installs the skills in `../skills`. `npm pack` and `npm publish` copy them into the package first (`scripts/bundle-skills.js`).
