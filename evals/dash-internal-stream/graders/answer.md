---
type: llm
---
PASS if the final answer reports the dashboard link returned by the update (app.honeybadger.io/projects/1001/insights/dashboards/...), says the "Errors over time" widget was added with a notice-per-hour query that reads the internal stream, and says the existing widgets were kept.
FAIL if it says it did not save, reports a different link, or says an existing widget was removed.
