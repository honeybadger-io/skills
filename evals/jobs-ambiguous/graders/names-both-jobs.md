---
type: llm
---
PASS if the answer names both scheduled jobs it found (the nightly `reports:nightly` rake task and the 15-minute `Order.sweep_abandoned_carts` runner) and asks the user which one to monitor, or offers to monitor both and asks for confirmation.

FAIL if it picks one job and proceeds without asking, or if it names only one of the two jobs.
