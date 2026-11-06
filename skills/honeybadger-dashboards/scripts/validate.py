#!/usr/bin/env python3
"""Check a proposed Honeybadger Insights dashboard before it is saved.

usage: python3 -I validate.py proposed.json [--before before.json]

proposed.json is the dashboard to save: {"title", "default_ts", "widgets"}.
before.json is the get_dashboard output of the dashboard being updated; with it,
the script lists the widgets that will be added, changed, and removed.

The API checks the dashboard's structure on save and rejects an invalid one
without changing anything. This script checks what the API does not: the grid
layout, widget ids, and which widgets an update would delete.

Prints errors, then warnings, then the diff. Exits 1 when there are errors.
Standard library only.
"""

import argparse
import json
import re
import sys

GRID_COLUMNS = 12
WIDGET_WARN_COUNT = 30  # more than this has been rejected on save

INTERNAL_EVENTS = re.compile(r"\b(notice|deploy|uptime_check|check_in)\b")


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
        return json.load(f)


def check(dashboard):
    """Return (errors, warnings) for one dashboard object."""
    errors, warnings = [], []
    if not isinstance(dashboard, dict):
        return ["dashboard must be a JSON object"], warnings
    widgets = dashboard.get("widgets")
    if not isinstance(widgets, list):
        return ["dashboard: widgets must be an array"], warnings
    if len(widgets) > WIDGET_WARN_COUNT:
        warnings.append(f"dashboard: {len(widgets)} widgets; more than {WIDGET_WARN_COUNT} may be rejected on save")

    occupied = {}
    for index, widget in enumerate(widgets):
        name = widget_name(widget, index)
        if not isinstance(widget, dict):
            errors.append(f"{name}: must be an object")
            continue
        check_grid(widget.get("grid"), name, occupied, errors)
        config = widget.get("config")
        if widget.get("type") == "insights_vis" and isinstance(config, dict):
            check_query(config, name, warnings)
    return errors, warnings


def check_grid(grid, name, occupied, errors):
    if grid is None:
        return
    if not isinstance(grid, dict) or not all(is_int(grid.get(k)) for k in "xywh"):
        errors.append(f"{name}: grid needs integer x, y, w, h")
        return
    x, y, w, h = (grid[k] for k in "xywh")
    if x < 0 or y < 0 or w < 1 or h < 1:
        errors.append(f"{name}: grid needs x >= 0, y >= 0, w >= 1, h >= 1")
        return
    if x + w > GRID_COLUMNS:
        errors.append(f"{name}: grid x {x} + w {w} exceeds {GRID_COLUMNS} columns")
    cells = [(col, row) for col in range(x, min(x + w, GRID_COLUMNS)) for row in range(y, y + h)]
    for cell in cells:
        other = occupied.get(cell)
        if other is not None:
            errors.append(f"{name}: overlaps {other} at column {cell[0]}, row {cell[1]}")
            return
    for cell in cells:
        occupied[cell] = name


def check_query(config, name, warnings):
    query = config.get("query")
    if not isinstance(query, str):
        return
    # A widget with no streams reads every stream; one that lists them reads only those.
    streams = config.get("streams")
    if INTERNAL_EVENTS.search(query) and isinstance(streams, list) and streams and "internal" not in streams:
        warnings.append(f"{name}: the query mentions a Honeybadger event but streams lacks \"internal\", so it will read none of them")
    if "${" in query:
        warnings.append(f"{name}: the query has parameters; query_insights does not expand them, so test with the values substituted")


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
            warnings.append(f"{name}: id {wid!r} is not on the existing dashboard; leave id off a new widget unless you are restoring one")
            added.append(name)
            continue
        fields = changed_fields(old[wid][1], widget)
        if fields:
            changed.append(f"{name} ({', '.join(fields)})")
        else:
            same += 1
    removed = [widget_name(w, i) for wid, (i, w) in old.items() if wid not in seen]
    if removed:
        warnings.append(f"the update will delete {len(removed)} widget(s): {', '.join(removed)}; "
                        "tell the user, and keep them unless the user asked to remove them")
    if "title" in after and before.get("title") != after.get("title"):
        lines.append(f"title: {before.get('title')!r} -> {after.get('title')!r}")
    if "default_ts" in after and before.get("default_ts") != after.get("default_ts"):
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
        if isinstance(proposed, dict):
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
        count = len(proposed.get("widgets") or []) if isinstance(proposed, dict) else 0
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
