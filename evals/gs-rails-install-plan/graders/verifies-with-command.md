---
type: llm
---
Judge only how the answer verifies the setup.
PASS if the answer sends exactly one test error, via the gem's install command (`bundle exec honeybadger install <key>`, which writes the config and sends a test exception itself), and confirms it arrived in Honeybadger (or says it will).
FAIL if it also runs `bundle exec honeybadger test`, calls `Honeybadger.notify`, or adds a temporary route, controller action, or raise to trigger a second test error; or if it has no verification step. Mentioning `honeybadger test` only to say it is unnecessary is fine.
