# Chart recipes

Query and `chart_config` shapes for common charts that aren't obvious from the `charts` reference topic. The examples use Rails request and job events; swap in the events and fields the project has, and run each query with `query_insights` before it goes in a widget. [designing-dashboards.md](designing-dashboards.md) says which chart fits which question.

**Several numbers in one billboard.** A billboard makes one tile per row by default. With `"groupType": "fields"` it makes one tile per column, titled by the alias, so one query fills a row of headline numbers:

```
filter event_type::str == "process_action.action_controller"
| stats count() as Requests,
        countIf(status::int >= 500) as `Server errors`,
        round(percentile(95, duration::float)) as `p95 ms`
```

```json
{"view": "billboard", "chart_config": {"groupType": "fields"}}
```

**A percentage, or any formatted number.** Billboards show values as the query returns them, so round and add the unit in the query. `toHumanString(x, "milliseconds")`, `toHumanString(x, "bytes")`, and `toHumanString(x, "short")` cover durations, sizes, and big counts.

```
filter event_type::str == "process_action.action_controller"
| stats count() as total, countIf(status::int >= 500) as errors
| only concat(toString(round(errors / total * 100, 2)), "%") as `Error rate`
```

```json
{"view": "billboard", "chart_config": {"groupType": "fields"}}
```

For one labelled tile per row (one per controller, say), keep the default `groupType` and point `titleField` and `valueField` at the aliases.

**p50 and p95 on one line chart.** With `"groupType": "fields"`, a line chart turns every column except `xField` into a series, so the percentiles come from one query:

```
filter event_type::str == "process_action.action_controller"
| stats percentile(50, duration::float) as p50,
        percentile(95, duration::float) as p95
  by bin() as time
```

```json
{"view": "line", "chart_config": {"groupType": "fields", "xField": "time", "yFieldUnit": "milliseconds"}}
```

The same shape puts any two aggregates on one chart. To split one aggregate by a field's values instead (one line per controller), keep the default `groupType`, set `yField`, and put the field in `zField`.

**Stacked bars with the zeros filled in.** A `stats … by bin, category` result has no row for a (bin, category) cell with no events, so a stacked chart draws gaps where it should draw zeros. `fill … across …` adds the missing cells; `including [...]` keeps a category on the chart even when it never occurs in the range. `rate()` keeps each bar per minute whatever bucket size `bin()` picks; filled cells come back as 0.

```
filter event_type::str == "perform.sidekiq"
| stats rate(count(), 1m) as per_minute by bin() as time, status::str as outcome
| fill time across outcome including ["success", "failure"]
```

```json
{"view": "bar", "chart_config": {"categoryField": "time", "valueField": "per_minute", "groupField": "outcome", "stacked": true}}
```

An `area` view with `"stacked": true`, `"xField": "time"`, `"yField": "per_minute"`, and `"zField": "outcome"` draws the same data as stacked areas.
