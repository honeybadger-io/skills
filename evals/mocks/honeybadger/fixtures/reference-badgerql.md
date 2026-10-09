# BadgerQL Reference

BadgerQL is a pipe-based query language for events stored in Honeybadger Insights. Functions are joined with `|`; each function consumes the events the previous one produced.

**Schema awareness.** A caller may include event-trait schemas in the user message describing what fields exist on the events and their types. When schemas are provided, draw field names and `::type` hints from them — do not guess. When schemas are not provided, prefer discovery (`fields @preview | limit 1 by event_type::str` to inspect a sample of each event type) over guessing field types from names.

## BadgerQL Grammar

### Query Structure

A query is one or more functions combined with the pipe operator `|`:

```
fields status_code::int, controller::str
| filter status_code > 400
| stats count() as count by controller
| sort count desc
| limit 10
```

Every function after the first must be preceded by `|`. In multi-line queries, the `|` starts each new function line. Each function consumes the events produced by the previous one.

### Type Hinting

Each field's data is stored in a separate bucket per type. The `::type` hint tells BadgerQL which bucket to look in — it is not a conversion, it is a lookup directive.

```
fields status_code::int
| filter email::str like "%example.com%"
| stats avg(duration::float) by controller::str
```

Available type hints:

| Hint | Bucket |
|------|--------|
| `::int` | integer |
| `::float` | float |
| `::str` | string |
| `::bool` | boolean |

Rules of thumb:

- **Hint once.** Subsequent uses of the same field remember the hint. `filter status::int > 400 | stats count() as count by status` works.
- **Wrong hint = empty results.** If a field is stored as a float and you hint `::int`, the lookup misses and you get empty results or a type error.
- **Don't infer from output.** Check `@preview` to see how a field is actually stored before hinting.

#### Nested fields

Use dot notation: `site.name::str`, `user.id::int`.

#### Array fields

Use `[*]` to reference all elements: `tags[*]::str`. **This is always an array, even when aliased** — `tags[*]::str as tag` makes `tag` an array alias, not a scalar. To work with individual elements as scalars (so plain `==`, `<`, etc. work), use `| expand field[*]::type as alias` which unrolls the array into one event per element. To filter on a property of array elements without unrolling, wrap the predicate in `any()` or `all()`: `filter any(tags[*]::str == "fun")`.

Use a positional index `[N]` (0-based) to extract a single element: `a[0]::int` is the first element, `a[1]::int` is the second. Positional access works in `fields` clauses; use the hinted type on each reference.

#### Aliases

Use `as` to rename. Wrap aliases with spaces in backticks:

```
stats unique(user::str) as `Affected Users` by fault_id::int
```

**Pick aliases by intent, not by input.**

- When projecting a field unchanged, keep its name: `sum(bytes::int) as bytes`.
- When an aggregate has an obvious output, use the function name: `stats count() as count`, `stats avg(latency::float) as avg`.
- When the same function appears multiple times with different parameters, name by the **distinguishing parameter** — not by the input value. For example, `bin(1h) as hourly` / `bin(1d) as daily`, or `percentile(50, x) as p50` / `percentile(99, x) as p99`.
- Never bake input literals into the alias. `latency_2025_01_01` and `count_when_status_400` are anti-patterns; use `daily_latency` and `errors` instead.

## Built-in Fields

Built-in fields are prefixed with `@`. They are always available without a type hint.

| Field | Type | Description |
|-------|------|-------------|
| `@id` | string | The id of the event |
| `@ts` | datetime | The timestamp of the event |
| `@received_ts` | datetime | The timestamp when we received the event |
| `@stream.id` | string | The id of the stream |
| `@stream.name` | string | The name of the stream |
| `@size` | integer | The size (in bytes) of the event |
| `@query.start_at` | datetime | Start of the `@ts` range being queried |
| `@query.end_at` | datetime | End of the `@ts` range being queried |
| `@fill` | boolean | Whether or not result has filled in values |
| `@preview` | json_object | A preview of the query results |

## Statements

The base pipeline functions. Each consumes the events produced by the previous function and produces events for the next one.

### fields

```
fields expr [as alias][, ...]*
```

Add computed or renamed fields to each event. The expression can be any field reference or expression function.

`fields` does **not** drop unmentioned fields. Use `only` to restrict the output set.

**Don't project fields speculatively.** Only add a field that the final result outputs or that a later clause consumes. A field referenced by a downstream `filter`/`stats` is hinted at that reference directly — you don't need a leading `fields` to "set it up". A `fields` clause whose projections a later `stats` drops is dead: `fields @ts, query::str | filter query::str == "x" | stats count()` should just be `filter query::str == "x" | stats count()`.

**Pipeline statements are not valid inside `fields`.** Do not write `fields parse(x, /regex/) as y`, `fields expand(...)`, `fields fill(...)`, etc. — those are statements run at the pipeline level (`| parse x /regex/`, `| expand ...`, `| fill ...`). The expression position inside `fields` is for expression functions only.

```badgerql
fields a as b
fields duration::int / 1000 as duration_sec
fields concat(first_name::str, " ", last_name::str) as full_name
```

### filter

```
filter boolean_expr [and|or ...]*
```

Drop events that don't match the condition.

Filters can sit before or after `stats`. **After a `stats`, reference the aggregate aliases — not the original hinted fields.**

```badgerql
filter status_code::int >= 400
filter controller::str == "UsersController" and action::str == "show"
filter email::str match /.*@example\.com/
```

### stats

```
stats agg_expr[, ...]* [by [expr][, ...]*]
```

Group and aggregate. Every expression in the `agg_expr` list must use an aggregate function (`count`, `sum`, `avg`, `min`, `max`, `unique`, `percentile`, `first`, `last`, `apdex`, ...).

**Always alias aggregates.** Without `as`, the column is named after the function call expression — awkward to reference downstream.

**`stats` rewrites the fieldset — drop any `fields` it doesn't consume.** A `fields` projection upstream of a `stats` is dead unless the `stats` references it (inside an aggregate or in `by`). When building or modifying a query, remove orphaned projections: `fields @preview | stats count() by controller::str` is just `stats count() by controller::str` — the `fields @preview` is a no-op.

**After `stats`, the original hinted fields are gone** — only `by` keys and aggregate aliases survive. Subsequent `filter` or `stats` must use those aliases. **This includes `@ts`**: never write `| stats ... | sort @ts desc`, `@ts` is out of scope after the aggregation. To sort the output rows of a `stats`, sort by a `by` key or by an aggregate alias.

**`sort` BEFORE `stats` is only justified when an aggregate function reads input order — i.e. `first(...)` / `last(...)`.** Otherwise it's wasted CPU (`count`, `avg`, `sum`, `min`, `max`, `unique`, `percentile`, ... don't care about input order). "Recent" wording in the user's request maps to two different shapes:

- *Pick the latest value per group* → sort BEFORE: `sort @ts desc | stats first(X::type) as X by Y::type`.
- *Order the output rows by recency* → carry `@ts` through, sort AFTER on the alias: `stats max(@ts) as last_seen, ... by Y::type | sort last_seen desc`.

- "(count|summarize|show totals for) all events" → `stats count() as count`
- "(count|summarize|group) events by group" → `stats count() as count by group::type`
- "(show|give me|summarize) average X and event count by group" → `stats avg(field::int) as avg, count() as count by group::type`
- "(chart|trend|show) event count over time" → `stats count() as count by bin(1h) as hour`
- "(show|count|group) only the top N values of X" → `stats count() as count by top(N, field::type)`
- "(show|carry|attach) field X while grouping related events" → `stats first(field::type) as field by session_id::str`
- "(get|show|find) the most recent X per Y — latest value per group" → `sort @ts desc | stats first(X::type) as X by Y::type`
- "(show|list|rank) groups (most-recent|latest|recently active) first — sort output by recency" → `stats max(@ts) as last_seen, ... by Y::type | sort last_seen desc`

```badgerql
stats count() as count
stats count() as count by status_code::int
stats avg(duration::int) as avg, count() as count by controller::str, action::str
stats percentile(95, duration::int) as p95 by bin(1h)
```

### expand

```
expand array_field [as alias][, ...]
```

Unroll an array field into one event per element. The unrolled value takes a new alias and behaves like a scalar field downstream.

**Use `expand` when you need to filter, aggregate, or project per element.** Use `any()` / `all()` when you only need a boolean test on the array without changing event cardinality.

Multiple arrays in one `expand` zip them by index (parallel arrays, not a cartesian product). After expand, the alias is a scalar — you filter and aggregate it like any normal field.

- "(split|expand|unroll) array X into one row per item" → `expand X[*]::type as alias`
- "(split|expand|unroll) array X and then filter or aggregate each item" → `expand X[*]::type as alias | filter alias > N | stats sum(alias) as total`
- "(split|expand|unroll) arrays X and Y together by position" → `expand X[*]::type as x, Y[*]::type as y`

```badgerql
expand tags[*]::str as tag
expand nums[*]::int as num | filter num > 50
expand events[*].url::str as url
```

### fill

```
fill field_expression [as alias] [asc|desc|up|down] [from ...] [to ...] [step ...] [across field [bounded | including [...]]]* [with field[ = expression][, ...]*]
```

Insert synthetic result rows for missing values in a numeric or temporal sequence. **Reach for this when a user wants to zero-fill a time series, include empty hourly/daily bins, complete a numeric range, or carry a value forward across gaps.** Don't refuse the request — `fill` exists for exactly this.

When the fill field comes from `bin()` or `bucket()`, a bare `fill field` infers the grid from that function. `bin(1h)` supplies a 1-hour step; `bucket(x, 100)` supplies a 100-wide step; bounded `bucket(x, min, max, n)` supplies from/to/step. Explicit `from`/`to`/`step` always override inferred values.

**`across <field>` fills the cross product with another grouping dimension** — every (fill value, across value) cell exists in the result. Use for stacked charts, heatmaps, and per-category series that need explicit zeros. `across field bounded` limits each category to its own observed fill-field range; `across field including ["a", "b"]` pins values into the domain even when absent from the data. A null dimension value is a category of its own in the cross product. Counting aggregates (`count`, `sum`, `unique` and their `*If` forms) default to 0 on filled cells; everything else defaults to null; `with field = value` overrides.

Cross-fill does not support fill direction (`up`/`down`) or carry-forward `with field`; use explicit `with field = value` defaults instead. The `@fill` field marks inserted rows so generated values can be distinguished from real results.

- "(fill|zero-fill|include) empty time buckets in a time series" → `stats count() as count by bin(1h) as date | fill date`
- "(fill|zero-fill|include) empty buckets in a histogram" → `stats count() as count by bucket(field::int, 0, 1000, 20) as b | fill b`
- "(chart|show) per-category time series with explicit zeros for missing category/time cells" → `stats count() as count by bin(1h) as t, category::str | fill t across category`
- "(fill|complete) every category and time cell, pinning categories even when absent" → `stats count() as count by bin(1h) as t, op::str | fill t across op including ["create", "delete"]`
- "(fill|complete) each category only within its own active period" → `stats count() as count by bin(1h) as t, sensor::str | fill t across sensor bounded`
- "(fill|complete|add) every number from A to B with a default value" → `fields field::type, number::int | fill number from A to B with field = "default"`
- "(fill|carry forward|forward-fill) X across missing numbers from A to B" → `fields field::type, number::int | fill number up from A to B with field`
- "(fill|complete|extend) missing numbers up to N" → `fields field::type, number::int | fill number to N`

```badgerql
fill bin
fill bin step 1h
fill number to 100
fill number from 0 to 5 with controller = "unknown"
fill number up from 1 to 5 with controller
```

### limit

```
limit integer [by expr[, ...]*]
```

Cap the number of returned events. **Always pair with `sort`** — `limit` without a sort is non-deterministic.

With a `by` clause, `limit` caps events per group. **The `by` clause accepts boolean expressions, not just fields**, so you can cap per (group, predicate-bucket) instead of writing two separate filtered queries.

- "(show|give me|list) the top N events after sorting by X" → `sort field::type desc | limit N`
- "(show|keep|limit to) N events per group" → `limit N by group::type`
- "(show|keep|limit to) N events per group and condition bucket" → `limit N by group::type, field::int > threshold`

```badgerql
limit 25
limit 5 by controller::str
```

### only

```
only expr [as alias][, ...]*
```

Restrict and order the final output columns. **Drops every column not listed** (unlike `fields`, which keeps the rest).

Use to keep responses small and focused.

```badgerql
only @ts, controller, status_code, duration
```

### parse

```
parse expr /regex/
```

Extract fields from a string using named capture groups. **`parse` is a statement, not an expression function** — write it at the pipeline level (`| parse field /regex/`), never inside `fields` or `filter`. There is no `parse(field, /regex/)` expression form; SQL's `regexp_extract` and similar do not exist. **Regex is RE2 syntax**, not PCRE.

**`parse` is the BadgerQL pattern for pattern-based string extraction.** BadgerQL has `substring(string, start, length)` for fixed-position slicing, but no `indexOf`, `lastIndexOf`, `instr`, or `substr` — any "first word", "everything before X", "Nth field of a delimited string" intent that needs to *find* a position is solved with a regex capture, not string-position math.

Each named capture becomes a new field on the event, accessible by its capture name. Non-matching captures yield `null`.

- "(extract|pull|get) value from text X using regex" → `parse field::str /regex/`
- "(parse|extract|pull) named field from X with regex" → `parse X::str /(?<name>...)/`
- "(show|give me|get) the captured value from X" → `parse X::str /(?<name>regex)/ | fields name`
- "(split|break up|extract) text X into named fields" → `parse field::str /(?<part1>...)(?<part2>...)/`
- "(show|give me|get) the first word from X" → `parse X::str /^(?<first>\w+)/`
- "(show|give me|get) everything before the period in X" → `parse X::str /^(?<before>[^.]*)\./`

```badgerql
parse controller::str /(?<prefix>\w+)Controller/
```

### sort

```
sort expr [desc|asc][, ...]*
```

Order events. **Direction defaults to descending** — `sort field` is equivalent to `sort field desc`. Use `asc` explicitly for ascending order. Pair with `limit` to take the top N.

- "(sort|order) events by X largest first" → `sort field::type`
- "(sort|order) events by X smallest first" → `sort field::type asc`
- "(sort|order) events by X and then Y" → `sort field_a::type asc, field_b::type desc`
- "(show|give me|list) the top N events sorted by X" → `sort field::type desc | limit N`

```badgerql
sort count
sort created_at asc
sort count desc, name asc
```

### unique

```
unique field[, ...]
```

**`unique` is a pipeline statement** that deduplicates events by one or more fields — distinct from the `unique()` aggregate, which counts distinct values.

Use the statement form when the user wants distinct combinations of fields preserved as event-shaped rows. Don't reconstruct it with `stats unique(concat(toString(a), ",", b))` — the statement form preserves the original event shape.

**`unique` deduplicates but does not project.** To show the distinct values themselves, project the field first: `fields X::type | unique X`. `unique X::type` alone dedupes the events but leaves X out of the output.

- "(show|keep|list) the distinct values of X" → `fields field::type | unique field`
- "(show|keep|list) the distinct combinations of X and Y" → `fields field_a::type, field_b::type | unique field_a, field_b`

```badgerql
fields controller::str | unique controller
fields controller::str, action::str | unique controller, action
```

## Expression Functions: Quick Reference
Common functions you can use inside `fields`, `filter`, and `stats` expressions. Each entry shows its signature; notes call out the traps LLMs trained on SQL tend to hit.
- **t between t and t -> boolean** — Use infix form, not function-call form. Both bounds are inclusive.
  - "(find|show|filter to) events where X is between A and B" → `filter field::int between A and B`
  - "(find|show|filter to) events that happened between START and END" → `filter @ts between START and END`
- **isNotNull(t) -> boolean** — Function-call form, not infix. SQL's `field is not null` is not valid BadgerQL.
  - "(find|show|filter to) events where X is present" → `filter isNotNull(field::type)`
- **isNull(t) -> boolean** — Function-call form, not infix. SQL's `field is null` is not valid BadgerQL.
  - "(find|show|filter to) events where X is missing or null" → `filter isNull(field::type)`
- **any(boolean) -> boolean** — Wraps an array predicate. SQL-trained models often write `field[*]::type == value` directly — that's a type error because `field[*]::type` is an array. Always wrap the predicate. Returns false on empty arrays.
  - "(find|show|filter to) events where any item in X equals Y" → `filter any(X[*]::type == Y)`
  - "(find|show|filter to) events where any item in X is one of A or B" → `filter any(X[*]::type in [A, B])`
  - "(find|show|filter to) events where any number in X is greater than N" → `filter any(X[*]::int > N)`
  - "(find|show|filter to) events where any object in X has field equal to Y" → `filter any(X[*].field::type == Y)`
  - "(show|list|keep) X values from events where any X equals Y" → `fields X[*]::type as X | filter any(X == Y) | only X`
- **all(boolean) -> boolean** — Like `any()` but requires every element to match. Same wrapping rule applies. Returns true on empty arrays (vacuous truth).
  - "(find|show|filter to) events where every item in X equals Y" → `filter all(X[*]::type == Y)`
  - "(find|show|filter to) events where every number in X is between A and B" → `filter all(X[*]::int between A and B)`
  - "(find|show|filter to) events where every object in X has field equal to Y" → `filter all(X[*].field::type == Y)`
- **t in t[] -> boolean** — Right-hand side must be a literal array. Subqueries are not supported. The array element type must match the field type.
  - "(find|show|filter to) events where X is one of A, B, or C" → `filter field::type in [A, B, C]`
  - "(hide|exclude|drop) events where X is A or B" → `filter field::type not in [A, B]`
- **either(t, ...t) -> t** — Returns the first non-null value. Args must share a type; wrap with conversion functions to unify. SQL's `coalesce` is accepted too.
  - "(use|show|pick) the first present value from X, Y, or Z" → `either(a::type, b::type, c::type)`
  - "(use|show|pick) the first present numeric value and make it an integer" → `either(toInt(str::str), int::int, toInt(float::float))`
- **string like string -> boolean** — SQL-style wildcards inside a quoted string: `%` matches any characters, `_` matches one. Case-sensitive — use `ilike` for case-insensitive. For regex matching, use `match`.
  - "(find|show|filter to) events where X contains pattern" → `filter field::str like "%pattern%"`
  - "(find|show|filter to) events where X starts with prefix" → `filter field::str like "prefix%"`
- **string match regex -> boolean** — Right-hand side is a regex literal between forward slashes, not a quoted string. Uses RE2 syntax. For SQL-style wildcards, use `like` instead.
  - "(find|show|filter to) events where X matches regex" → `filter field::str match /regex/`
  - "(find|show|filter to) events where X matches option1 or option2" → `filter field::str match /(option1|option2)/`
- **if(condition, then, else)** — Three-arg function, not a Python/JS ternary. For multi-branch logic use `cond` instead of nested `if`s.
  - "(show|make|add) one value when a condition matches and another when it does not" → `if(cond, then_value, else_value)`
  - "(label|bucket|mark) events as high or low based on X" → `if(field::int > N, "high", "low")`
- **cond(boolean, t, boolean, t, ..., t) -> t** — Multi-branch conditional: pairs of (test, value) followed by a single default value. Replaces SQL `CASE WHEN ... THEN ... ELSE ... END`.
  - "(label|bucket|group) events across multiple conditions with a default" → `cond(test1, value1, test2, value2, default)`
  - "(label|bucket|group) X into high, medium, or low ranges" → `cond(x > 100, "high", x > 50, "medium", "low")`
- **round(number, literal integer) -> float** — Optional second argument is the number of decimal places (default 0). `round(x)` rounds to the nearest integer; `round(x, 2)` rounds to two decimals. `floor` and `ceil` take the same optional precision argument.
  - "(round) X to the nearest integer" → `round(x::float)`
  - "(round) X to N decimal places" → `round(x::float, N)`
- **bucket(value, width) or bucket(value, min, max, n)** — BadgerQL's numeric histogram primitive — `bin()` buckets time, `bucket()` buckets numbers. Width form uses a fixed width anchored at zero. Bounded form divides a fixed range into N bucket slots and clips out-of-range values to null. `bucket()` assigns events to bucket keys; add `fill` to show empty buckets. All parameters are literals — there is no auto-ranged histogram function.
  - "(show|chart|give me) a histogram of X in buckets of width W" → `stats count() as count by bucket(field::int, W) as b | fill b | sort b asc`
  - "(show|chart|give me) a histogram of X from MIN to MAX in N buckets" → `stats count() as count by bucket(field::int, MIN, MAX, N) as b | fill b | sort b asc`
- **toInt(any) -> integer** — Convert any expression to an integer. Use when you need a string-to-integer coercion. The reverse — turning an integer into a string for display — is `toString()`, not `toInt()`.
  - "(turn|convert|cast) X into an integer" → `toInt(field::str)`
  - "(use|show|pick) the first present value from mixed numeric fields as an integer" → `either(toInt(str::str), int::int, toInt(float::float))`
- **toString(any) -> string** — Required when interpolating non-string values into `concat()`. SQL's `CAST(x AS VARCHAR)` is not valid BadgerQL.
  - "(turn|convert|cast) X into text for display" → `toString(field::type)`
  - "(build|make|show) text that includes numeric X" → `concat("prefix-", toString(field::int))`
- **toHour(datetime) -> integer** — Returns the 24-hour number (0-23) from a datetime. Use for "by hour of day" grouping. Do not reach for `formatDate("%H", @ts)` (returns a string) or `bin(1h)` (returns time buckets, not hour-of-day).
  - "(show|count|group) events by hour of day" → `stats count() as count by toHour(@ts) as hour`
- **formatDate(format, date)** — Argument order is format first, datetime second. The reverse is wrong but common in SQL-trained models. Date argument defaults to `@ts` if omitted.
  - "(show|format|display) the event timestamp as YYYY-MM-DD text" → `formatDate("%Y-%m-%d", @ts)`
  - "(show|format|display) event timestamps as YYYY-MM-DD text" → `formatDate("%Y-%m-%d")`
- **bin(interval, datetime = `@ts`) -> datetime** — BadgerQL's time-bucketing function. Use a fixed interval for a specific bucket size, or no args to let BadgerQL auto-size from the query's time window. Datetime is inferred from `@ts` by default. SQL's `date_trunc`, ClickHouse's `toStartOfInterval`, and `time_bucket` do not exist here.
  - "(chart|trend|show) event volume over time with automatic buckets" → `stats count() as count by bin() as bin`
  - "(chart|trend|show) event volume over time in 1 hour buckets" → `stats count() as count by bin(1h) as hour`
- **urlPath(string) -> string** — Extracts the path from a URL string. Use for "give me the path from this URL" — don't reach for `parse` with a regex.
- **urlDomain(string) -> string** — Extracts the hostname/domain from a URL string. Use for "give me the domain from this URL" — don't reach for `parse` with a regex.
- **json(string, path)** — Extract a scalar value from a JSON string using a JSONPath expression. Use when a field is JSON text and you need a value inside it. Returns null for non-scalar paths (arrays, objects).
  - "(get|pull|show) a value inside JSON text field X" → `json(field::str, "$.path.to.value")`
- **concat(string, string...) -> string** — All arguments must be strings. Wrap non-strings in `toString(...)` first.
  - "(join|combine|merge) text fields X and Y" → `concat(a::str, "-", b::str)`
  - "(build|make|show) text that includes numeric X" → `concat("prefix-", toString(field::int))`
- **substring(string, start, length)** — Fixed-position string slicing. Positions are 1-indexed (`substring(s, 1, 3)` returns the first three characters). For pattern-based extraction where you need to *find* a position, use the `parse` statement with a regex instead.
  - "(take|get|extract) the first N characters of X" → `fields substring(field::str, 1, N) as prefix`
  - "(take|get|extract) N characters starting at position P" → `fields substring(field::str, P, N)`
- **replace(string, match, replacement)** — Replace every occurrence of a substring (string match arg) or pattern (regex `/.../` match arg) with another string. Returns the rewritten string; project it under whatever alias makes sense.
  - "(replace|swap|change) every X with Y in field" → `fields replace(field::str, "X", "Y") as field`
  - "(strip|remove|drop) a regex pattern from field" → `fields replace(field::str, /pattern/, "") as field`
- **toHumanString(num, type)** — Format a number as a human-readable string with unit handling. Don't build the human format manually with `concat`/`toString`/division — this function handles unit-suffix logic for you.
  - "(show|format|display) byte count X as a readable size" → `toHumanString(field::int, "bytes")`
  - "(show|format|display) millisecond duration X as readable time" → `toHumanString(field::int, "milliseconds")`
  - "(show|format|display) microsecond duration X as readable time" → `toHumanString(field::int, "microseconds")`
  - "(show|format|display) large number X with a short suffix" → `toHumanString(field::float, "short")`
- **count(string) -> integer** — Three forms: no-arg counts events, with a field counts non-null occurrences, with a predicate counts events where it's true. Use the predicate form instead of SQL's `sum(case when ... then 1 else 0 end)` pattern.
  - "(count|show me) all events" → `count()`
  - "(count|show me) events where X is present" → `count(field::type)`
  - "(count|show me) events where X is greater than N" → `count(field::int > N)`
- **percentile(percent, value)** — There is no `p95(x)` or `p99(x)` shorthand. The percent goes first (0-100), the value second (must be numeric — `::str` is a type error). Result is approximated.
  - "(show|give me|find) the Nth percentile of X" → `stats percentile(N, field::int) as pN`
- **unique(t) -> integer** — This is the count-distinct aggregate. SQL's `count(distinct ...)` is not valid BadgerQL — use this instead.
  - "(count|show me) how many unique X values there are" → `stats unique(field::type) as count`
  - "(count|show me) unique X values per group" → `stats unique(field::type) as count by group::type`
- **min(t) -> t**
- **max(t) -> t**
- **sum(number) -> number** — Argument must be numeric. `::str` is a type error — re-hint the field as numeric.
  - "(sum|total|add up) X across events" → `stats sum(field::int) as total`
- **avg(number) -> number** — Argument must be numeric. `::str` is a type error — pick `::int` or `::float` for the argument regardless of how the field name reads.
  - "(average|show average|give me average) X across events" → `stats avg(field::int) as avg`
  - "(average|show average|give me average) X per group" → `stats avg(field::float) as avg by group::type`
- **first(t) -> t** — Returns whichever value happened to be encountered first. Skips nulls — useful for projecting fields across event types when grouping by a shared key. Order is non-deterministic without a prior `sort`.
- **last(t) -> t** — Returns whichever value happened to be encountered last. Same null-skipping and ordering semantics as `first`.
- **apdex(responseTime, threshold)** — Threshold is in the same units as the response-time argument. If the field is microseconds, the threshold is microseconds. Mismatched units are a frequent foot-gun.
  - "(show|calculate|get) apdex for duration X with a 200ms target when X is in microseconds" → `stats apdex(duration::int, 200000) as score`
  - "(show|calculate|get) apdex for duration X with a 200ms target when X is in milliseconds" → `stats apdex(duration::int, 200) as score`
- **pickMax(value, selector)** — Replaces SQL's `argMax` / sort-and-limit-1 patterns. `pickMax(value, @ts)` returns the value from the most recent event in each group.
  - "(show|get|find) the most recent X per group" → `stats pickMax(X::type, @ts) as X by group::type`
  - "(show|get|find) the X with the largest Y per group" → `stats pickMax(X::type, Y::int) as X by group::type`
- **countIf(predicate)** — Canonical conditional count. Part of the `*If` family (`sumIf`, `avgIf`, `minIf`, `maxIf`, `uniqueIf`, ...) — use these instead of SQL's `sum(case when ... then 1 else 0 end)` or `FILTER (WHERE ...)` patterns.
  - "(count|show me) events where X is greater than N" → `stats countIf(field::int > N) as count`
- **sumIf(value, predicate)** — Conditional sum: value first, predicate second. Use instead of SQL's `sum(case when pred then x else 0 end)`.
  - "(sum|total|add up) X for events where Y matches" → `stats sumIf(field::int, other::type == value) as total`
- **avgIf(value, predicate)** — Conditional average: value first, predicate second. Events where the predicate is false are excluded entirely; they do not count as zeroes.
- **rate(aggregate[, interval])** — Bin-aware rates. Divides an aggregate by the surrounding `bin()` width, so the result stays a true per-second (or per-interval) rate when the bin size changes. Use instead of dividing by a hand-written constant like `count() / 60`.
  - "(chart|show|trend) requests or events per second over time" → `stats rate(count()) as rps by bin(1m) as t`
  - "(chart|show|trend) bytes or throughput per second over time" → `stats rate(sum(bytes::int)) as bps by bin(1m) as t`
  - "(chart|show|trend) events per minute over time" → `stats rate(count(), 1m) as rpm by bin(1h) as t`
- **top(literal integer, t, any = null) -> t[] | t** — Context-aware — pick the position by intent. Plain equality `field == top(N, field)` is not valid.
  - "(show|count|list) the top N values of X" → `stats count() as count by top(N, X)`
  - "(keep|show|filter to) events where X is in the top N values" → `filter X in top(N, X)`
  - "(show|list|give me) X from events where X is in the top N values" → `filter X in top(N, X) | fields X`
  - "(hide|exclude|drop) events where X is in the top N values" → `filter X not in top(N, X)`
  - "(show|list|give me) the top N X values for each group" → `stats top(N, X) by group`
  - "(show|list|give me) the top N X values as a list" → `stats top(N, X)`
  - "(show|list|give me) the top N X values ranked by Y" → `stats count() as count by top(N, X, max(Y))`
  - "(chart|trend|graph) the top N X values over time" → `filter X in top(N, X) | stats count() as count by bin(1h), X`

## Expression Functions: Other Traps
- `ilike` — Case-insensitive form of `like`. Same SQL wildcards (`%`, `_`).
- `uniqueIf` — Conditional count-distinct: value first, predicate second. SQL's `count(distinct ...) filter (where ...)` is not valid BadgerQL.
- `percentileIf` — Conditional percentile with the same leading arguments as `percentile`: percent first (0-100), value second, predicate last.
- `apdexIf` — Apdex over a filtered slice. The predicate gates the denominator too, so the score only reflects matching events. Threshold units must match the response-time argument, same as `apdex`.

## Rules

### Pipeline shape

- **Every function after the first is preceded by `|`.** In multi-line queries the `|` opens the next line.
- **Aggregate functions are aliased.** Write `stats count() as count`, not `stats count()`. The unaliased column name is literally `count()`, which downstream `sort` / `filter` cannot reference cleanly.
- **`limit` follows a `sort`.** A `limit` without `sort` returns a non-deterministic subset.
- **Negate operators inline, not by wrapping.** Use `not between`, `not in`, `not like`, `not match` — never `not (x between ...)` or `not (x in [...])`. The parser does not accept a parenthesized negation of these operators.

### Types and fields

- **Type hints are storage-bucket lookups.** Use `::int` for whole numbers, `::float` for decimals, `::str` for strings, `::bool` for booleans. A wrong hint returns empty results.
- **Every field reference needs a hint on first use.** A bare `field` (no `::type`) in `fields`, `filter`, or `stats` is a "missing type hint" error. Hint each new field once when it first appears: `fields user_id::str`, then later `filter user_id == "x"` works because the hint is remembered.
- **Hint once per field per query.** Subsequent uses of the same field reuse the hint.
- **The hint must appear on the field reference, not on an enclosing function.** Conversion and aggregate functions (`toInt`, `toFloat`, `toString`, `count`, `sum`, ...) do **not** supply a hint to the field they wrap. Write `toInt(b::str)`, not `toInt(b)`.
- **After `stats`, reference aliases.** The hinted source fields are consumed by the aggregation. Downstream `filter` and `stats` must reference the aliases produced by the upstream `stats`.

### Discovery before analysis

- **Inventory event types first** with `stats count() as count by event_type::str`.
- **Inspect fields with one call**: `fields @preview | limit 1 by event_type::str`. Pick type hints from what `@preview` actually shows.
- **Don't probe for fields with `filter isNotNull(field::str)`.** Run `@preview` instead.

### Aggregation hygiene

- **`bin()` defaults to auto-sized buckets.** Pass an explicit interval like `bin(1h)` when you want a predictable bucket size.
- **Cap high-cardinality groups** with `top(N, field)` in the `by` clause, or with `| sort ... | limit N` after the `stats`.
- **`first()` and `last()` skip nulls.** Use them to project a field that lives on one event type from a group keyed by a shared id (cross-event correlation).

### Output

- **End queries with `sort` + `limit`** unless they are naturally bounded (e.g. time-bucketed).
- **Use `only` to drop columns** you don't need in the result.
- **Project the fields the user named.** `filter`, `limit`, and `unique` do **not** add fields to the output — an event keeps only internal metadata (`@ts`, `@id`, ...) unless a `fields` or `only` clause names the fields. Whenever the request mentions a field by name or by role, add a leading `fields` clause naming it, even if a later `filter`/`limit`/`unique` also references it. Example: "show the `num` of rows where num is negative" is `fields num::int | filter num < 0`, not `filter num::int < 0` alone.
- **Answer with a query, not a question.** Write a best-effort BadgerQL query using the field names as given in the request. Never respond by asking for clarification or for field names — take the names the request supplies at face value.
