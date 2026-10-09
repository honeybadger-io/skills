---
type: llm
---
Judge only how the answer verifies the setup.
PASS if the answer uses the honeybadger gem's own command to send a test error (`bundle exec honeybadger install <key>`, which sends a test exception, or `bundle exec honeybadger test`) and confirms it arrived in Honeybadger (or says it will).
FAIL if it adds a temporary route, controller action, or raise to the app to trigger a test error, or has no verification step.
