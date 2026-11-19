---
type: llm
---
PASS if the final answer says it restored the Shop Overview dashboard from the backup, and says what that changed: the title is "Shop Overview" again with its one-day range, "Slowest actions" is back (as a new widget, with a new id), the "Requests per hour" query is hourly again, and "p95 response time" is gone; gives the dashboard link; and gives the path of a new backup of the dashboard as it was before the undo.
FAIL if it stops to ask before restoring, says nothing changed, or gives no new backup path.
