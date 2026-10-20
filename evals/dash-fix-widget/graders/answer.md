---
type: llm
---
PASS if the final answer says the widget reads Honeybadger's notice events, which live on the internal stream, while the widget read only the default stream; says it changed the widget to read the internal stream and saved the dashboard; gives the dashboard link from the update response; and gives the backup file path and says the change can be undone.
FAIL if it stops to ask before saving, blames something other than the stream, or gives no backup path.
