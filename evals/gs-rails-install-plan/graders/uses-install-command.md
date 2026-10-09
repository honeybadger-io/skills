---
type: regex
pattern: 'honeybadger install'
match: contains
target: last_message
---
The plan names the gem's install command, which is the one step that sends the test error.
