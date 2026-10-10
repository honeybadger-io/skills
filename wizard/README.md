# Honeybadger wizard

Set up Honeybadger with your coding agent. Run it in your app's directory:

```
npx @honeybadger-io/wizard
```

The wizard is for US Honeybadger accounts (app.honeybadger.io). For an EU account, set up your agent by hand: see [Install](https://github.com/honeybadger-io/skills#install).

The wizard:

1. Checks that you're in an app directory and that you have no uncommitted changes, and asks before going on if not, so you can review the agent's changes on their own.
2. Asks which agents to set up: Claude Code, Codex, Cursor, OpenCode, Gemini CLI, GitHub Copilot CLI, Amp, or Pi. Agents with their CLI on your PATH start checked.
3. Shows what it will install, including any Honeybadger skills it will overwrite, and asks before going on.
4. Installs the [Honeybadger skills](https://github.com/honeybadger-io/skills) and MCP server for each agent.
5. Offers to start an agent with the `honeybadger-get-started` skill, which adds Honeybadger to your app and confirms a test error arrives. The agent asks you to log in to Honeybadger in your browser. If you'd rather start it yourself, the wizard prints the prompt to use.

## Options

```
--agent <id>       Agent to set up; repeat for more than one (default: ask)
                   claude, codex, cursor, opencode, gemini, copilot, amp, pi
--no-launch        Install only; don't start an agent
--dry-run          Print what would run, change nothing
-y, --yes          Don't ask anything: skip the checks for uncommitted changes
                   and an app directory and the install confirmation, set up
                   the --agent agents (default: every agent on your PATH), and
                   start the first one
```

With `--yes` and no terminal, as in CI, the wizard installs but doesn't start an agent.

## What it installs

| Agent | Skills | MCP server |
|-------|--------|------------|
| Claude Code | The `honeybadger` plugin, via `claude plugin install` | Bundled with the plugin |
| Everything else | Copied to `~/.agents/skills`, which they all read | [add-mcp](https://github.com/neondatabase/add-mcp) writes each agent's config; Amp uses `amp mcp add` |

Claude Code doesn't update the plugin automatically unless you turn on auto-update: run `/plugin`, open the **Marketplaces** tab, select `honeybadger`, and choose **Enable auto-update**. Copied skills don't update themselves either; run the wizard again to update them.

Codex also reads `~/.agents/skills`, so the wizard removes the Codex plugin if you have it, to keep the skills from loading twice.

The wizard doesn't start Amp; it prints the prompt to give it instead.

You can pick an agent whose CLI isn't on your PATH. It gets the skills and MCP config files, and the wizard prints the prompt instead of starting it. Claude Code and Amp need their CLI to install, so the wizard prints the commands to run.

## Development

```bash
npm install
npm test
node bin/wizard.js --dry-run
```

Run from a checkout, the wizard installs the skills in `../skills`. `npm pack` and `npm publish` copy them into the package and remove the copy afterward (`scripts/bundle-skills.js`).
