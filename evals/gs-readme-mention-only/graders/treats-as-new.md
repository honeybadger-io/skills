---
type: llm
---
Judge only whether the answer thinks Honeybadger is already installed in this app. Ignore everything else, including questions about which project to use.
PASS if the answer treats Honeybadger as not installed (the README only mentions it; there is no gem, config, or initializer).
FAIL if it says Honeybadger is already installed or configured in this app.
