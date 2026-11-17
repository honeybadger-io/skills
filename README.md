# Honeybadger Skills

Skills and an MCP server that teach AI coding agents how to use [Honeybadger](https://www.honeybadger.io): find production errors, read the backtrace, find the root cause, and fix it.

Works with Claude Code, Codex, GitHub Copilot CLI, Cursor, and any agent that supports the [Agent Plugins](https://agent-plugins.org/) standard or [Agent Skills](https://agentskills.io/).

## Install

### Wizard

Run this in your app's directory:

```
npx @honeybadger-io/wizard
```

It installs the skills and MCP server for the coding agents it finds (Claude Code, Codex, Cursor, OpenCode, Gemini CLI, GitHub Copilot CLI, Amp, and Pi), then offers to start one to add Honeybadger to the app. See [wizard/](wizard/) for what it changes. It asks for your Honeybadger region, US or EU.

If you used the wizard, don't also install the Codex, Copilot, or Pi packages below: those agents already load the skills from `~/.agents/skills`, and the packages would load them twice. Pi still needs an MCP extension; see [Pi](#pi).

### Claude Code

```
/plugin marketplace add honeybadger-io/skills
/plugin install honeybadger@honeybadger
```

The plugin asks which MCP server to use: `https://mcp.honeybadger.io/mcp` for US accounts (the default) or `https://eu-mcp.honeybadger.io/mcp` for EU accounts. To change it later, run `/plugin`, open the **Installed** tab, select `honeybadger`, and choose **Configure options**. From your shell:

```
claude plugin install honeybadger@honeybadger --config mcp_url=https://eu-mcp.honeybadger.io/mcp
```

### Codex

```
codex plugin marketplace add honeybadger-io/skills
codex plugin add honeybadger@honeybadger
```

The plugin uses the US MCP server. For an EU account, replace it with the EU server:

```
codex mcp add honeybadger --url https://eu-mcp.honeybadger.io/mcp
```

### GitHub Copilot CLI

```
copilot plugin marketplace add honeybadger-io/skills
copilot plugin install honeybadger@honeybadger
```

The plugin uses the US MCP server. For an EU account, add the EU server under its own name and turn off the plugin's server, which Copilot otherwise keeps running beside it:

```
copilot mcp add --transport http honeybadger-eu https://eu-mcp.honeybadger.io/mcp
copilot mcp disable honeybadger
```

### Pi

```
pi install https://github.com/honeybadger-io/skills
```

This installs the skills. Pi has no built-in MCP support, so to give it the MCP server, install an MCP extension such as [pi-mcp-adapter](https://github.com/nicobailon/pi-mcp-adapter) and add `https://mcp.honeybadger.io/mcp` (EU: `https://eu-mcp.honeybadger.io/mcp`) as its README describes.

### Cursor, OpenCode, and other agents

Copy the skills to `~/.agents/skills`, which Cursor, OpenCode, and most other agents read:

```
git clone --depth 1 https://github.com/honeybadger-io/skills.git honeybadger-skills
mkdir -p ~/.agents/skills
cp -R honeybadger-skills/skills/honeybadger-* ~/.agents/skills/
```

To update, run `git -C honeybadger-skills pull` and the `cp` command again from the same directory. Then add the MCP server. EU accounts use `https://eu-mcp.honeybadger.io/mcp` in place of the US URL below.

**Cursor:** add the server to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "honeybadger": {
      "url": "https://mcp.honeybadger.io/mcp"
    }
  }
}
```

**OpenCode:**

```
opencode mcp add honeybadger --url https://mcp.honeybadger.io/mcp --global
```

**Other agents:** if your agent doesn't read `~/.agents/skills`, copy the skills to wherever it loads them from. Most agents take an MCP config in this shape; check your agent's docs for where it goes:

```json
{
  "mcpServers": {
    "honeybadger": {
      "type": "http",
      "url": "https://mcp.honeybadger.io/mcp"
    }
  }
}
```

### Troubleshooting

If you also added Honeybadger as a connector on claude.ai, Claude Code uses that connector instead of the plugin's MCP server, because both point at the same URL. If the Honeybadger tools are missing, run `/mcp` and log in to the claude.ai Honeybadger connector, or remove that connector.

## Skills

| Skill | What it does | Try asking |
|-------|--------------|------------|
| [honeybadger-get-started](skills/honeybadger-get-started/SKILL.md) | Add Honeybadger to an app and confirm a real error arrives, or find the next step for an existing setup | "Add Honeybadger to this app" |
| [honeybadger-debug-errors](skills/honeybadger-debug-errors/SKILL.md) | Find a fault, read the backtrace, find the root cause, and fix it | "Fix the most recent Honeybadger error" |
| [honeybadger-monitor-jobs](skills/honeybadger-monitor-jobs/SKILL.md) | Create a check-in for a cron job or scheduled task and wire the report into the job | "Add a Honeybadger check-in to the nightly backup job" |
| [honeybadger-alarms](skills/honeybadger-alarms/SKILL.md) | Create, tune, or explain an Insights alarm, with the threshold measured from real data | "Alert us when 500s spike in production" |
| [honeybadger-investigate](skills/honeybadger-investigate/SKILL.md) | Investigate a support ticket, slowdown, or incident with Insights events, faults, and deploys | "A customer says checkout failed yesterday, what happened?" |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md).

## License

[MIT](LICENSE)
