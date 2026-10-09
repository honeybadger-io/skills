---
type: llm
---
PASS if the final answer says the open faults are intentional smoke tests (synthetic errors sent on purpose to check error reporting), proposes no code change to make them stop, and does not recommend ignoring them unless it also says that ignoring discards their future occurrences. Pointing out an unrelated bug it noticed in the code is fine.
FAIL if it proposes a code change to fix the smoke-test faults, treats them as real bugs, or recommends ignoring them without that warning.
