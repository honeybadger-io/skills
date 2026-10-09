---
type: llm
---
PASS if the final answer says no existing Honeybadger project fits this app (the only one is "Marketing Site"), proposes a name for a new project (such as "Shop"), and asks the user to confirm before creating it.
FAIL if it says it already created a project, picks "Marketing Site" without asking, or does not mention choosing or creating a project.
