# Check-ins

Check-ins monitor scheduled and recurring processes (cron jobs, queue workers, backups). The process reports to Honeybadger on each run, and Honeybadger alerts when an expected report doesn't arrive on time. Check-ins are inbound (the process calls Honeybadger); uptime monitoring is the outbound counterpart (Honeybadger probes a URL). A silent process is exactly what check-ins catch — a cron job that stops running produces no error to track.

## Check-in fields

- `name`: string, optional (max 255 characters, unique per project). Display falls back to the check-in ID when blank
- `slug`: string, optional — lowercase letters, digits, hyphens, underscores; unique per project. Enables the slug report URL (see Reporting). **Immutable after creation** — updates silently ignore it
- `schedule_type`: `simple` or `cron`, defaults to `simple` when omitted. **Immutable after creation** — switching schedule types means deleting and recreating the check-in, which discards the check-in's report history and resets monitoring. Verify the existing check-in and confirm the change is intended before recreating
- `report_period`: required for `simple` — how often a report is expected, as `"<n> <unit>"` where unit is `minute`, `hour`, `day`, `week`, or `month` (`"5 minutes"`, `"1 day"`). Zero periods are invalid
- `cron_schedule`: required for `cron` — a standard cron expression (`"30 * * * *"`) describing when the job runs
- `cron_timezone`: optional for `cron`, defaults to `UTC`. Takes Rails/ActiveSupport zone names (`"Eastern Time (US & Canada)"`, `"London"`, `"UTC"`) — **IANA identifiers like `"America/New_York"` are rejected** with a "not included in the list" validation error
- `grace_period`: optional, same format as `report_period` — extra time allowed after the expected report before the check-in is considered missing. Use it for jobs with variable runtime: a job that runs hourly but can take 20 minutes gets `report_period: "1 hour"`, `grace_period: "20 minutes"`

## Plan limits

- **The `cron` schedule type and report payloads both require the Business plan** — they share one entitlement, not two. On Basic and Team plans: creating or updating a `cron` check-in fails with an upgrade error, and any payload (standard *or* custom fields) is discarded on report (the report itself still counts, and missing detection still works). Simple check-ins and missing alerts are available on all plans
- A `simple` period only approximates a regular cadence — it cannot represent an irregular cron schedule (weekdays only, specific times, uneven intervals). It's a lossy fallback, not an equivalent: surface the cron option and its Business requirement rather than silently swapping in a simple period when a user's schedule is really a cron
- Plans also cap the number of check-ins per account

## Lifecycle and states

- `pending` — created (or schedule changed) but not yet reported. **A pending check-in never alerts** — monitoring arms on the first report. After creating a check-in, the process must report once before missing detection begins
- `reporting` — reporting on schedule. The next expected report is calculated from the last report: for `simple`, last report + `report_period`; for `cron`, the next cron occurrence after the last report (plus `grace_period`)
- `missing` — the expected report (plus `grace_period`) didn't arrive. A notification is sent for each missed period, incrementing the missed count. When a missing check-in reports again, it returns to `reporting` and a recovery notification is sent
- `paused` — monitoring is suspended for a duration; missing detection resumes when the pause window ends

Changing `report_period` or `cron_schedule` resets the check-in to `pending` — it re-arms on the next report. A missing check-in stops notifying after 60 consecutive misses, or when its last report is more than 6 months old.

## Reporting

Each check-in has a report URL containing its ID:

```
https://api.honeybadger.io/v1/check_in/XyZZy
```

Accounts in the EU region report to `eu-api.honeybadger.io` instead.

- `GET` reports a simple ping; `POST` reports a ping plus an optional payload (see below). `HEAD` also works. No authentication is required — the ID *is* the credential, so treat the report URL like a secret: anyone who has it can submit fake reports and suppress missing alerts
- IDs are **case-sensitive**, in URLs and everywhere else
- If the check-in has a slug, an alternate URL uses the project API key and slug instead of the ID — useful to avoid embedding generated IDs in code and config:

```
https://api.honeybadger.io/v1/check_in/<project_api_key>/<slug>
```

- A report can also be sent by email to `<id>@report.hbchk.in` (no subject or body required; the ID is case-sensitive)

The typical integration appends a report to the scheduled command so it only fires on success:

```
@hourly /usr/bin/do_something && curl https://api.honeybadger.io/v1/check_in/XyZZy
```

### Report payloads

A `POST` report (with a `Content-Type: application/json` header) may include a JSON payload with the run's results (plan-gated — see Plan limits):

```json
{
  "check_in": {
    "status": "success",
    "duration": 1234,
    "stdout": "backup completed",
    "stderr": "",
    "exit_code": 0
  }
}
```

- `status`: `"success"` or `"error"`
- `duration`: integer, milliseconds
- `stdout` / `stderr`: captured output strings
- `exit_code`: integer

These five are the standard fields (the UI renders them specially). The payload is not restricted to them — any additional custom fields are accepted, stored, and queryable in Insights as `payload.<field>`.

The payload is informational and queryable only — it does not drive monitoring state. Any report sets the check-in to `reporting`, including one with `"status": "error"`; a payload status never triggers a missing alert. Only the *absence* of an expected report does.

Keep payloads under 20KB.

## Check-ins in Insights

Check-in activity is emitted as events with `event_type` `"check_in"` on the project's **internal** stream (the stream must be selected for these queries to return anything). Events carry `check_in_id`, `state`, and the report `payload` fields when present. Note which activity emits an event:

- `reporting` — emitted on each recorded report (deduplicated to at most one per ~30 seconds), even when the check-in was already reporting
- `missing` — emitted for every missed period, even when already missing (this is what drives the per-miss notifications)
- `paused` — emitted when the check-in is paused
- Creation, and a schedule change that resets the check-in to `pending`, emit **no** event

```
filter event_type::str == "check_in" and state::str == "missing"
| stats count() as count by check_in_id::str
```

This counts *historical* `missing` events per check-in, not check-ins that are currently missing — a check-in that recovered still has its past `missing` events. For current state, list or fetch the check-ins directly rather than querying events.

Payload fields are queryable under `payload` (`payload.status::str`, `payload.duration::int`, `payload.exit_code::int`) — history of run durations, failure exit codes, and output is all queryable. Custom payload fields are queryable the same way (`payload.<field>`). Payloads exist only for Business accounts (see Plan limits); on other plans they're discarded, so `payload.*` fields are simply absent — empty results mean no stored payload, not that the job reported no data.
