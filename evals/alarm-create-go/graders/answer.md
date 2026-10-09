---
type: llm
---
PASS if the final answer reports the created alarm with its link (app.honeybadger.io/projects/1001/insights/alarms/...), states the trigger (more than 10 in 5 minutes), and tells the user that alarm notifications go through the project's integrations. If it names the Slack #shop-alerts channel, it must also say that the integration's alarm notification setting must be checked in the Honeybadger UI.
FAIL if it says nothing about where notifications go, reports a different trigger, or names a specific channel without stating that its alarm notification setting must be checked in the Honeybadger UI.
