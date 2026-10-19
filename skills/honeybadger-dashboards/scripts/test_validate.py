"""Tests for validate.py. Run: python3 -I <this file>"""

import importlib.util
import json
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("validate", os.path.join(HERE, "validate.py"))
validate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate)


def widget(title, x, y, w, h, wid=None, query='filter event_type::str == "request.handled" | stats count() as count by bin(1h) as time',
           view="line", chart_config=None, streams=None, wtype="insights_vis"):
    out = {"type": wtype, "presentation": {"title": title}, "grid": {"x": x, "y": y, "w": w, "h": h}}
    if wid:
        out["id"] = wid
    if wtype == "insights_vis":
        vis = {"view": view}
        if chart_config is not None:
            vis["chart_config"] = chart_config
        out["config"] = {"query": query, "vis": vis}
        if streams is not None:
            out["config"]["streams"] = streams
    else:
        out["config"] = {"limit": 5}
    return out


def dashboard(*widgets, title="Shop"):
    return {"title": title, "default_ts": "P1D", "widgets": list(widgets)}


LINE = {"xField": "time", "yField": "count"}


class SchemaTests(unittest.TestCase):
    """The rules come from dashboards.json; these fail if its layout stops matching the loader."""

    def setUp(self):
        with open(validate.SCHEMA_PATH, encoding="utf-8") as f:
            self.schema = json.load(f)
        self.widget = self.schema["properties"]["widgets"]["items"]

    def test_every_widget_type_has_config_rules(self):
        types = set(self.widget["properties"]["type"]["enum"])
        self.assertEqual(set(validate.CONFIG_KEYS), types)

    def test_every_view_has_chart_rules(self):
        views = set(self.widget["properties"]["config"]["properties"]["vis"]["properties"]["view"]["enum"])
        self.assertEqual(set(validate.CHART_CONFIG), views)

    def test_rules_are_populated(self):
        self.assertEqual(validate.DASHBOARD_KEYS, {"title", "default_ts", "widgets"})
        self.assertEqual(validate.GRID_KEYS, {"x", "y", "w", "h"})
        self.assertEqual(validate.STREAMS, {"default", "internal"})
        self.assertEqual(validate.GROUP_TYPES, {"fields", "events"})
        self.assertEqual(validate.MAX_TEXT, 255)
        self.assertEqual(validate.CHART_CONFIG["bar"][1], {"categoryField", "valueField"})
        self.assertEqual(validate.EVENTS_REQUIRED, {"billboard": "valueField", "line": "yField", "area": "yField"})
        self.assertIn(("errors", "sort"), validate.CONFIG_ENUMS)


class CheckTests(unittest.TestCase):
    def errors(self, dash):
        return validate.check(dash)[0]

    def warnings(self, dash):
        return validate.check(dash)[1]

    def test_valid_dashboard(self):
        errors, warnings = validate.check(dashboard(
            widget("Requests", 0, 0, 6, 4, chart_config=LINE),
            widget("Errors", 6, 0, 6, 4, wtype="errors"),
        ))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_read_only_keys_are_ignored(self):
        dash = dashboard(widget("A", 0, 0, 12, 4, chart_config=LINE))
        dash.update({"id": "dQ7xRk", "url": "https://app.honeybadger.io/x", "project_id": 1, "is_default": False})
        self.assertEqual(self.errors(dash), [])

    def test_unknown_keys(self):
        dash = dashboard(widget("A", 0, 0, 12, 4, chart_config={"xField": "time", "yField": "count", "color": "red"}))
        dash["widgets"][0]["position"] = 1
        dash["widgets"][0]["config"]["ts"] = "P1D"
        dash["owner"] = "me"
        errs = self.errors(dash)
        self.assertTrue(any("unknown key 'owner'" in e for e in errs))
        self.assertTrue(any("unknown key 'position'" in e for e in errs))
        self.assertTrue(any("unknown config key 'ts'" in e for e in errs))
        self.assertTrue(any("'color' is not valid for view line" in e for e in errs))

    def test_widget_type_and_view(self):
        bad_type = dashboard(widget("A", 0, 0, 6, 4, wtype="chart"))
        self.assertTrue(any("type must be one of" in e for e in self.errors(bad_type)))
        bad_view = dashboard(widget("A", 0, 0, 6, 4, view="sparkline"))
        self.assertTrue(any("vis.view must be one of" in e for e in self.errors(bad_view)))

    def test_required_chart_config(self):
        bar = dashboard(widget("A", 0, 0, 6, 4, view="bar", chart_config={"valueField": "count"}))
        self.assertTrue(any("requires chart_config.categoryField" in e for e in self.errors(bar)))
        events_line = dashboard(widget("A", 0, 0, 6, 4, view="line", chart_config={"groupType": "events", "xField": "time"}))
        self.assertTrue(any("requires chart_config.yField" in e for e in self.errors(events_line)))
        fields_line = dashboard(widget("A", 0, 0, 6, 4, view="line", chart_config={"groupType": "fields", "xField": "time"}))
        self.assertEqual(self.errors(fields_line), [])
        bare_billboard = dashboard(widget("A", 0, 0, 6, 4, view="billboard"))
        self.assertEqual(self.errors(bare_billboard), [])
        self.assertTrue(any("defaults to groupType events" in w for w in self.warnings(bare_billboard)))

    def test_grid_overflow_and_overlap(self):
        overflow = dashboard(widget("A", 8, 0, 6, 4, chart_config=LINE))
        self.assertTrue(any("exceeds 12 columns" in e for e in self.errors(overflow)))
        overlap = dashboard(widget("A", 0, 0, 6, 4, chart_config=LINE), widget("B", 3, 2, 6, 4, chart_config=LINE))
        self.assertTrue(any("overlaps" in e for e in self.errors(overlap)))
        floats = dashboard(widget("A", 0, 0, 6.0, 4, chart_config=LINE))
        self.assertTrue(any("must be integers" in e for e in self.errors(floats)))
        adjacent = dashboard(widget("A", 0, 0, 6, 4, chart_config=LINE), widget("B", 6, 0, 6, 4, chart_config=LINE),
                             widget("C", 0, 4, 12, 2, chart_config=LINE))
        self.assertEqual(self.errors(adjacent), [])

    def test_title_lengths(self):
        long = "x" * 256
        dash = dashboard(widget(long, 0, 0, 6, 4, chart_config=LINE), title=long)
        errs = self.errors(dash)
        self.assertTrue(any("dashboard: title is 256" in e for e in errs))
        self.assertTrue(any("presentation.title is 256" in e for e in errs))
        null_title = dashboard(widget("A", 0, 0, 6, 4, chart_config=LINE))
        null_title["widgets"][0]["presentation"] = {"title": None, "subtitle": None}
        self.assertEqual(self.errors(null_title), [])

    def test_widget_count_warning(self):
        many = dashboard(*[widget(f"W{i}", 0, i * 2, 12, 2, chart_config=LINE) for i in range(31)])
        self.assertTrue(any("31 widgets" in w for w in self.warnings(many)))

    def test_insights_vis_needs_query_and_view(self):
        dash = dashboard(widget("A", 0, 0, 6, 4, chart_config=LINE))
        dash["widgets"][0]["config"] = {"vis": {"chart_config": LINE}}
        errs = self.errors(dash)
        self.assertTrue(any("need a non-empty query" in e for e in errs))
        self.assertTrue(any("vis.view must be one of" in e for e in errs))

    def test_internal_stream_warning(self):
        notice = 'filter event_type::str == "notice" | stats count() as count by klass::str'
        bar = {"categoryField": "klass", "valueField": "count"}
        missing = dashboard(widget("Errors", 0, 0, 6, 4, query=notice, view="bar", chart_config=bar, streams=["default"]))
        self.assertTrue(any('lacks "internal"' in w for w in self.warnings(missing)))
        present = dashboard(widget("Errors", 0, 0, 6, 4, query=notice, view="bar", chart_config=bar, streams=["internal"]))
        self.assertFalse(any('lacks "internal"' in w for w in self.warnings(present)))
        deployments = dashboard(widget("Deploys", 0, 0, 6, 4, wtype="deployments"))
        self.assertEqual(self.warnings(deployments), [])
        bad_slug = dashboard(widget("A", 0, 0, 6, 4, chart_config=LINE, streams=["Kp3mQ8vLxR2a"]))
        self.assertTrue(any("unknown stream" in e for e in self.errors(bad_slug)))


class DiffTests(unittest.TestCase):
    def setUp(self):
        self.before = dashboard(
            widget("Requests", 0, 0, 6, 4, wid="w1", chart_config=LINE),
            widget("Errors", 6, 0, 6, 4, wid="w2", wtype="errors"),
        )

    def test_added_changed_removed(self):
        after = dashboard(
            widget("Requests per hour", 0, 0, 6, 4, wid="w1", chart_config=LINE),
            widget("Latency", 0, 4, 12, 4, chart_config=LINE),
        )
        errors, warnings, lines = validate.diff(self.before, after)
        self.assertEqual(errors, [])
        text = "\n".join(lines)
        self.assertIn('added (1): widget 1 "Latency"', text)
        self.assertIn('changed (1): widget 0 "Requests per hour" (presentation.title)', text)
        self.assertIn('removed (1): widget 1 "Errors"', text)
        self.assertEqual(len(warnings), 1)
        self.assertIn('will delete 1 widget(s): widget 1 "Errors"', warnings[0])

    def test_changed_fields(self):
        moved = widget("Requests", 0, 4, 6, 4, wid="w1", chart_config=LINE)
        moved["config"]["streams"] = ["default", "internal"]
        moved["config"]["vis"]["chart_config"] = {"xField": "time", "yField": "total"}
        after = dashboard(moved, widget("Errors", 6, 0, 6, 4, wid="w2", wtype="errors"))
        _, _, lines = validate.diff(self.before, after)
        self.assertIn('changed (1): widget 0 "Requests" (config.streams, config.vis.chart_config.yField, grid)',
                      "\n".join(lines))

    def test_unchanged(self):
        errors, warnings, lines = validate.diff(self.before, json.loads(json.dumps(self.before)))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertIn("unchanged: 2", "\n".join(lines))
        self.assertIn("removed (0): none", "\n".join(lines))

    def test_unknown_and_duplicate_ids(self):
        after = dashboard(
            widget("Requests", 0, 0, 6, 4, wid="w1", chart_config=LINE),
            widget("Errors", 6, 0, 6, 4, wid="w2", wtype="errors"),
            widget("Copy", 0, 4, 6, 4, wid="w1", chart_config=LINE),
            widget("Invented", 6, 4, 6, 4, wid="w9", chart_config=LINE),
        )
        errors, _, _ = validate.diff(self.before, after)
        self.assertTrue(any("'w1' appears twice" in e for e in errors))
        self.assertTrue(any("'w9' is not on the existing dashboard" in e for e in errors))


class RunTests(unittest.TestCase):
    def write(self, data):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(data, f)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_exit_codes_and_order(self):
        before = dashboard(widget("Requests", 0, 0, 6, 4, wid="w1", chart_config=LINE))
        proposed = dashboard(
            widget("Requests", 0, 0, 6, 4, wid="w1", chart_config=LINE),
            widget("Errors", 6, 0, 8, 4, query='filter event_type::str == "notice" | stats count() as count',
                   view="billboard", chart_config={"valueField": "count"}),
        )
        code, lines = validate.run(self.write(proposed), self.write(before))
        self.assertEqual(code, 1)
        kinds = [line.split(" ")[0].rstrip(":") for line in lines if line.startswith(("error", "warning", "diff"))]
        self.assertEqual(kinds, sorted(kinds, key=["error", "warning", "diff"].index))
        self.assertTrue(any("exceeds 12 columns" in line for line in lines))
        self.assertTrue(any('lacks "internal"' in line for line in lines))

    def test_ok_run(self):
        proposed = dashboard(widget("Requests", 0, 0, 6, 4, chart_config=LINE))
        code, lines = validate.run(self.write(proposed))
        self.assertEqual(code, 0)
        self.assertEqual(lines[-1], "ok: 1 widgets, 0 warnings")

    def test_ids_without_before_warns(self):
        proposed = dashboard(widget("Requests", 0, 0, 6, 4, wid="w1", chart_config=LINE))
        code, lines = validate.run(self.write(proposed))
        self.assertEqual(code, 0)
        self.assertTrue(any("no --before" in line for line in lines))

    def test_bad_json(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        f.write("{not json")
        f.close()
        self.addCleanup(os.unlink, f.name)
        code, lines = validate.run(f.name)
        self.assertEqual(code, 1)
        self.assertTrue(lines[0].startswith("error: cannot read"))


if __name__ == "__main__":
    unittest.main()
