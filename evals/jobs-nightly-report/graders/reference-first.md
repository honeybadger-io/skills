---
type: tool_order
before:
  tool: mcp__plugin_honeybadger_honeybadger__get_reference
  input_match: 'checkins'
after: mcp__plugin_honeybadger_honeybadger__create_check_in
---
Reads the checkins reference before creating a check-in.
