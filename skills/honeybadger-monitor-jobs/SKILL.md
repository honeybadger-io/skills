---
name: honeybadger-monitor-jobs
description: Adds a Honeybadger check-in to a scheduled job so the user is alerted when it stops running. Use when asked to monitor a cron job, scheduled task, rake task, periodic script, or background worker with Honeybadger, to add a check-in or ping to a job, or to find out when a job "goes silent" or "stops running". Also use right after adding a new scheduled job to a project that already uses Honeybadger, to offer a check-in for it.
---

# Monitor a job with a check-in

A check-in is a URL the job pings when it finishes. Honeybadger alerts when the ping stops. The work has three parts: find the job and its schedule, create the check-in, make the job report. Do all three in one pass. When the user asked for the check-in, creating it is the task, not something to ask permission for. Ask only when the job or the project is ambiguous.

If the user did not ask for monitoring (you just added a scheduled job for them and the project uses Honeybadger), offer it in one sentence after finishing the job, and go on only if they say yes.

## 1. Find the job

- If the user named a job, find its code and the schedule that runs it. The places schedules live are listed in [`references/wiring.md`](references/wiring.md).
- If the user did not name one and the repo has more than one scheduled job, list each job with its schedule and ask which to monitor. Stop there. Do not pick the newest, the most important, or the one the user "probably" meant.
- Read the job's code to find where it finishes successfully. That is where the report goes.
- Note the schedule, its timezone, and how long a run can take.

## 2. Translate the schedule

| The job runs | Create |
| --- | --- |
| At set times: a cron line, `every 1.day, at: "2:30 am"`, `->dailyAt('02:30')` | `schedule_type: "cron"` with the equivalent `cron_schedule` and `cron_timezone` |
| Every N minutes or hours with no fixed time | `schedule_type: "simple"` with `report_period` |

- `cron_timezone` takes Rails zone names (`"Eastern Time (US & Canada)"`), never IANA names (`"America/New_York"`), which the API rejects. The conversion table is in the reference. Take the zone from `CRON_TZ`, `TZ`, or the scheduler's config. If nothing sets one, use UTC, say that you assumed it, and offer to change it with `update_check_in`.
- `grace_period` is how long a run can take, rounded up. Say what you chose.
- Cron check-ins need the Business plan. If `create_check_in` fails with a plan or upgrade error, tell the user, and offer a simple check-in with the gap it leaves (it checks the interval, not the time). Do not swap in a simple schedule silently.

## 3. Create it

1. Fetch the `checkins` topic with `get_reference` first (skip if it is already in your context).
2. `list_projects` and match the repo's name. If more than one project could be it, ask.
3. `list_check_ins` for that project. If one already matches the job by name or slug, reuse it and skip creation. If its schedule differs from the code, say so and change it only if the user agrees.
4. If the repo already manages check-ins from `honeybadger.config.js` or `config/honeybadger.php` (a `checkins` array), add the new one there and report by slug. Do not call `create_check_in`: the next sync would remove it. See the reference, then skip to "Make the job report".
5. `create_check_in` with a `name` in words ("Nightly sales report"), a kebab-case `slug`, and the schedule. Read `id` and `url` from the response. The `url` already has the right host for the account's region (EU accounts report to `eu-api.honeybadger.io`); copy it rather than typing one.

## 4. Make the job report

The report is the last thing a successful run does. A run that fails or stops early must not report, or Honeybadger cannot tell it from a good one.

- **Shell schedulers** (crontab, CI schedules, anything that runs the command through a shell): change the scheduled command line, not the script. Append `&& curl -fsS -m 10 --retry 3 -o /dev/null <url>` after the command and its redirects. If the box already has the `hb` CLI, `&& hb check-in --id <id>` works too, but do not install it just for this: curl needs nothing.
- **No-shell schedulers** (systemd `ExecStart=`, Kubernetes `command` and `args`): these run the program directly, so `&& curl` would be passed to the job as arguments. Wrap the command in `sh -c 'cmd && curl ...'`, or call a small wrapper script that runs the job and then curls.
- **App schedulers** (rake, Sidekiq, Solid Queue, Laravel, Celery, node-cron, and the like): add the report as the last line of the job. Use the SDK helper when the app already has the Honeybadger library, else an HTTP GET. The per-platform table is in [`references/wiring.md`](references/wiring.md).
- The Ruby gem's `Honeybadger.check_in` takes the check-in ID (or the full report URL), not a slug. The JavaScript `checkIn` and the Laravel macros take either.
- The ID is a credential: anyone with it can fake reports. Store it the way the project stores its Honeybadger API key. If the key comes from an environment variable, read the ID from one too. If the key sits in committed config, the ID can sit beside it.
- If the job runs in several environments, report only from the one that is monitored (usually production). The Laravel macro takes an environment argument; elsewhere, guard on the environment.

## 5. Arm it

A new check-in is `pending` and never alerts until it gets its first report. Do not ping it yourself: that arms monitoring before the change is deployed, and the first alert will be a false one. Tell the user to deploy, let the job run once (or run it by hand on the box), and then confirm with `get_check_in` that the state is `reporting`.

## Report

End with these parts, in order:

1. The check-in: name, ID, project, schedule, timezone, and grace period, naming any value you assumed.
2. The diff.
3. What is left: deploy, the first run, and the state check.
