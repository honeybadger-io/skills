---
type: tool_used
tool: mcp__plugin_honeybadger_honeybadger__create_dashboard
input_match: 'bin\(\s*\d'
min: 0
max: 0
---
No time series uses a fixed bucket like bin(1h): bare bin() sizes buckets to the range the viewer picks, so the charts stay readable when it changes.
