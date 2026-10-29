# Contributing

Skills teach agents how to do a task with Honeybadger. They should help agents find the right documentation and MCP tools, not hold another copy of the docs.

## Adding or changing a skill

1. Read [AGENTS.md](AGENTS.md) for the layout and the rules for writing skills.
2. Check your guidance against [docs.honeybadger.io](https://docs.honeybadger.io). Link to the page instead of copying API signatures, config options, or limits that can change.
3. If the docs are missing something the skill needs, describe the gap in your pull request. Fix the docs first when you can.
4. Try the skill in a real agent session against a real project before you open a pull request.
5. Run the checks:

   ```bash
   python3 scripts/validate.py
   claude plugin validate .
   ```

## New skills

Open an issue first if the skill is large or adds a new area. Name the skill after the task, in kebab-case with a `honeybadger-` prefix (for example `honeybadger-setup-check-ins`), and add it to the table in [README.md](README.md).

## Submitting to the OpenAI plugin directory

OpenAI's plugin dashboard takes the package as a ZIP. Build it from a commit, with only the files the package uses:

```bash
git archive -o honeybadger.zip HEAD plugin.json mcp.json skills assets
```

Upload it at https://platform.openai.com/plugins. The listing and review test cases come from `plugin.json` (see [AGENTS.md](AGENTS.md)); the reviewer account and its sign-in details go in the dashboard, never in the package. See OpenAI's [submission guide](https://developers.openai.com/plugins/deploy/submission).
