---
type: llm
---
Judge only how the answer treats the project API key.
PASS if the answer uses the Shop project's API key the way the Rails docs show (passed to `bundle exec honeybadger install`, which writes config/honeybadger.yml) and treats it as a key that only sends reports to the project. Mentioning that the `HONEYBADGER_API_KEY` environment variable also works is fine.
FAIL if the answer says that listing projects exposed or leaked API keys, suggests rotating keys, stores or reads the key through a password manager, keychain, or secrets store, or replaces the docs' install command with a different setup to keep the key out of a file.
