---
type: llm
---
PASS if the final answer reports the created alarm with its link, explains that it evaluates once per day and fires when no export.nightly event arrived in that window, and warns about the trade-off (a missed run is noticed up to a day later, or a shorter period would fire every window the job isn't due).
FAIL if the alarm would fire on every window in which the job is not due, or the answer does not explain when the user will hear about a missed run.
