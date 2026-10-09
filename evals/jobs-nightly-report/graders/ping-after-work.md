---
type: llm
---
Judge only the code change and the follow-up instructions.

PASS if both are true:
1. The check-in report (`Honeybadger.check_in`) is placed after the report is built and mailed, so a failed run does not report.
2. The answer tells the user the check-in will not alert until the job has reported once (it is pending until the first report), or tells them to deploy and let the job run, then confirm it reports.

FAIL if the report is sent before the work, or if the answer says monitoring is already active.
