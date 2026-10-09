# Honeybadger Skills

Skills and an MCP server that teach AI coding agents how to use [Honeybadger](https://www.honeybadger.io): find production errors, read the backtrace, find the root cause, and fix it.

Works with Claude Code, Codex, Cursor, and any agent that supports the [Agent Plugins](https://agent-plugins.org/) standard or [Agent Skills](https://agentskills.io/).

## Install

### Claude Code

```
/plugin marketplace add honeybadger-io/skills
/plugin install honeybadger@honeybadger
```

### Codex and Cursor

Add this repository as a plugin source in your agent. The manifests are in `.codex-plugin/` and `.cursor-plugin/`.

### Other agents

Copy the folders in `skills/` to wherever your agent loads skills from, and add the MCP server:

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

EU accounts use `https://eu-mcp.honeybadger.io/mcp`.

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
