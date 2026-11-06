---
type: llm
---
Judge only how the answer verifies the setup.
PASS if the answer verifies by sending one test error by hand through the running app with a recognizable message (for example a `notify` call from the browser console, or a temporary `notify` call or throw in the app code), confirms it arrives in Honeybadger (or says it will check), and, when it adds code for the test, says to remove it afterward. A console call adds no code, so it needs no removal step.
FAIL if it has no verification step, relies on a test or install command that the Ember integration does not have, relies on an existing bug or failing page instead of a test error with a recognizable message, or leaves a trigger it added in place.
