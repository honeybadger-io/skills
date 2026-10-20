<!-- Generated file — do not edit by hand. -->
# Dashboards

A dashboard is a collection of widgets displayed on a project's Insights page.

Companion reading: widget queries are BadgerQL (see the BadgerQL reference), the **queries** instructions cover query fundamentals and `${...}` parameters, and the **charts** instructions cover `chart_config` fields.

## Dashboard object

- `title`: string, required (max 255 characters)
- `default_ts`: string, optional — default time range as an ISO 8601 duration (`PT3H`, `P1D`) or keyword (`today`, `yesterday`, `week`, `month`)
- `widgets`: array of widget objects, required

Dashboard responses also include the dashboard's page in the web UI (read-only) as `url`. Give it to the user rather than constructing one.

## Widget object

- `type`: string, required — one of the widget types below
- `id`: string — omit when creating a widget; the server assigns one. A widget without an `id` is treated as new. Preserve existing `id`s when updating a dashboard so widget state and history are retained
- `grid`: object — layout position `{x, y, w, h}` (see Grid layout)
- `presentation`: object — `{title, subtitle}` display strings (max 255 characters each)
- `config`: object — type-specific configuration

## Widget types and purposes

- `insights_vis` — renders a BadgerQL query as a chart or table; the primary building block
- `errors` — list of the project's errors, optionally filtered by a search query (syntax: see the **errors** instructions)
- `alarms` — current status of the project's Insights alarms
- `deployments` — recent deploy history
- `checkins` — check-in statuses
- `uptime` — uptime monitor statuses

## Config fields by widget type

Valid widget `type` values: `insights_vis`, `alarms`, `errors`, `deployments`, `checkins`, `uptime`.

### `insights_vis`
- `streams`: array of default|internal — Streams to query (defaults to ["default"])
- `query`: any — BadgerQL query producing the widget's data
- `vis`: any — How to render the result: `{view, chart_config}`

### `alarms`
- `limit`: integer, minimum 1 — Max alarms shown
- `filter_state`: string (all|triggered|ok) — Show all alarms or only those in one state

### `errors`
- `limit`: integer, minimum 1 — Max errors shown
- `query`: string — Error search query string to filter the list
- `sort`: string (last_seen_desc|last_seen_asc|times_desc|times_asc) — Sort order

### `deployments`
- `limit`: integer, minimum 1 — Max deploys shown
- `override_time`: boolean — Use `ts` instead of the dashboard's time range
- `ts`: string — Time range used when `override_time` is true

### `checkins`
- `limit`: integer, minimum 1 — Max check-ins shown
- `sort_order`: string (state_name|name|last_reported) — Sort by state, name, or last report time

### `uptime`
- `limit`: integer, minimum 1 — Max uptime monitors shown

## Timepicker tokens (`errors` widgets)

An `errors` widget's `config.query` is error search syntax, not BadgerQL, so it cannot use `@query.start_at` / `@query.end_at`. Instead, two tokens expand to the dashboard timepicker's range:

- `@ts` — the start of the range
- `@ts.end` — the end of the range

Both expand to a quoted timestamp, so use them as the value of a date key: `created.after:@ts`, `created.before:@ts.end`.

```json
{"type": "errors", "config": {"query": "-is:resolved created.after:@ts created.before:@ts.end"}}
```

When the selected range is open-ended — a relative duration like `PT3H`, or a keyword like `today` — its end is simply "now", so the entire term containing `@ts.end` is dropped rather than emitting a redundant upper bound. `created.after:@ts created.before:@ts.end` becomes `created.after:"3 hours ago"`. This means one query works for both bounded and open-ended ranges; there is no need to maintain separate widgets.

Widgets whose query contains either token re-run when the timepicker changes.

## The vis object (`insights_vis` widgets)

`config.vis` controls how the query result renders:

- `view`: string, required — one of `table`, `billboard`, `line`, `area`, `bar`, `histogram`, `scatter`, `heatmap`, `pie`
- `chart_config`: object, optional — view-specific options. For the fields each view accepts, see the **charts** instructions; do not invent fields

Example widget:

```json
{
  "type": "insights_vis",
  "presentation": {"title": "Errors Over Time"},
  "grid": {"x": 0, "y": 0, "w": 6, "h": 4},
  "config": {
    "query": "filter event_type::str == \"notice\" | stats count() as count by bin(1h)",
    "vis": {"view": "line"}
  }
}
```

## Grid layout

Dashboards use a 12-column grid:

- `x` — column offset (0–11)
- `y` — row offset (0 = top)
- `w` — width in columns (1–12)
- `h` — height in row units

Widgets must not overlap. A widget's `y` must be >= the `y + h` of any widget above it in the same columns. Side-by-side widgets in the same row share the same `y`; the next row starts at `y + h` of the tallest widget in the current row. Plan the full layout before assigning positions — overlapping or misaligned widgets render incorrectly.

Example two-column layout:

```
Row 0:  Widget A: {x:0, y:0, w:6, h:4}    Widget B: {x:6, y:0, w:6, h:4}
Row 4:  Widget C: {x:0, y:4, w:12, h:4}
Row 8:  Widget D: {x:0, y:8, w:6, h:3}    Widget E: {x:6, y:8, w:6, h:3}
```

## Validation

Dashboard structure IS validated on save: unknown keys anywhere in the dashboard, widget, config, or chart_config objects are rejected.

Widget queries are NOT validated when a dashboard is saved — a widget with a broken query silently renders empty or shows an error. Verify each query returns the expected data before saving it into a dashboard.

Widget queries may use query parameters — `${name}` or `${name:-default}` (syntax: see the **queries** instructions). Parameter values come from the dashboard URL's query parameters and apply dashboard-wide, so every widget referencing `${env}` resolves to the same value. Give each parameter the same inline default everywhere it appears; a parameter that lacks both a URL value and a default blocks that widget from running.
