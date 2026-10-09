---
type: tool_used
tool: mcp__plugin_honeybadger_honeybadger__create_alarm
input_match: '"lookback_lag":\s*"([1-9]\d*[mh])"'
min: 1
---
Lookback lag is at least one minute: with an `eq 0` trigger, a late event would otherwise leave the window empty and fire a false alarm.
