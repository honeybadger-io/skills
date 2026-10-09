---
type: tool_used
tool: mcp__plugin_honeybadger_honeybadger__create_check_in
input_match: '"cron_timezone"\s*:\s*"Eastern Time \(US & Canada\)"'
min: 1
---
Passes the crontab's CRON_TZ as the Rails zone name, not the IANA identifier (which the API rejects).
