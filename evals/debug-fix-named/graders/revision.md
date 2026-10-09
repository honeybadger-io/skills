---
type: llm
---
PASS if the final answer names the revision that raised the error (71983319, or the full SHA starting with it) and says whether it matches the local HEAD (it does).
FAIL if the answer does not mention the deployed revision at all, or claims it differs from HEAD.
