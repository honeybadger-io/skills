---
type: llm
---
Judge only where the API key goes.
PASS if the answer keeps the API key out of committed source: an environment variable (such as HONEYBADGER_API_KEY), Rails credentials, or the gem's install command writing config that reads the key from the environment or credentials. Passing the key on the `honeybadger install` command line is fine.
FAIL if it writes the literal key into a file that would be committed (such as config/honeybadger.yml with the key inline) without saying to keep it out of source control.
