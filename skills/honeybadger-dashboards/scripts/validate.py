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
import sys

GRID_COLUMNS = 12


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
    if "widgets" not in dashboard:
        return errors, warnings  # an update without widgets keeps the existing ones
    widgets = dashboard["widgets"]
    if not isinstance(widgets, list):
        return ["dashboard: widgets must be an array"], warnings

    placed, ids = [], set()
    for index, widget in enumerate(widgets):
        name = widget_name(widget, index)
        if not isinstance(widget, dict):
            errors.append(f"{name}: must be an object")
            continue
        wid = widget.get("id")
        if wid is not None and not isinstance(wid, str):
            errors.append(f"{name}: id must be a string")
        elif wid in ids:
            errors.append(f"{name}: id {wid!r} appears twice; the second copy would be a duplicate")
        elif wid:
            ids.add(wid)
        check_grid(widget.get("grid"), name, placed, errors)
    return errors, warnings


def check_grid(grid, name, placed, errors):
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
    right = min(x + w, GRID_COLUMNS)
    for other, ox, oy, oright, obottom in placed:
        if x < oright and ox < right and y < obottom and oy < y + h:
            errors.append(f"{name}: overlaps {other} at column {max(x, ox)}, row {max(y, oy)}")
            break
    # Keep an overlapping widget too, so a later widget that overlaps it is reported.
    placed.append((name, x, y, right, y + h))

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
    left_out = [key for key in ("title", "default_ts") if key in before and key not in after]
    if left_out:
        warnings.append(f"the proposed dashboard leaves out {', '.join(left_out)}; "
                        "an update that replaces the whole dashboard would reset them, so send them back unchanged")
    for key in ("title", "default_ts"):
        if key in after and before.get(key) != after.get(key):
            lines.append(f"{key}: {before.get(key)!r} -> {after.get(key)!r}")
    if "widgets" not in after:
        lines.append("widgets: not sent, so the existing widgets stay")
        return errors, warnings, lines
    if not isinstance(after["widgets"], list):
        return errors, warnings, lines  # check() reports it

    old_widgets = before.get("widgets") if isinstance(before.get("widgets"), list) else []
    old = {w["id"]: (i, w) for i, w in enumerate(old_widgets) if isinstance(w, dict) and isinstance(w.get("id"), str) and w["id"]}
    seen = set()
    added, changed, same = [], [], 0
    for i, widget in enumerate(after["widgets"]):
        if not isinstance(widget, dict):
            continue
        name = widget_name(widget, i)
        wid = widget.get("id")
        if not isinstance(wid, str) or not wid:
            if wid is None or wid == "":
                added.append(name)
            continue
        if wid in seen:
            continue  # check() reports duplicates
        seen.add(wid)
        if wid not in old:
            warnings.append(f"{name}: id {wid!r} is not on the existing dashboard; leave id off a new widget, including one restored from a backup")
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
    elif isinstance(proposed, dict) and isinstance(proposed.get("widgets"), list) and any(
            isinstance(w, dict) and w.get("id") for w in proposed["widgets"]):
        warnings.append("some widgets have ids but no --before dashboard was given; ids must come from the dashboard being updated")

    out.extend(f"error: {e}" for e in errors)
    out.extend(f"warning: {w}" for w in warnings)
    if diff_lines:
        out.append("diff against the existing dashboard:")
        out.extend(f"  {line}" for line in diff_lines)
    if not errors:
        widgets = proposed.get("widgets") if isinstance(proposed, dict) else None
        count = len(widgets) if isinstance(widgets, list) else 0
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
