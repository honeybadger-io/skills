# Designing Insights dashboards

How to build a dashboard someone can glance at and know whether things are OK, and if not, where to look: for a service, a job queue, a release, or the business itself. Each rule is phrased so it can be checked against a saved dashboard. Mechanics (widget objects, `chart_config` fields, the grid) live in the `dashboards` and `charts` topics; this covers the choices. Query patterns marked *verified* were run against the Insights engine.

## 1. Know what you're building

- **When the user named what they want,** build that: a service, a feature, a job queue, a team's area, a customer, a release, the business, or specific widgets. The rest of this guide decides how each part is shown, not whether it belongs.
- **When the request is vague but asks for a dashboard** ("a dashboard for my app"), build for the obvious subject (the app's health: traffic, errors, latency) and say what it covers, so the user can redirect.
- **Know who reads it.** On-call at 2 AM needs symptoms and where to look next; a weekly review needs trends.
- **Keep it to one dashboard.** If the request spans more (a service and its infrastructure), build what was asked and mention what could be its own dashboard, rather than splitting unasked or building one wall of charts.
- **Check the events exist first.** If the question needs events the project doesn't send, say what's missing and how to instrument it. Don't build widgets that will render empty.
- **Field names differ by runtime.** Rails request events have `status` and `duration`; Laravel's `request.handled` schema has no `status`. Check the event's schema (docs: insights/event-types/<runtime>/<event>) or `fields @preview`, never assume.

### When the user isn't sure what to build

Start from a question with them, then propose a dashboard that answers it:

- **What do you watch for?** "Is checkout healthy?", "Did the deploy make anything worse?", "Are background jobs keeping up?", "Are people finishing signup?"
- **Who looks at it, and when?** That decides symptoms or trends, minutes or weeks.
- **What would you do differently after seeing it?** A widget nobody would act on doesn't belong.

## 2. Pick what to measure

Insights events can be anything an app sends: requests and queries, jobs, deploys, orders, signups, payments, feature use. The kind of question decides the measures.

### Rules for every kind

- **Every number needs context.** A value alone can't say whether things are OK. Put a trend next to a headline number, or compare it with the previous period or a target.
- **Would anyone act differently after seeing it?** If not, it's a vanity metric: leave it off. Cumulative totals ("signups ever", "requests all time") are the usual offenders; show rates, ratios, and recent activity instead.
- **Ratios over counts when the base varies.** Error rate, conversion rate, failure rate. Compute one ratio over all the events, never an average of per-group ratios. A percentage: `round(countIf(status::int >= 500) / count() * 100, 2)`.
- **Show the denominator.** "Accounts querying" means little without "of active accounts"; put the base next to the ratio or in the label.
- **Count the right thing.** Events (`count()`) and people or accounts (`unique(user_id::str)`, BadgerQL's count-distinct) answer different questions. "Orders" and "customers who ordered" are not the same chart. Count accounts or users rather than requests when one sender can dominate: a single busy account can make most of the requests.
- **Exclude the same things everywhere.** Internal accounts, test traffic, health checks, the default page-load query: apply the same exclusions in every widget, ideally through one shared parameter, so widgets agree with each other.
- **Keep personal data off shared dashboards.** Dashboards are shared with the whole team. Count or `unique()` emails, IP addresses, and customer names rather than listing them in a table.
- **Small numbers are noise.** A jump from 2 to 3 is +50% and means nothing. Show the counts, not just the percentage, and widen the range or the bin before calling a trend.
- **Weekly patterns are real.** Most traffic and business events differ by weekday. Compare a day with the same weekday a week earlier, and judge stable metrics by the week, not the day.
- **Compare with the previous period inside one query** by splitting the selected range in half, so the two windows stay equal whatever range the viewer picks (verified): `stats countIf(@ts >= @query.start_at + (@query.end_at - @query.start_at) / 2) as recent, countIf(@ts < @query.start_at + (@query.end_at - @query.start_at) / 2) as earlier`, shown as a billboard with `groupType: fields`. Set `default_ts` to twice the window you mean (`P2D` for "last 24 hours versus the 24 before"), and title it by the halves ("this half of the range versus the previous half") so it still reads right when the range changes. Don't split at `now() - …`: a wider or past range then compares unequal windows.
- **Calendar windows follow the viewer's timezone.** On a dashboard, "today", "this week", and `bin(1d)` split at midnight in each viewer's selected timezone, so two viewers can see different daily numbers. Nothing to set; worth knowing when numbers are compared across people.

### Service health (operations)

Start from the four golden signals: latency, traffic, errors, saturation. RED (rate, errors, duration) is the same minus saturation; USE (utilization, saturation, errors) is for machines and resources, and explains causes rather than symptoms. Lead with symptoms users feel; put causes below.

| Signal | Measure it as | Not as |
|---|---|---|
| Latency, as users feel it | `percentile(50, …)` and `percentile(95, …)` (or 99) of the duration field, over time | `avg()` alone. A 100 ms average can hide 1% of requests taking 5 s. |
| Latency of failures | Successful and failed requests separately when errors are fast (a 500 in 3 ms drags the percentile down) | One mixed series |
| Traffic | `rate(count(), 1m)` (requests per minute) by `bin()` | A raw count per bucket, which changes with the bucket size |
| Failed requests | The 5xx rate over all requests, from request events: what users hit | A count of 5xx responses when traffic varies |
| Errors Honeybadger tracked | The `errors` widget, listing the faults themselves (unresolved, or first seen since the last deploy). When charting `notice` events, break them down by fault or error class | One total of notices: a single noisy fault can make thousands of them |
| Saturation | Queue depth, queue latency, worker or connection-pool usage (job and server stats events) | CPU alone, if the bottleneck is elsewhere |

- **Pick the statistic by the question, not by habit.** How slow it feels → p50 and p95. How much work or cost (worker time, capacity) → `sum()`, or `avg()` with the count beside it; percentiles can't be added up. Which group is slowest → p95 per group, or `avg()` when durations are consistent. Did it change → either, but the same one over time.
- **Failed requests and Honeybadger errors are different counts.** A fault is one unique error and its notices are the occurrences. Not every 5xx is a notice (exceptions the app ignores, like `RecordNotFound` returning 404, never reach Honeybadger), and not every notice is a 5xx (background jobs, errors reported by hand, requests that still returned 200). Show both when both matter, and don't expect them to match.
- **Notices live on the `internal` stream.** A widget charting `notice` events needs `internal` in its `streams`, or it renders empty. Scope them to the dashboard's subject with fields like `params.controller`, `params.action`, or `component` (a checkout dashboard keeps only checkout errors), break them down by `klass` or `fault_id`, and filter `environment` to keep production apart. Which fields exist depends on what the app sends: check with `fields @preview` on `notice` events first.
- **Never average percentiles** across hosts, endpoints, or time bins. Compute the percentile over the underlying events.
- **Percentiles need enough events.** A p99 over 50 events is the maximum. For low-volume groups or short buckets, show `max()` or `avg()` with the count instead.
- **When the distribution's shape matters** (bimodal latency, outliers), show it: `histogram`, or `heatmap` over time.

### Background jobs and pipelines

- Throughput (jobs finished per unit of time), failure rate, duration percentiles, and, where the events carry it, queue latency or backlog.
- Break down by job class or queue; one slow class hides in an overall average.
- Scheduled jobs: did it run, and when? A check-in, or the `checkins` widget, answers that better than a count chart.

### Release check

- The service signals, around a deploy: put the `deployments` widget next to the trends so a change lines up with its deploy.
- Request and job events don't carry the release (verified for Rails, Sidekiq, Django, Laravel schemas); only error notices have `revision`. So compare before and after on the time axis rather than by version, or break errors down by `revision`.
- New errors since the deploy: an `errors` widget filtered to the time range.

### Business and product metrics

- **Outcomes first:** completed orders, signups, payments, activations: the events that mean the business worked. Then the steps that lead to them.
- **Conversion between steps** (viewed → added to cart → checked out) as rates, with the steps in their real order, not alphabetical. Show where people drop off.
- **Money:** sum the amount field, say the currency and whether refunds are netted out, and watch for amounts stored in cents.
- **Adoption:** unique users or accounts using a feature, as a share of active users, not a raw event count.
- **Leading and lagging together:** pair the outcome (revenue, completed orders) with what predicts it (checkouts started, trials begun), so the dashboard warns before the outcome moves.
- **Segment carefully:** by plan, country, or source when the question asks for it; a parameter (`${plan}`) beats one widget per segment.

### One customer or account

- Scope every widget to the account with a parameter (`${account_id}`), with no default, or a safe one, so the dashboard serves any customer.
- Their requests, errors, and jobs over time, plus the specific failures (a table of recent failing requests or an `errors` widget filtered to them).

## 3. Pick the view by the shape of the question

| The question | View | Notes |
|---|---|---|
| Is it OK right now? (one number) | `billboard` | Round in the query and put the unit in the alias or with `toHumanString`. Several headline numbers from one query: `groupType: fields`. |
| Is it changing? | `line`, with `bin()` on the x axis | Several series (p50 and p95, or one per status) on one chart. |
| How do parts add up over time? | `area` with `stacked: true`, or stacked `bar` | Only when the parts sum to a meaningful total, there are few series (≤5), and missing buckets are filled with zeros. Otherwise use separate lines. Stacking hides individual series. |
| Where do people drop off? (funnel) | `bar`, one bar per step in step order | Order steps explicitly: `fields step, n, cond(step == "viewed", 1, step == "added", 2, 3) as step_order \| sort step_order asc`. **`sort` defaults to descending** (verified), so without `asc` the funnel comes out backwards. Add a billboard for the overall conversion rate. |
| Which ones? (ranking) | `bar`, sorted, `horizontal: true` for long labels | Limit in the query: `by top(10, field::str)`, or `sort … \| limit 10`. Say "top 10" in the title. |
| Exact values, several columns per row | `table` | Format units in the query (`toHumanString`). Sort by the column that answers the question. |
| What's the spread? | `histogram`; over time, `heatmap` | A heatmap query must `sort` by x then y. |
| Do two measures move together? | `scatter` | |
| What share is each part? (one moment) | `pie` only with ≤5 parts; otherwise `bar` | Comparing the same part across groups: side-by-side bars, not pies or stacks. |
| Errors, deploys, alarms, check-ins, uptime | Honeybadger's `errors`, `deployments`, `alarms`, `checkins`, `uptime` widgets | They link to the underlying records; don't rebuild them as charts. |

## 4. Write queries that chart well

- **The query's aliases are the chart's fields.** Every field `chart_config` names must be an alias the query outputs, exactly. Check this before saving; a mismatch renders empty.
- **Use bare `bin()` with `rate()` on time charts.** Bare `bin()` sizes buckets to the range the viewer picks (1-minute buckets for an hour, 15-minute buckets for a day, verified), so the chart keeps a readable number of points. That also changes what a plain `count()` per bucket means: the same traffic reads about 700 per bucket over an hour and about 10,500 over a day. `rate(count(), 1m)` divides each bucket by its length, so every point means "per minute" at any range (the `badgerql` topic's `rate` entry has the details):
  - **Pick the unit that keeps numbers readable:** `rate(count(), 1m)` for busy traffic, `rate(count(), 1h)` or `1d` for low-volume events like signups.
  - **Totals use plain `count()`.** A billboard answering "how many orders in this range" wants the count, not a rate.
  - **A fixed `count() by bin(1m)` only fits short ranges.** Over a day it returns more than the 1,000-row result cap, and the chart is cut off.
  - **Wide buckets smooth spikes.** Each point is the average for its bucket, so a 3-minute spike inside an hour-long bucket shows as a small bump. Zoom in to see it.
  - **The last bucket is still filling,** so the last point dips. Don't read it as a drop.
  - **One fixed bucket earns its place:** a calendar comparison, such as `bin(1d)` for days of the week, on a dashboard whose default range is at least a week.
- **Fill gaps for counts over time.** A bucket with no events has no row, so lines skip and stacks shift. `fill t` zero-fills a time series; `fill t across outcome including ["success", "failure"]` does it per category (verified). It also adds a `null` category for events missing the field, so filter `isNotNull(...)` first if that series isn't wanted.
- **Limit categories** with `top(N, field)` in `by`; long tails make unreadable bars and pies.
- **Units:** set `yFieldUnit`/`valueFieldUnit` where the view supports it (`percent`, `milliseconds`, `microseconds`); otherwise put the unit in the alias or title.
- **Time range belongs to the dashboard** (`default_ts`), never in the query body.
- **One widget, many environments:** use a parameter with a default (`${env:-production}`) instead of a widget or dashboard per environment, host, or customer.

- **Worked examples:** [recipes.md](recipes.md) has queries and `chart_config` for several numbers in one billboard, a formatted percentage, p50 and p95 on one line, and stacked bars with the zeros filled in.

## 5. Make it cheap to load

Every widget runs when the dashboard opens, all at once, and again whenever the viewer widens the range. A filter on `event_type` still scans the whole time range of the stream, so cost grows with the range and with how much the stream holds. A handful of widgets scanning a week of request events on a busy project can time out.

- **Run each query at the default range and at the widest range viewers will pick** (often 7 or 30 days), and check speed as well as rows. Narrow a slow widget you chose, or leave it out; keep a slow widget the user asked for and tell them, with a narrower version they could use.
- **Filter to the narrowest events first,** and prefer small event types over the biggest streams when either answers the question.
- **Keep the default range short** (`default_ts`), and use fewer widgets.

## 6. Lay it out

- **Top row: headline numbers** (billboards) that answer "is it OK?". **Then trends** (lines over time). **Then breakdowns** (bars, tables, lists) that answer "where?". General to specific.
- **Most important in the largest, top-left position.**
- **Related widgets side by side, on the same time range,** so a spike in one lines up with the other (traffic next to errors next to latency, as in RED rows).
- **One row per service or component,** in the order requests flow through them, when the dashboard covers several.
- **6 to 12 widgets.** More and nothing stands out; split into dashboards that link to each other.
- **Split when magnitudes differ.** One busy endpoint flattens the rest on a shared axis; give it its own chart, or chart rates and percentages, not raw values.

## 7. Words and color

- **Titles state the measure and unit:** "p95 response time (ms)", "5xx error rate (%)", "Jobs failed per hour". Not "Latency" or "Errors".
- **Subtitles state the scope and the limits:** which events, filters, or environment, and anything that skews the number, next to it ("guest checkouts counted as one user", "excludes internal accounts").
- **Color means something:** red is bad. Don't rely on red against green alone (color blindness). Don't color for decoration.
- **Bars start at zero;** lines don't have to.
- **Targets:** charts have no threshold or target line (`chart_config` has none). Put the target in the subtitle ("target: p95 under 500 ms"), or compute the gap in the query.

Before saving, prove each widget and hand the dashboard over as SKILL.md says ("Build widgets that work" and "Report").

## Checklist

Before saving a new dashboard, check every widget against this list and fix what fails.

- [ ] Every widget serves what the dashboard is for: the subject the user named, or the question agreed with them.
- [ ] Each statistic fits what it shows: percentiles for latency as users feel it, sums or averages for load and cost, a rate or ratio with its denominator when the base varies.
- [ ] Events and people are kept apart (`count()` versus `unique()`), and the title says which.
- [ ] Time charts use bare `bin()` with `rate()` (a fixed `bin(1d)` only for calendar comparisons over a week or more), and fill gaps.
- [ ] Each view is readable: no pie with more than five parts or one part dwarfing the rest, stacks only for parts of a meaningful whole, rankings sorted and limited.
- [ ] Headline numbers on top, trends next, breakdowns and lists below.
- [ ] Titles carry the measure and unit; subtitles carry the scope and any limits.
- [ ] No personal data on the dashboard (emails, names, IP addresses, customer or company names): count them, don't list them.
- [ ] No two widgets overlap, and none runs past column 12 (`x + w` at most 12).
