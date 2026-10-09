---
type: tool_used
tool: mcp__plugin_honeybadger_honeybadger__create_alarm
input_match: 'event_type::str\s*==\s*\\"process_action.action_controller\\"[^"]*status::int\s*==\s*500'
min: 1
---
The alarm query scopes to request events with status exactly 500, as the user asked.
