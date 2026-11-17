# Finding the job and wiring the report

Two lookups: where schedules live (to find the job and its schedule), and how each platform sends the report.

## Where schedules live

Search for the job's name first. If the user did not name one, look in these places and list every job you find.

| Scheduler | Look in | Schedule is |
| --- | --- | --- |
| crontab, cron.d | `crontab`, `*.cron`, `cron.d/`, `deploy/`, `config/`, Dockerfiles that call `crontab` | The five cron fields on the line. `CRON_TZ=` or `TZ=` above it sets the timezone; otherwise the box's timezone, usually UTC. |
| whenever (Ruby) | `config/schedule.rb` | `every 1.day, at: "2:30 am"` is `30 2 * * *`; `every 15.minutes` is `*/15 * * * *`; `every :sunday, at: "4am"` is `0 4 * * 0`. Timezone is the box's unless the file sets `ENV['TZ']`. |
| sidekiq-cron, sidekiq-scheduler | `config/sidekiq.yml`, `config/schedule.yml`, `config/initializers/sidekiq.rb` | `cron:` or `every:` per job |
| Solid Queue, GoodJob | `config/recurring.yml`, `config/initializers/good_job.rb` | `schedule:` or `cron:` per job |
| Laravel scheduler | `routes/console.php`, `app/Console/Kernel.php` | `->daily()`, `->hourlyAt(17)`, `->cron('0 */6 * * *')`; `->timezone()` if set |
| Celery beat | `celery.py`, `settings.py` (`CELERY_BEAT_SCHEDULE`) | `crontab(hour=2, minute=30)` or `schedule=timedelta(...)` |
| APScheduler, node-cron, node-schedule, Oban cron, Quantum | The file that registers jobs | Cron string or interval in the registration |
| systemd timer | `*.timer` | `OnCalendar=` |
| Kubernetes CronJob | `*.yaml` with `kind: CronJob` | `schedule:`, `timeZone:` |
| GitHub Actions | `.github/workflows/*.yml` with `on: schedule` | `cron:` (always UTC) |
| Heroku Scheduler, cloud cron services | Not in the repo | Ask the user for the schedule |

## How to report

The report fires only when the job finished its work. Put it last in the job, or chain it after the command with `&&`.

The host is `api.honeybadger.io`, or `eu-api.honeybadger.io` for EU accounts. The `url` field on the check-in from `create_check_in`, `get_check_in`, or `list_check_ins` already has the right host; copy it.

| Platform | Report with | Docs |
| --- | --- | --- |
| Shell: crontab, CI schedules | `cmd && curl -fsS -m 10 --retry 3 -o /dev/null <url>` | https://docs.honeybadger.io/guides/check-ins.md |
| No shell: systemd `ExecStart=`, Kubernetes `command`/`args` | `sh -c 'cmd && curl -fsS -m 10 --retry 3 -o /dev/null <url>'`, or a wrapper script. A bare `&& curl` becomes arguments to the job. | https://docs.honeybadger.io/guides/check-ins.md |
| Shell with the `hb` CLI already installed | `cmd && hb check-in --id <id>`. Do not use `hb run` alone: it reports failed runs too (with an error status), and any report counts as a good one, so a failing job looks healthy. | https://docs.honeybadger.io/resources/cli.md |
| Ruby: rake task, Sidekiq job, ActiveJob, script | `Honeybadger.check_in("<id>")` as the last line. The gem must already be installed and configured. | https://docs.honeybadger.io/lib/ruby/getting-started/performing-check-ins.md |
| Node.js | `await Honeybadger.checkIn("<id or slug>")` as the last line. Server only. | https://docs.honeybadger.io/lib/javascript/guides/check-ins.md |
| Laravel | `->pingHoneybadgerOnSuccess('<id>')` on the scheduled command. It takes an environment or list as the second argument. Do not use `->thenPingHoneybadger`: it reports failed runs too, so a failing job looks healthy. | https://docs.honeybadger.io/lib/php/integration/laravel.md |
| Python, Elixir, Go, PHP without Laravel, anything else | A `GET` to the URL with the language's HTTP client and a short timeout. Wrap it so a failed ping logs and does not raise: the job already succeeded. | https://docs.honeybadger.io/api/reporting-check-ins.md |

Python example:

```python
import urllib.request

def report_check_in(url):
    try:
        urllib.request.urlopen(url, timeout=10).read()
    except Exception as e:  # the job already succeeded; never fail it over the ping
        print(f"honeybadger check-in failed: {e}")
```

## Config-managed check-ins

The Node.js and PHP libraries can define check-ins in a config file and sync them on deploy (`npx honeybadger-checkins-sync`, `php artisan honeybadger:checkins:sync`). If the repo already does this (a `checkins:` array in `honeybadger.config.js` or `config/honeybadger.php`), add the new check-in there and report by slug. Do not also call `create_check_in`: the next sync would treat it as unmanaged and remove it.

## Timezone names

`cron_timezone` takes Rails zone names. Common conversions:

| IANA | Rails name |
| --- | --- |
| `UTC`, `Etc/UTC` | `UTC` |
| `America/New_York` | `Eastern Time (US & Canada)` |
| `America/Chicago` | `Central Time (US & Canada)` |
| `America/Denver` | `Mountain Time (US & Canada)` |
| `America/Los_Angeles` | `Pacific Time (US & Canada)` |
| `Europe/London` | `London` |
| `Europe/Berlin` | `Berlin` |
| `Europe/Paris` | `Paris` |
| `Asia/Tokyo` | `Tokyo` |
| `Australia/Sydney` | `Sydney` |

For others, use the city name from the IANA identifier (`Europe/Amsterdam` is `Amsterdam`). If the API rejects it, ask the user for the zone as shown in Honeybadger's check-in form.
