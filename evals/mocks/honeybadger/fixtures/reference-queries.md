# Insights queries

Fundamentals for writing BadgerQL queries against Honeybadger Insights — what to establish before aggregating, and the traps that silently produce wrong results. For the language itself (syntax, functions, types), see the BadgerQL reference.

## Streams

Events live in streams, and every project has two: `default` (events your applications send) and `internal` (events Honeybadger generates about the project — errors, deploys, uptime checks, check-ins). Which streams a query searches is a request-level selection like `ts`, NOT a query clause — an event class that lives on an unselected stream returns nothing, which looks identical to the events not existing. Honeybadger-generated event types (`notice`, `deploy`, `uptime_check`, ...) require the internal stream. `@stream.id` and `@stream.name` identify each result event's stream.

Streams are selected by id via the `stream_ids` request parameter; when omitted, all of the project's streams are searched. A project's streams and their ids are listed at `GET /v2/projects/{project_id}/streams`. Selection is per-project: ids not belonging to the queried project — unknown or from another project — are silently dropped, so a cross-project query partially succeeds and looks complete. Streams are provisioned asynchronously: a just-created project's stream list may be empty or partial for a short time — retry before concluding streams are missing.

## Time range

The time range (`ts`) is a *separate* parameter from the query — BadgerQL queries do NOT filter on time in their body. `ts` accepts three forms:

- Rolling windows, as an ISO-8601 duration: "last 15 minutes" → `PT15M`, "last hour" → `PT1H`, "last 24 hours" → `PT24H`, "last 7 days" → `P7D`, "last 30 days" → `P30D`
- Calendar windows, as a keyword: `today`, `yesterday`, `week` (this week so far), `month` (this month so far)
- Absolute ranges, as slash-separated ISO-8601 timestamps: `2026-01-22T00:00:00/2026-01-29T00:00:00`

Calendar windows and absolute ranges are interpreted in the `timezone` parameter — an IANA name (`America/Chicago`) or a UTC offset in seconds, defaulting to UTC. Rolling durations are timezone-independent. When the user's question is calendar-shaped ("today", "since Monday"), set `timezone` to their timezone or the window boundaries will be UTC's, not theirs.

`timezone` also changes outputs, not just the window: datetime values in results (`@ts`, `now()`) are returned in that timezone, and `bin()` buckets align to its boundaries — `bin(1d)` splits days at that timezone's midnight, so daily counts differ between timezones. When comparing timestamps across queries or against other systems, use one consistent `timezone` (or leave everything UTC).

Anything that scopes a query to a time window belongs in `ts`, never in the query body — even when phrased as a filter ("events from today", "where the time is in the last hour"). The only time-related clause that belongs in a query body is `bin(...)` for time-grouped aggregates — that's binning, not filtering.

Never write in a query body:

- `filter @ts > now() - PT1H` — use `ts: "PT1H"` instead
- `filter @ts between formatDate(...) and ...` — set `ts` and let the platform handle the window
- `formatDate(...)`, `nowMinus(...)`, `dateAdd(...)`, string-concatenated ISO timestamps — these are NOT BadgerQL functions; don't invent them
- Any `@ts`-based filter that mirrors a requested time range — `ts` already covers it

## Filter by event class

When a query targets a class of events ("sql queries", "errors", "deploys", "cache reads"), include an explicit `filter event_type::str == "<exact_value>"` clause. Without it, aggregates run across every event type in the selected streams and silently return wrong numbers.

Use exact `event_type` values that are grounded — named in the request, observed in prior results, or discovered. Do not guess: a plausible-looking value that doesn't exist matches nothing. When unsure, inventory the data first:

```
fields @preview | limit 1 by event_type::str
```

## Query parameters

Query text may contain parameters: `${name}`, or `${name:-default}` with an inline default. Values are resolved from URL query parameters of the same name (`?hostname=web-1`), falling back to the inline default; a parameter with no URL value and no default leaves the query unable to run until a value is supplied. Up to 20 distinct parameters per query.

```
filter hostname::str == "${hostname:-web-1}" and environment::str == "${env}"
```

Parameters are resolved by the app UI before the query executes. A query submitted directly to the API with an unresolved `${...}` is NOT substituted — it's sent literally and will not match; substitute values yourself before submitting.

## Query URLs

A query, its time range, and its visualization serialize into a shareable URL at `/projects/{project_id}/insights/query`:

- `query`, `ts`, `timezone`, and `view` are query parameters
- Chart config fields (see the charts instructions) are ALSO flat query parameters — every parameter other than the reserved ones is read as a chart config field. There is no `chart_config` parameter; do not JSON-encode the config object into the URL
- Query-parameter values (`${name}` in the query text) are ALSO supplied as URL parameters of the same name: `?env=staging`

```
?query=filter+status%3A%3Aint+%3E%3D+500%0A%7C+stats+count()+as+count+by+bin(1h)&view=line&xField=bin(1h)&ts=P7D
```

## Field names: no invention

Only reference fields that are known to exist:

1. Fields observed in the data (via discovery queries), OR
2. Top-level meta fields documented in the BadgerQL reference (`@ts`, `@id`, `@preview`, `@stream.id`, etc.), OR
3. Fields named as literal identifiers in the request (`duration`, `response.status_code`). A natural-language concept ("response time", "error code") is NOT a grounded field name — it must be resolved through (1) or (2) first.

Do NOT invent fields based on intuition (e.g. `scheduled_time`, `actual_time`, `response_time`, `error_code`). If a request implies fields you can't ground, inspect a sample first:

```
fields @preview | limit 5
```

## Result limits and retention

Results are capped at 1,000 rows regardless of the `limit` you write. Aggregate (`stats ... by ...`) instead of enumerating raw events — a raw dump that "looks complete" at 1,000 rows usually isn't.

Event retention is plan-dependent and can be as short as 7 days. A `ts` window longer than the retention period silently returns only what's retained — an apparent drop-off at the retention boundary is data purge, not a real change in the metric.
