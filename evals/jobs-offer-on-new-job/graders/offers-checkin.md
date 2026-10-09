---
type: llm
---
PASS if the answer does the job the user asked for (the rake task and its schedule) AND, in a sentence or two, offers to add a Honeybadger check-in for the new job and waits for the user to say yes.

FAIL if it never mentions a check-in or monitoring for the new job, if it says it already created a check-in, or if it turns the answer into a monitoring walkthrough instead of a short offer.
