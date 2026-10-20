---
type: llm
---
PASS if the final answer says it added one widget for p95 response time (a BadgerQL query using percentile(95, duration) over request events), placed below the existing widgets, says the existing widgets are unchanged, gives the dashboard link from the update response, and gives the backup file path and says the change can be undone.
FAIL if it stops to ask before saving, says it dropped, renamed, or re-created an existing widget, or gives no backup path.
