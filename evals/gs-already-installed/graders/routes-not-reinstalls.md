---
type: llm
---
PASS if the answer says Honeybadger is already installed in this app (the honeybadger gem and config/honeybadger.yml), does not propose installing it again, and asks what the user wants to do next or offers next steps such as checking that errors arrive, fixing errors, sending logs/events to Insights, or tracking deploys.
FAIL if it proposes installing the gem or rerunning the installer as the main step, or does not notice the existing install.
