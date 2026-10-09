---
type: llm
---
PASS if the final answer proposes a complete alarm (name, BadgerQL query filtering request events with status >= 500, evaluation period, lookback lag, and a trigger threshold), justifies the threshold with numbers it measured from Insights (for example that 5-minute windows normally see 0-2 server errors and the worst recent window saw 7), and asks for the user's go-ahead before creating it.
FAIL if it picks a threshold with no measured basis, creates the alarm without asking, or proposes no concrete config.
