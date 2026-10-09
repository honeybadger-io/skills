---
type: tool_used
tool: mcp__plugin_honeybadger_honeybadger__create_alarm
input_match: '"evaluation_period":\s*"(1d|24h)"'
min: 1
---
Evaluation period is exactly one day: one run per window, so a missed run always leaves an empty window.
