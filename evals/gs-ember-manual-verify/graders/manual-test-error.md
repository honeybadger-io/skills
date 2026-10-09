---
type: llm
---
Judge only how the answer verifies the setup.
PASS if the answer verifies by triggering a test error by hand in the running app (for example a temporary throw in a route, action, or the console, with a recognizable message), confirms it arrives in Honeybadger (or says it will), and says to remove the temporary trigger afterward.
FAIL if it has no verification step, relies on a test or install command that the Ember integration does not have, or leaves the trigger in place.
