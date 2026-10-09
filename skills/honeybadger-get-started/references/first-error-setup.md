# First-error setup

Goal: a real error from the running app is confirmed in Honeybadger through the MCP, and
the app is on a path to production. A local-only success isn't the goal — the value of
error tracking comes from errors real users hit.

## 1. Platform and region

1. Map the project to its docs page with [`sdk-docs.md`](sdk-docs.md) and fetch the page.
2. Confirm the platform with the user before installing anything. Files can mislead:
   monorepos, a frontend and a backend in one repo, a framework layered on another.
3. If you're connected to the EU MCP endpoint (`eu-mcp.honeybadger.io`), the account is in
   the EU region, and the library must report to EU endpoints. Set every region-specific
   option the library's configuration reference lists — some libraries have several.

## 2. Project and API key

1. Choose a project from the `list_projects` result. If several could fit, ask.
2. If none fits, propose a name and ask before calling `create_project` — it creates
   something visible to the user's whole team. If `create_project` isn't among your tools,
   the connection is read-only: the user either re-authorizes with read-write access or
   creates the project in the UI.
3. Get the API key: use `list_project_keys` if your MCP has it (keys start with `hbp_`;
   create one with `create_project_key` only after asking). Otherwise call `get_project`
   on the chosen project and use its `token` field — `list_projects` doesn't include it.
4. Configure the key the way the docs show — usually the `HONEYBADGER_API_KEY` environment
   variable or the library's config file. The key can send reports to the project but
   can't read data through the REST API, and browser and mobile apps ship it publicly.
   For server apps, keep it out of source control anyway: anyone holding it can send
   reports to the project.

## 3. Install

Install and configure the library following the platform docs, keeping their default
configuration. The defaults are what Honeybadger recommends; trimming them removes things
users expect to have.

## 4. Verify

Client libraries don't report from development or test environments by default, so a
correct install sends nothing from a local run. Before verifying, temporarily enable
reporting with the switch the library's docs describe, and remove it afterward. A missing
switch is the usual reason nothing shows up.

Verify with the platform's own instructions:

- **The docs have a test or install command that sends a test error** (for example
  `bundle exec honeybadger install` or `bundle exec honeybadger test` for Ruby, and
  `php artisan honeybadger:install` or `php artisan honeybadger:test` for Laravel): run it as the docs
  say. If the install step already sent a test error, confirm that one instead of sending
  another.
- **The docs show another way to test** (a settings checkbox or a snippet that notifies or
  raises): follow it.
- **The docs have no test step** (for example Ember): trigger a test error yourself. Run
  the app the way it normally starts and raise an error on a real code path. A temporary
  route, button, or a raise behind a one-off flag is fine; remove it afterward. Give the
  error a unique message (e.g. `Honeybadger test error <timestamp>`) so you can find
  exactly it. If you know how to start the app, offer to do it; otherwise ask the user to
  start it or tell you how.

To confirm the test error:

1. Fetch the `errors` topic with `get_reference` for the search syntax.
2. Call `list_faults` with the project ID, `order: recent`, and `q` matching the error's
   message. Ingestion usually takes seconds; poll a few times before concluding it's
   missing.
3. Call `get_fault` and `list_fault_notices` on the match. It counts only if the newest
   notice was created after you triggered it: Honeybadger groups repeat errors
   into one fault, so a test from an earlier install can match the search even when
   this one is broken.
4. Report the error class, message, and fault URL to the user.

If nothing arrives within about two minutes, check in this order: reporting is enabled for
the current environment, the key belongs to this project, the region matches (a US key
fails against EU endpoints and vice versa), the library initializes before the error, and
the triggering code actually ran. Temporarily turn on the library's debug logging (see
its docs) and read what it prints at boot and on notify. Keep diagnosing until the error
arrives; pointing the user at their dashboard doesn't close the loop.

Track every temporary change you make — the reporting override, the trigger, and any
debug logging — and remove all of them whenever this step ends: after verification, when
diagnosis stalls, or when the user stops you. A leftover crash route or forced
development reporting does more harm than an unfinished setup. After verification, offer
to resolve the test faults with `update_fault`, sharing their URLs first so the user can
look.

## 5. Production

- If you can see how the project deploys — CI config, a Dockerfile or Procfile, a hosting
  platform, a deploy section in `AGENTS.md` or `CLAUDE.md` — propose the changes so
  production has the API key, the environment name, and the revision. Wire up deployment
  tracking from the library's docs so errors tie to the deploy that introduced them.
- Otherwise, ask how they deploy and offer to wire it in. Production is where the real
  errors are, so recommend this step rather than leaving it as optional.
- Take deploy actions only with the user's consent.

## 6. Readable backtraces

Production builds can mangle backtraces that look fine locally.

- JavaScript or TypeScript that's bundled or minified (browser apps, Next.js, React
  Native) needs source maps.
- Apple platforms need dSYMs.
- Server-side languages (Ruby, Python, PHP, Elixir, Go, Java, .NET, …) usually need
  nothing; say so and move on.

The docs for each are under "Readable backtraces" in [`sdk-docs.md`](sdk-docs.md). Also
check the verified error's backtrace in its notice: frames that are minified or missing
file and line information locally will be worse in production.

## Done when

- [ ] Library installed with its default configuration
- [ ] Test error, sent the way the platform docs say (or triggered by hand when they
      have no test step), confirmed through the MCP; class, message, and URL reported to
      the user
- [ ] Temporary trigger, reporting override, and debug logging removed
- [ ] Production path agreed with the user (no deploy without consent)
- [ ] Backtrace readability addressed for this platform
