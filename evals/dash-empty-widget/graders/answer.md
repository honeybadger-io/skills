---
type: llm
---
PASS if the final answer says the widget's query reads Honeybadger's notice events, which live on the internal stream, while the widget's streams setting is ["default"], so it reads none of them, and proposes changing streams to include "internal" (asking or offering before saving).
FAIL if it blames the query syntax or a lack of data without mentioning the stream, changes the dashboard without asking, or proposes no fix.
