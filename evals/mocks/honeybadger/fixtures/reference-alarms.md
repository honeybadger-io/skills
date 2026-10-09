# Alarms

Alarms monitor an Insights query and send notifications when a trigger condition is met.

Companion reading: alarm queries are BadgerQL (see the BadgerQL reference), and the **queries** instructions' event-class filtering and field-grounding rules apply. Their time-range (`ts`) rules do NOT — an alarm has no `ts`; the time window is the `evaluation_period`.

## Alarm fields

- `name`: string, required
- `query`: BadgerQL query, required — see Query guidelines below
- `evaluation_period`: how often the alarm is evaluated (`5m`, `1h`, `1d`). Minimum `1m`, must be more granular than a week
- `lookback_lag`: delay before each evaluation so late-arriving data is counted (`1m`, or `0s` for none)
- `trigger_config`: object defining when the alarm triggers (see below)
- `description`: string, optional
- `stream_ids`: array of stream ids the query runs against, optional — defaults to all of the project's streams. Stream ids are listed at `GET /v2/projects/{project_id}/streams`; unknown ids are silently dropped. Honeybadger-generated event types (`notice`, `deploy`, `uptime_check`, ...) live on the internal stream.

## Trigger config

### Structure

```json
{
  "type": "alert_result_count",
  "config": {
    "operator": "gt",
    "value": 100
  }
}
```

### Types

- `alert_result_count` — triggers based on the count of events matching the query

### Config fields

- `operator`: string, required — comparison operator
- `value`: integer, required — threshold to compare against (>= 0)

### Operators

- `gt` — greater than
- `gte` — greater than or equal
- `lt` — less than
- `lte` — less than or equal
- `eq` — equal
- `neq` — not equal

### Examples

Trigger when error count exceeds 50:

```json
{"type": "alert_result_count", "config": {"operator": "gt", "value": 50}}
```

Trigger when count drops below a threshold:

```json
{"type": "alert_result_count", "config": {"operator": "lt", "value": 10}}
```

Trigger when exactly zero events (missing heartbeat):

```json
{"type": "alert_result_count", "config": {"operator": "eq", "value": 0}}
```

Trigger when any events exist:

```json
{"type": "alert_result_count", "config": {"operator": "neq", "value": 0}}
```

## Alarm states

- `initial` — created but not yet evaluated
- `ok` — query result does not meet the trigger condition
- `alarm` — query result meets the trigger condition (alarm is triggered)

An alarm with a non-null `error` field means the query failed to execute; check the `error` field for details.

## Evaluation timing

The alarm evaluates at each `evaluation_period` boundary, looking back over the `evaluation_period` duration (offset by `lookback_lag` if set).

## Query guidelines

The alarm system automatically wraps the query to count results per evaluation period. The query should filter and/or aggregate events; the system handles the final counting.

Good queries:

```
filter event_type::str == "notice"
filter status::int >= 500
filter event_type::str == "request.handled" and duration::int > 5000
```

Queries with `stats` also work (the system counts the result rows):

```
filter event_type::str == "notice" | stats count() as count by fault_id::int
```

## Common patterns

Error spike detection:

```
name: "Error Spike"
query: filter event_type::str == "notice"
evaluation_period: 5m
lookback_lag: 1m
trigger_config: {"type": "alert_result_count", "config": {"operator": "gt", "value": 100}}
```

Slow requests:

```
name: "Slow Requests"
query: filter event_type::str == "request.handled" and duration::int > 5000
evaluation_period: 5m
lookback_lag: 1m
trigger_config: {"type": "alert_result_count", "config": {"operator": "gt", "value": 10}}
```

Missing heartbeat (no events in period):

```
name: "Missing Heartbeat"
query: filter event_type::str == "heartbeat"
evaluation_period: 10m
lookback_lag: 0m
trigger_config: {"type": "alert_result_count", "config": {"operator": "eq", "value": 0}}
```

Server errors (any 5xx):

```
name: "Server Errors"
query: filter event_type::str == "request.handled" and status::int >= 500
evaluation_period: 5m
lookback_lag: 1m
trigger_config: {"type": "alert_result_count", "config": {"operator": "gt", "value": 0}}
```
