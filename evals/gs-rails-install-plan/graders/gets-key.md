---
type: regex
pattern: 'honeybadger\s+install\s+["'']?hbp_fixture_key(["''`\s]|$)'
match: contains
target: last_message
---
Passes the Shop project's real API key, from the MCP, to the gem's install command, as the docs show.
