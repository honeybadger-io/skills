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
import os
import re
import sys

# ---------------------------------------------------------------------------
# Rules. The allowed keys, required keys, and allowed values come from
# dashboards.json, a pinned copy of insights/v1/dashboards.json from
# https://github.com/honeybadger-io/honeybadger-schemas. Update it with
# scripts/sync-dashboard-schema.py at the repo root; do not edit it by hand.
# ---------------------------------------------------------------------------

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboards.json")

GRID_COLUMNS = 12
WIDGET_WARN_COUNT = 30  # more than this has been rejected on save
# Present in get_dashboard output; ignored on save.
DASHBOARD_READ_ONLY_KEYS = {"id", "url", "created_at", "updated_at", "project_id", "is_default", "shared"}
# The schema allows any string for these; the charts reference lists the values the renderer understands.
UNIT_KEYS = {"valueFieldUnit", "xFieldUnit", "yFieldUnit"}
UNITS = {"percent", "microseconds", "milliseconds"}


def resolve(schema, node):
    """Follow local $refs ("#/$defs/...") until node is a plain schema."""
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if not ref.startswith("#/"):
            raise ValueError(f"unsupported $ref {ref!r}")
        node = schema
        for part in ref[2:].split("/"):
            node = node[part]
    return node


def rules_by_const(schema, all_of, field, target):
    """Map each `if: {field: const}` rule in all_of to the schema its `then` gives `target`."""
    rules = {}
    for rule in all_of:
        const = rule["if"]["properties"][field]["const"]
        rules[const] = resolve(schema, rule["then"]["properties"][target])
    return rules


def load_rules(path=SCHEMA_PATH):
    with open(path, encoding="utf-8") as f:
        schema = json.load(f)
    dashboard = schema["properties"]
    widget = dashboard["widgets"]["items"]
    vis = widget["properties"]["config"]["properties"]["vis"]
    configs = rules_by_const(schema, widget["allOf"], "type", "config")
    charts = rules_by_const(schema, vis["allOf"], "view", "chart_config")

    rules = {
        "dashboard_keys": set(dashboard),
        "max_text": dashboard["title"]["maxLength"],
        "widget_keys": set(widget["properties"]),
        "grid_keys": set(widget["properties"]["grid"]["properties"]),
        "presentation_keys": set(widget["properties"]["presentation"]["properties"]),
        "vis_keys": set(vis["properties"]),
        "config_keys": {t: set(c.get("properties", {})) for t, c in configs.items()},
        "config_enums": {
            (t, key): set(p["enum"])
            for t, c in configs.items()
            for key, p in c.get("properties", {}).items()
            if isinstance(p, dict) and "enum" in p
        },
        "streams": set(configs["insights_vis"]["properties"]["streams"]["items"]["enum"]),
        "chart_config": {
            view: (set(c.get("properties", {})), set(c.get("required", [])))
            for view, c in charts.items()
        },
        "group_types": set(),
        "events_required": {},
    }
    for view, c in charts.items():
        group_type = c.get("properties", {}).get("groupType")
        if group_type:
            rules["group_types"] |= set(group_type["enum"])
        for rule in c.get("allOf", []):
            if rule["if"]["properties"].get("groupType", {}).get("const") == "events":
                rules["events_required"][view] = rule["then"]["required"][0]
    return rules


RULES = load_rules()
DASHBOARD_KEYS = RULES["dashboard_keys"]
MAX_TEXT = RULES["max_text"]
WIDGET_KEYS = RULES["widget_keys"]
GRID_KEYS = RULES["grid_keys"]
PRESENTATION_KEYS = RULES["presentation_keys"]
CONFIG_KEYS = RULES["config_keys"]
CONFIG_ENUMS = RULES["config_enums"]
STREAMS = RULES["streams"]
VIS_KEYS = RULES["vis_keys"]
GROUP_TYPES = RULES["group_types"]
# view -> (allowed chart_config keys, keys required whatever the groupType)
CHART_CONFIG = RULES["chart_config"]
# Required only when groupType is "events" (the default when groupType is absent).
EVENTS_REQUIRED = RULES["events_required"]

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


def changed_fields(old, new, prefix=""):
    """Return the dotted paths of the fields that differ between two widgets."""
    paths = []
    for key in sorted(set(old) | set(new), key=str):
        path = f"{prefix}{key}"
        a, b = old.get(key), new.get(key)
        if a == b:
            continue
        # A moved or resized widget reads better as "grid" than as grid.x, grid.w.
        if isinstance(a, dict) and isinstance(b, dict) and path != "grid":
            paths.extend(changed_fields(a, b, path + "."))
        else:
            paths.append(path)
    return paths


def diff(before, after):
    """Return (errors, warnings, lines): id problems, removals, and the added/changed/removed widgets."""
    errors, warnings, lines = [], [], []
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
        fields = changed_fields(old[wid][1], widget)
        if fields:
            changed.append(f"{name} ({', '.join(fields)})")
        else:
            same += 1
    removed = [widget_name(w, i) for wid, (i, w) in old.items() if wid not in seen]
    if removed:
        warnings.append(f"update_dashboard will delete {len(removed)} widget(s): {', '.join(removed)}; "
                        "tell the user, and keep them unless the user asked to remove them")
    if "title" in before and before.get("title") != after.get("title"):
        lines.append(f"title: {before.get('title')!r} -> {after.get('title')!r}")
    if before.get("default_ts") != after.get("default_ts"):
        lines.append(f"default_ts: {before.get('default_ts')!r} -> {after.get('default_ts')!r}")
    lines.append(f"added ({len(added)}): " + (", ".join(added) or "none"))
    lines.append(f"changed ({len(changed)}): " + (", ".join(changed) or "none"))
    lines.append(f"removed ({len(removed)}): " + (", ".join(removed) or "none"))
    lines.append(f"unchanged: {same}")
    return errors, warnings, lines


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
        diff_errors, diff_warnings, diff_lines = diff(before, proposed)
        errors.extend(diff_errors)
        warnings.extend(diff_warnings)
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
