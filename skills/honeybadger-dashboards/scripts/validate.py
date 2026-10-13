#!/usr/bin/env python3
"""Check a proposed Honeybadger Insights dashboard before it is saved.

usage: python3 -I validate.py proposed.json [--before before.json]

proposed.json is the dashboard to save: {"title", "default_ts", "widgets"}.
before.json is the get_dashboard output of the dashboard being updated; with it,
the script lists the widgets that will be added, changed, and removed.

Prints errors, then warnings, then the diff. Exits 1 when there are errors.
Standard library only.
"""

import argparse
import json
import re
import sys

# ---------------------------------------------------------------------------
# Allowed keys. This table mirrors the `dashboards` and `charts` topics of the
# Honeybadger MCP server's get_reference tool. When they disagree, the live
# reference wins: update this table, not the dashboard.
# ---------------------------------------------------------------------------

GRID_COLUMNS = 12
MAX_TEXT = 255
WIDGET_WARN_COUNT = 30  # more than this has been rejected on save

DASHBOARD_KEYS = {"title", "default_ts", "widgets"}
# Present in get_dashboard output; ignored on save.
DASHBOARD_READ_ONLY_KEYS = {"id", "url", "created_at", "updated_at", "project_id", "is_default", "shared"}

WIDGET_KEYS = {"type", "id", "grid", "presentation", "config"}
GRID_KEYS = {"x", "y", "w", "h"}
PRESENTATION_KEYS = {"title", "subtitle"}

CONFIG_KEYS = {
    "insights_vis": {"streams", "query", "vis"},
    "alarms": {"limit", "filter_state"},
    "errors": {"limit", "query", "sort"},
    "deployments": {"limit", "override_time", "ts"},
    "checkins": {"limit", "sort_order"},
    "uptime": {"limit"},
}
CONFIG_ENUMS = {
    ("alarms", "filter_state"): {"all", "triggered", "ok"},
    ("errors", "sort"): {"last_seen_desc", "last_seen_asc", "times_desc", "times_asc"},
    ("checkins", "sort_order"): {"state_name", "name", "last_reported"},
}
STREAMS = {"default", "internal"}

VIS_KEYS = {"view", "chart_config"}
GROUP_TYPES = {"fields", "events"}
UNITS = {"percent", "microseconds", "milliseconds"}

# view -> (allowed chart_config keys, keys required whatever the groupType)
CHART_CONFIG = {
    "table": (set(), set()),
    "billboard": ({"titleField", "valueField", "titleURLField", "subtitleField", "statusField", "groupType"}, set()),
    "bar": ({"categoryField", "valueField", "valueFieldUnit", "labelField", "groupType", "groupField",
             "horizontal", "stacked", "groups"}, {"categoryField", "valueField"}),
    "line": ({"xField", "yField", "zField", "colorField", "xFieldUnit", "yFieldUnit", "groupType",
              "yAxisLabel", "yAxisMin", "yAxisMax", "rightYAxisFormat", "rightYAxisLabel", "rightYAxisMin",
              "rightYAxisMax", "groups"}, set()),
    "area": ({"xField", "yField", "zField", "groupType", "stacked", "groups"}, set()),
    "histogram": ({"xField", "yField", "zField", "xFieldUnit", "yFieldUnit", "groups"}, {"xField", "yField"}),
    "scatter": ({"xField", "yField", "groupField", "scaleField", "groups"}, {"xField", "yField"}),
    "heatmap": ({"xField", "yField", "zField", "yFieldUnit", "steps", "groups"}, {"xField", "yField", "zField"}),
    "pie": ({"nameField", "valueField", "groups"}, {"nameField", "valueField"}),
}
# Required only when groupType is "events" (the default when groupType is absent).
EVENTS_REQUIRED = {"billboard": "valueField", "line": "yField", "area": "yField"}
UNIT_KEYS = {"valueFieldUnit", "xFieldUnit", "yFieldUnit"}

# Event types Honeybadger generates; they live on the internal stream.
INTERNAL_EVENTS = re.compile(r"\b(notice|deploy|uptime_check|check_in)\b")

# ---------------------------------------------------------------------------


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def widget_name(widget, index):
    presentation = widget.get("presentation") if isinstance(widget, dict) else None
    title = presentation.get("title") if isinstance(presentation, dict) else None
    label = f"widget {index}"
    if title:
        label += f' "{title}"'
    return label


def load(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and set(data) == {"dashboard"}:
        data = data["dashboard"]
    return data


def check(dashboard):
    """Return (errors, warnings) for one dashboard object."""
    errors, warnings = [], []
    if not isinstance(dashboard, dict):
        return ["dashboard must be a JSON object"], warnings

    for key in sorted(set(dashboard) - DASHBOARD_KEYS - DASHBOARD_READ_ONLY_KEYS):
        errors.append(f"dashboard: unknown key {key!r}")
    title = dashboard.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("dashboard: title is required")
    elif len(title) > MAX_TEXT:
        errors.append(f"dashboard: title is {len(title)} characters, max {MAX_TEXT}")
    if "default_ts" in dashboard and dashboard["default_ts"] is not None and not isinstance(dashboard["default_ts"], str):
        errors.append("dashboard: default_ts must be a string")

    widgets = dashboard.get("widgets")
    if not isinstance(widgets, list):
        errors.append("dashboard: widgets must be an array")
        return errors, warnings
    if len(widgets) > WIDGET_WARN_COUNT:
        warnings.append(f"{len(widgets)} widgets; dashboards with more than {WIDGET_WARN_COUNT} have been rejected on save")

    occupied = {}
    for i, widget in enumerate(widgets):
        name = widget_name(widget, i)
        if not isinstance(widget, dict):
            errors.append(f"{name}: must be a JSON object")
            continue
        for key in sorted(set(widget) - WIDGET_KEYS):
            errors.append(f"{name}: unknown key {key!r}")
        wtype = widget.get("type")
        if wtype not in CONFIG_KEYS:
            errors.append(f"{name}: type must be one of {', '.join(sorted(CONFIG_KEYS))} (got {wtype!r})")
        if "id" in widget and not (isinstance(widget["id"], str) and widget["id"]):
            errors.append(f"{name}: id must be a non-empty string when present")

        check_presentation(widget.get("presentation"), name, errors)
        check_grid(widget.get("grid"), name, i, occupied, errors)
        if wtype in CONFIG_KEYS:
            check_config(widget.get("config"), wtype, name, errors, warnings)
    return errors, warnings


def check_presentation(presentation, name, errors):
    if presentation is None:
        return
    if not isinstance(presentation, dict):
        errors.append(f"{name}: presentation must be an object")
        return
    for key in sorted(set(presentation) - PRESENTATION_KEYS):
        errors.append(f"{name}: unknown presentation key {key!r}")
    for key in PRESENTATION_KEYS:
        value = presentation.get(key)
        if value is None:
            continue
        if not isinstance(value, str):
            errors.append(f"{name}: presentation.{key} must be a string")
        elif len(value) > MAX_TEXT:
            errors.append(f"{name}: presentation.{key} is {len(value)} characters, max {MAX_TEXT}")


def check_grid(grid, name, index, occupied, errors):
    if grid is None:
        return
    if not isinstance(grid, dict):
        errors.append(f"{name}: grid must be an object")
        return
    for key in sorted(set(grid) - GRID_KEYS):
        errors.append(f"{name}: unknown grid key {key!r}")
    missing = sorted(GRID_KEYS - set(grid))
    if missing:
        errors.append(f"{name}: grid is missing {', '.join(missing)}")
        return
    if not all(is_int(grid[k]) for k in GRID_KEYS):
        errors.append(f"{name}: grid x, y, w, h must be integers")
        return
    x, y, w, h = (grid[k] for k in ("x", "y", "w", "h"))
    if x < 0 or y < 0 or w < 1 or h < 1:
        errors.append(f"{name}: grid needs x >= 0, y >= 0, w >= 1, h >= 1")
        return
    if x + w > GRID_COLUMNS:
        errors.append(f"{name}: grid x {x} + w {w} exceeds {GRID_COLUMNS} columns")
    for col in range(x, min(x + w, GRID_COLUMNS)):
        for row in range(y, y + h):
            other = occupied.get((col, row))
            if other is not None:
                errors.append(f"{name}: overlaps {other} at column {col}, row {row}")
                return
    for col in range(x, min(x + w, GRID_COLUMNS)):
        for row in range(y, y + h):
            occupied[(col, row)] = name


def check_config(config, wtype, name, errors, warnings):
    if config is None:
        config = {}
    if not isinstance(config, dict):
        errors.append(f"{name}: config must be an object")
        return
    for key in sorted(set(config) - CONFIG_KEYS[wtype]):
        errors.append(f"{name}: unknown config key {key!r} for type {wtype}")
    for (etype, key), allowed in CONFIG_ENUMS.items():
        if etype == wtype and key in config and config[key] not in allowed:
            errors.append(f"{name}: config.{key} must be one of {', '.join(sorted(allowed))}")
    if "limit" in config and (not is_int(config["limit"]) or config["limit"] < 1):
        errors.append(f"{name}: config.limit must be an integer >= 1")
    if wtype == "insights_vis":
        check_insights_vis(config, name, errors, warnings)


def check_insights_vis(config, name, errors, warnings):
    query = config.get("query")
    if not isinstance(query, str) or not query.strip():
        errors.append(f"{name}: insights_vis widgets need a non-empty query")
        query = ""
    streams = config.get("streams")
    if streams is not None:
        if not isinstance(streams, list) or not all(isinstance(s, str) for s in streams):
            errors.append(f"{name}: streams must be an array of stream slugs")
            streams = None
        else:
            for slug in sorted(set(streams) - STREAMS):
                errors.append(f"{name}: unknown stream {slug!r} (slugs are {', '.join(sorted(STREAMS))})")
    if INTERNAL_EVENTS.search(query) and (not streams or "internal" not in streams):
        warnings.append(f"{name}: the query mentions a Honeybadger event but streams lacks \"internal\", so it will read none of them")
    if "${" in query:
        warnings.append(f"{name}: the query has parameters; query_insights does not expand them, so test with the values substituted")

    vis = config.get("vis")
    if not isinstance(vis, dict):
        errors.append(f"{name}: insights_vis widgets need vis with a view")
        return
    for key in sorted(set(vis) - VIS_KEYS):
        errors.append(f"{name}: unknown vis key {key!r}")
    view = vis.get("view")
    if view not in CHART_CONFIG:
        errors.append(f"{name}: vis.view must be one of {', '.join(sorted(CHART_CONFIG))} (got {view!r})")
        return
    chart_config = vis.get("chart_config")
    if chart_config is None:
        chart_config = {}
    if not isinstance(chart_config, dict):
        errors.append(f"{name}: chart_config must be an object")
        return
    allowed, required = CHART_CONFIG[view]
    for key in sorted(set(chart_config) - allowed):
        errors.append(f"{name}: chart_config key {key!r} is not valid for view {view}")
    for key in sorted(required - set(chart_config)):
        errors.append(f"{name}: view {view} requires chart_config.{key}")
    group_type = chart_config.get("groupType")
    if group_type is not None and group_type not in GROUP_TYPES:
        errors.append(f"{name}: chart_config.groupType must be fields or events")
    needed = EVENTS_REQUIRED.get(view)
    if needed and needed not in chart_config:
        if group_type == "events":
            errors.append(f"{name}: view {view} with groupType events requires chart_config.{needed}")
        elif group_type is None:
            warnings.append(f"{name}: view {view} defaults to groupType events, which needs chart_config.{needed}; set groupType to fields for one series or tile per column")
    for key in UNIT_KEYS & set(chart_config):
        if chart_config[key] not in UNITS:
            errors.append(f"{name}: chart_config.{key} must be one of {', '.join(sorted(UNITS))}")
    if "steps" in chart_config and (not is_int(chart_config["steps"]) or chart_config["steps"] < 1):
        errors.append(f"{name}: chart_config.steps must be an integer >= 1")
    for key in ("stacked", "horizontal"):
        if key in chart_config and not isinstance(chart_config[key], bool):
            errors.append(f"{name}: chart_config.{key} must be true or false")
    if "groups" in chart_config and not isinstance(chart_config["groups"], dict):
        errors.append(f"{name}: chart_config.groups must be an object keyed by series name")


def diff(before, after):
    """Return (errors, lines): id problems, and the added/changed/removed widgets."""
    errors, lines = [], []
    old = {w["id"]: (i, w) for i, w in enumerate(before.get("widgets") or []) if isinstance(w, dict) and w.get("id")}
    seen = set()
    added, changed, same = [], [], 0
    for i, widget in enumerate(after.get("widgets") or []):
        if not isinstance(widget, dict):
            continue
        name = widget_name(widget, i)
        wid = widget.get("id")
        if not wid:
            added.append(name)
            continue
        if wid in seen:
            errors.append(f"{name}: id {wid!r} appears twice; the second copy would be a duplicate")
            continue
        seen.add(wid)
        if wid not in old:
            errors.append(f"{name}: id {wid!r} is not on the existing dashboard; leave id off a new widget")
            continue
        if old[wid][1] == widget:
            same += 1
        else:
            changed.append(name)
    removed = [widget_name(w, i) for wid, (i, w) in old.items() if wid not in seen]
    if "title" in before and before.get("title") != after.get("title"):
        lines.append(f"title: {before.get('title')!r} -> {after.get('title')!r}")
    if before.get("default_ts") != after.get("default_ts"):
        lines.append(f"default_ts: {before.get('default_ts')!r} -> {after.get('default_ts')!r}")
    lines.append(f"added ({len(added)}): " + (", ".join(added) or "none"))
    lines.append(f"changed ({len(changed)}): " + (", ".join(changed) or "none"))
    lines.append(f"removed ({len(removed)}): " + (", ".join(removed) or "none"))
    lines.append(f"unchanged: {same}")
    return errors, lines


def run(proposed_path, before_path=None):
    """Validate and return (exit code, output lines)."""
    out = []
    try:
        proposed = load(proposed_path)
    except (OSError, ValueError) as e:
        return 1, [f"error: cannot read {proposed_path}: {e}"]
    errors, warnings = check(proposed)
    diff_lines = []
    if before_path:
        try:
            before = load(before_path)
        except (OSError, ValueError) as e:
            return 1, [f"error: cannot read {before_path}: {e}"]
        if not isinstance(before, dict):
            return 1, [f"error: {before_path} is not a dashboard object"]
        diff_errors, diff_lines = diff(before, proposed)
        errors.extend(diff_errors)
    elif isinstance(proposed, dict) and any(isinstance(w, dict) and w.get("id") for w in proposed.get("widgets") or []):
        warnings.append("some widgets have ids but no --before dashboard was given; ids must come from the dashboard being updated")

    out.extend(f"error: {e}" for e in errors)
    out.extend(f"warning: {w}" for w in warnings)
    if diff_lines:
        out.append("diff against the existing dashboard:")
        out.extend(f"  {line}" for line in diff_lines)
    if not errors:
        count = len(proposed.get("widgets", [])) if isinstance(proposed, dict) else 0
        out.append(f"ok: {count} widgets, {len(warnings)} warnings")
    return (1 if errors else 0), out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("proposed", help="dashboard JSON to save")
    parser.add_argument("--before", help="get_dashboard output of the dashboard being updated")
    args = parser.parse_args(argv)
    code, lines = run(args.proposed, args.before)
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
