---
type: tool_order
before: mcp__plugin_honeybadger_honeybadger__list_projects
after:
  tool: mcp__plugin_honeybadger_honeybadger__get_fault
  input_match: '"fault_id":\s*5001'
---
Finds the project before it reads the fault.
