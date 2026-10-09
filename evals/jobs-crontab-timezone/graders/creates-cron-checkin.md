---
type: tool_used
tool: mcp__plugin_honeybadger_honeybadger__create_check_in
input_match: '^(?=[\s\S]*"project_id"\s*:\s*1002)(?=[\s\S]*"schedule_type"\s*:\s*"cron")(?=[\s\S]*"cron_schedule"\s*:\s*"0 \*/6 \* \* \*")'
min: 1
max: 1
---
Creates exactly one cron check-in, in the Marketing Site project, with the crontab's schedule.
