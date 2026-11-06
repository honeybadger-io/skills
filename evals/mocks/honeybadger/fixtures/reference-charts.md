<!-- Generated file — do not edit by hand. -->
# Chart configuration reference

Each visualization view accepts an optional `chart_config` object — the key is named `chart_config` for every view, including views that aren't strictly charts (`table`, `billboard`). Keys must match the schema for the chosen view below. Values reference the *output aliases* produced by the query — an aggregate aliased `count` is referenced as `"count"`, not `count()`.

How the fields are packaged depends on the surface: dashboard widgets nest them in an object, query URLs flatten them into parameters. See the dashboards and queries instructions respectively — this reference only defines the fields themselves.

## table
Raw result rows and columns. No config.

## billboard
Big-number stat tiles: one tile per result row (or one per result field when `groupType` is `fields`).
- `titleField`: string — Alias shown as the tile title
- `valueField`: string — Alias shown as the big number; required when `groupType` is `events`
- `titleURLField`: string — Alias containing a URL; makes the tile title a link
- `subtitleField`: string — Alias shown below the value
- `statusField`: string — Alias whose value drives the tile's status indicator
- `groupType`: string (fields|events) — `events` (default): one tile per result row using `valueField`; `fields`: one tile per result field

## bar
Bar chart of a value per category.
- `categoryField`: string, REQUIRED — Alias for the category axis; one bar per distinct value
- `valueField`: string, REQUIRED — Alias for bar height
- `valueFieldUnit`: string — Unit used to format values: `percent`, `microseconds`, or `milliseconds`
- `labelField`: string — Alias rendered as a label on each bar
- `groupType`: string (fields|events) — `events` (default): series come from `groupField`; `fields`: every result field except `categoryField` becomes its own series
- `groupField`: string — Alias whose distinct values split bars into series (with `groupType` `events`)
- `horizontal`: boolean — Render bars horizontally
- `stacked`: boolean — Stack series instead of grouping side by side
- `groups`: object — Per-series display options keyed by series name, e.g. `{"web": {"color": "#4A90D9"}}`. Advanced — usually omit

## line
One or more series plotted over an x axis, usually time.
- `xField`: string — Alias for the x axis, typically a time bin such as `bin(1h)`
- `yField`: string — Alias plotted as the series value; required when `groupType` is `events`
- `zField`: string — Alias whose distinct values split results into one series each
- `colorField`: string — Alias whose values supply explicit series colors
- `xFieldUnit`: string — Unit used to format x values: `percent`, `microseconds`, or `milliseconds`
- `yFieldUnit`: string — Unit used to format y values: `percent`, `microseconds`, or `milliseconds`
- `groupType`: string (fields|events) — `events` (default): one series from `yField`, split by `zField` if set; `fields`: every result field except `xField` becomes its own series
- `yAxisLabel`: string — Left y-axis label (accepted but not currently applied by the renderer)
- `yAxisMin`: number — Left y-axis minimum (accepted but not currently applied by the renderer)
- `yAxisMax`: number — Left y-axis maximum (accepted but not currently applied by the renderer)
- `rightYAxisFormat`: string — Right y-axis format (accepted but not currently applied by the renderer)
- `rightYAxisLabel`: string — Right y-axis label (accepted but not currently applied by the renderer)
- `rightYAxisMin`: number — Right y-axis minimum (accepted but not currently applied by the renderer)
- `rightYAxisMax`: number — Right y-axis maximum (accepted but not currently applied by the renderer)
- `groups`: object — Per-series display options keyed by series name, e.g. `{"web": {"color": "#4A90D9"}}`; entries may also set `axis` (`left`|`right`) to plot a series on the right y axis. Advanced — usually omit

## area
Like line, with the area under each series filled; series can be stacked.
- `xField`: string — Alias for the x axis, typically a time bin such as `bin(1h)`
- `yField`: string — Alias plotted as the series value; required when `groupType` is `events`
- `zField`: string — Alias whose distinct values split results into one series each
- `groupType`: string (fields|events) — `events` (default): one series from `yField`, split by `zField` if set; `fields`: every result field except `xField` becomes its own series
- `stacked`: boolean — Stack series instead of overlaying them
- `groups`: object — Per-series display options keyed by series name, e.g. `{"web": {"color": "#4A90D9"}}`. Advanced — usually omit

## histogram
Distribution of values across buckets.
- `xField`: string, REQUIRED — Alias for the x axis
- `yField`: string, REQUIRED — Alias for the y axis
- `zField`: string — Alias whose distinct values split results into one series each
- `xFieldUnit`: string — Unit used to format x values: `percent`, `microseconds`, or `milliseconds`
- `yFieldUnit`: string — Unit used to format y values: `percent`, `microseconds`, or `milliseconds`
- `groups`: object — Per-series display options keyed by series name, e.g. `{"web": {"color": "#4A90D9"}}`. Advanced — usually omit

## scatter
Individual points plotted on two axes.
- `xField`: string, REQUIRED — Alias for the x axis
- `yField`: string, REQUIRED — Alias for the y axis
- `groupField`: string — Alias whose distinct values color the points
- `scaleField`: string — Alias that scales point size
- `groups`: object — Per-series display options keyed by series name, e.g. `{"web": {"color": "#4A90D9"}}`. Advanced — usually omit

## heatmap
Grid of cells colored by intensity. The query must sort by the x and y fields (`| sort x, y`) to render correctly.
- `xField`: string, REQUIRED — Alias for the x axis, typically a time bin such as `bin(1h)`
- `yField`: string, REQUIRED — Alias for the y axis
- `zField`: string, REQUIRED — Alias for cell value/intensity
- `yFieldUnit`: string — Unit used to format y values: `percent`, `microseconds`, or `milliseconds`
- `steps`: integer, minimum 1 — Number of color steps (default 5)
- `groups`: object — Per-series display options keyed by series name, e.g. `{"web": {"color": "#4A90D9"}}`. Advanced — usually omit

## pie
Proportional slices; one slice per result row.
- `nameField`: string, REQUIRED — Alias for slice labels
- `valueField`: string, REQUIRED — Alias for slice sizes
- `groups`: object — Per-slice display options keyed by slice name, e.g. `{"web": {"color": "#4A90D9"}}`. Advanced — usually omit
