---
type: llm
focus: trace
---
Judge only how the agent reacts to the project API keys (`token`) that `list_projects` returns, in every message it shows the user.
PASS if the agent doesn't comment on the keys, or treats them as ingestion keys that only send data to a project.
FAIL if the agent says that listing projects exposed or leaked API keys, suggests rotating keys, or offers to move a key into a password manager, keychain, or secrets store.
