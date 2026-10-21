# Chart recipes

Shapes that are not obvious from the `charts` reference. Every `chart_config` key names an output alias of the query, so alias each aggregate. Run each query with `query_insights` before it goes into a widget; the examples use Rails request and job events, so swap in the event types and fields the project actually has.

## Several numbers in one billboard

A billboard makes one tile per result row by default. With `"groupType": "fields"` it makes one tile per result column instead, titled by the alias, so one query can fill a row of headline numbers:

```
filter event_type::str == "process_action.action_controller"
| stats count() as Requests,
        countIf(status::int >= 500) as `Server errors`,
        round(percentile(95, duration::float)) as `p95 ms`
```

```json
{"view": "billboard", "chart_config": {"groupType": "fields"}}
```

## A percentage, or any formatted number

Billboards show values as they come out of the query, so do the rounding and the unit in the query. `toHumanString(x, "milliseconds")`, `toHumanString(x, "bytes")`, and `toHumanString(x, "short")` cover durations, sizes, and big counts.

```
filter event_type::str == "process_action.action_controller"
| stats count() as total, countIf(status::int >= 500) as errors
| only concat(toString(round(errors / total * 100, 2)), "%") as `Error rate`
```

```json
{"view": "billboard", "chart_config": {"groupType": "fields"}}
```

For one labelled tile per row (one per controller, say), keep the default `groupType` and point `titleField` and `valueField` at the aliases.

## p50 and p95 on one line chart

With `"groupType": "fields"` a line chart turns every column except `xField` into a series, so the percentiles come from one query:

```
filter event_type::str == "process_action.action_controller"
| stats percentile(50, duration::float) as p50,
        percentile(95, duration::float) as p95
  by bin(1h) as time
```

```json
{"view": "line", "chart_config": {"groupType": "fields", "xField": "time", "yFieldUnit": "milliseconds"}}
```

The same shape puts any two aggregates on one chart. To split one aggregate by a field's values instead (one line per controller), keep the default `groupType`, set `yField`, and put the field in `zField`.

## Stacked bars with the zeros filled in

A `stats ... by bin, category` result has no row for a (bin, category) cell with no events, so a stacked chart draws gaps where it should draw zeros. `fill ... across ...` adds the missing cells; `including [...]` keeps a category on the chart even when it never occurs in the range.

```
filter event_type::str == "perform.sidekiq"
| stats count() as count by bin(1h) as time, status::str as outcome
| fill time across outcome including ["success", "failure"]
```

```json
{"view": "bar", "chart_config": {"categoryField": "time", "valueField": "count", "groupField": "outcome", "stacked": true}}
```

An `area` view with `"stacked": true`, `"xField": "time"`, `"yField": "count"`, and `"zField": "outcome"` draws the same data as stacked areas.

## Honeybadger's own events

`notice`, `deploy`, and the other events Honeybadger generates are on the internal stream, which a widget does not read unless its `streams` say so:

```json
{
  "type": "insights_vis",
  "presentation": {"title": "Errors by class"},
  "grid": {"x": 0, "y": 8, "w": 6, "h": 4},
  "config": {
    "streams": ["internal"],
    "query": "filter event_type::str == \"notice\" | stats count() as count by klass::str | sort count desc | limit 10",
    "vis": {"view": "bar", "chart_config": {"categoryField": "klass", "valueField": "count"}}
  }
}
```

For a plain list of recent errors, the `errors` widget type needs no query at all; see the `dashboards` topic for its `@ts` and `@ts.end` tokens.
