---
type: llm
---
PASS if the final answer explains why the alarm is noisy using numbers (threshold of 2 per 5 minutes against a normal rate of about 5 requests over 400 ms per 5 minutes, up to 19), proposes a specific new configuration (a higher threshold, a stricter duration, or a longer evaluation period, with the numbers it would produce), and asks for the user's go-ahead before changing the alarm.
FAIL if it changes the alarm without asking, proposes a new threshold without measured data, or only describes the problem.
