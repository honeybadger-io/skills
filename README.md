# Honeybadger

Skills that teach Claude how to use [Honeybadger](https://www.honeybadger.io): find production errors, read the backtrace, find the root cause, and fix it; investigate incidents from logs; create alarms; and monitor cron jobs.

The plugin uses the Honeybadger connector for live account access. When you connect it, choose the region your Honeybadger account is hosted in, US or EU.

## Skills

| Skill | What it does | Try asking |
|-------|--------------|------------|
| [honeybadger-get-started](skills/honeybadger-get-started/SKILL.md) | Add Honeybadger to an app and confirm a real error arrives, or find the next step for an existing setup | "Add Honeybadger to this app" |
| [honeybadger-debug-errors](skills/honeybadger-debug-errors/SKILL.md) | Find a fault, read the backtrace, find the root cause, and fix it | "Fix the most recent Honeybadger error" |
| [honeybadger-monitor-jobs](skills/honeybadger-monitor-jobs/SKILL.md) | Create a check-in for a cron job or scheduled task and wire the report into the job | "Add a Honeybadger check-in to the nightly backup job" |
| [honeybadger-alarms](skills/honeybadger-alarms/SKILL.md) | Create, tune, or explain an Insights alarm, with the threshold measured from real data | "Alert us when 500s spike in production" |
| [honeybadger-investigate](skills/honeybadger-investigate/SKILL.md) | Investigate a support ticket, slowdown, or incident with Insights events, faults, and deploys | "A customer says checkout failed yesterday, what happened?" |

## Claude Code

In Claude Code, the plugin's MCP server points at the US endpoint, `https://mcp.honeybadger.io/mcp`. If your account is in the EU, connect the Honeybadger connector with the EU region on claude.ai, or add `https://eu-mcp.honeybadger.io/mcp` yourself; you can ignore the plugin's `honeybadger` server.

## About this branch

This branch is generated from [`main`](https://github.com/honeybadger-io/skills) for Anthropic's plugin directory and holds only the files the directory accepts. Don't edit it; send changes to `main`. Documentation: https://docs.honeybadger.io/resources/mcp/

## License

[MIT](LICENSE)
