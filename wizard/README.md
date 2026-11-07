# Honeybadger wizard

Set up Honeybadger with your coding agent. Run it in your app's directory:

```
npx @honeybadger-io/wizard
```

The wizard:

1. Asks which Honeybadger region your account is in: US (app.honeybadger.io, the default) or EU (eu-app.honeybadger.io).
2. Checks that you're in an app directory and that you have no uncommitted changes, and asks before going on if not, so you can review the agent's changes on their own.
3. Asks which agents to set up: Claude Code, Codex, Cursor, OpenCode, Gemini CLI, GitHub Copilot CLI, Amp, Pi, or another agent. Agents with their CLI on your PATH start checked.
4. Shows what it will install and asks before going on.
5. Installs the [Honeybadger skills](https://github.com/honeybadger-io/skills) and the region's MCP server for each agent.
6. Offers to start an agent with the `honeybadger-get-started` skill, which adds Honeybadger to your app and confirms a test error arrives. The agent asks you to log in to Honeybadger in your browser. If you'd rather start it yourself, the wizard prints the prompt to use.

## Options

```
--agent <id>       Agent to set up; repeat for more than one (default: ask)
                   claude, codex, cursor, opencode, gemini, copilot, amp, pi, other
--region <us|eu>   Your Honeybadger account's region (default: ask; us with --yes)
--no-launch        Install only; don't start an agent
--dry-run          Print what would run, change nothing
-y, --yes          Don't ask anything: skip the checks for uncommitted changes
                   and an app directory and the install confirmation, set up
                   the --agent agents (default: every agent on your PATH), and
                   start the first one
```

With `--yes` in CI (when `CI` is set) or with no terminal, the wizard installs but doesn't start an agent. Pass `--region eu` for an EU account.

## What it installs

| Agent | Skills | MCP server |
|-------|--------|------------|
| Claude Code | The `honeybadger` plugin, via `claude plugin install` | Bundled with the plugin; the wizard sets its `mcp_url` option to the region's server |
| Everything else | Installed from GitHub by the [skills CLI](https://github.com/vercel-labs/skills) into `~/.agents/skills`, which they all read | [add-mcp](https://github.com/neondatabase/add-mcp) writes each agent's config; Amp uses `amp mcp add` |

Claude Code doesn't update the plugin automatically unless you turn on auto-update: run `/plugin`, open the **Marketplaces** tab, select `honeybadger`, and choose **Enable auto-update**. To update the skills for the other agents, run `npx skills update --global`, or run the wizard again.

The wizard runs the skills CLI with its telemetry turned off (`DISABLE_TELEMETRY=1`).

To switch regions, run the wizard again and pick the other one. If Claude Code is open, restart it afterward.

Codex also reads `~/.agents/skills`, so the wizard removes the Codex plugin if you have it, to keep the skills from loading twice.

The wizard doesn't start Amp; it prints the prompt to give it instead.

You can pick an agent whose CLI isn't on your PATH. It gets the skills and, where add-mcp can write it, the MCP config, and the wizard prints the prompt instead of starting it. Claude Code and Amp need their CLI to install, so the wizard prints the commands to run.

"Other agent" is for an agent the wizard doesn't list. It installs the skills to `~/.agents/skills`, which many agents read, and prints the MCP server's URL with an example config, since the wizard can't know where that agent keeps its MCP config or which format it uses. Check your agent's docs for both.

## Development

```bash
npm install
npm test
node bin/wizard.js --dry-run
```

The package doesn't include the skills; the wizard installs them from GitHub. To test unreleased skills or plugin changes, set `HONEYBADGER_WIZARD_MARKETPLACE` to a local checkout of this repo: the Claude Code marketplace and the skills CLI both install from it.
