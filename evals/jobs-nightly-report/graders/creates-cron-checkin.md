---
type: tool_used
tool: mcp__plugin_honeybadger_honeybadger__create_check_in
input_match: '^(?=[\s\S]*"project_id"\s*:\s*1001)(?=[\s\S]*"schedule_type"\s*:\s*"cron")(?=[\s\S]*"cron_schedule"\s*:\s*"30 2 \* \* \*")'
min: 1
max: 1
---
Creates exactly one cron check-in, in the Shop project, with a schedule that matches "2:30 am" daily.
