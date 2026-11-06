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

    def test_any_response_keys_are_accepted(self):
        dash = dashboard(widget("A", 0, 0, 12, 4, chart_config=dict(LINE)))
        dash.update({"id": "dQ7xRk", "url": "https://app.honeybadger.io/x", "project_id": "p8Kx2", "links": {"web": "https://app.honeybadger.io/x"}})
        dash["widgets"][0]["config"]["vis"]["chart_config"]["anything"] = 1
        self.assertEqual(self.errors(dash), [])

    def test_grid_overflow_and_overlap(self):
        overflow = dashboard(widget("A", 8, 0, 6, 4, chart_config=LINE))
        self.assertTrue(any("exceeds 12 columns" in e for e in self.errors(overflow)))
        overlap = dashboard(widget("A", 0, 0, 6, 4, chart_config=LINE), widget("B", 3, 2, 6, 4, chart_config=LINE))
        self.assertTrue(any("overlaps" in e for e in self.errors(overlap)))
        floats = dashboard(widget("A", 0, 0, 6.0, 4, chart_config=LINE))
        self.assertTrue(any("integer x, y, w, h" in e for e in self.errors(floats)))
        adjacent = dashboard(widget("A", 0, 0, 6, 4, chart_config=LINE), widget("B", 6, 0, 6, 4, chart_config=LINE),
                             widget("C", 0, 4, 12, 2, chart_config=LINE))
        self.assertEqual(self.errors(adjacent), [])

    def test_overlaps_are_all_reported(self):
        chain = dashboard(widget("A", 0, 0, 6, 4, chart_config=LINE), widget("B", 3, 0, 6, 4, chart_config=LINE),
                          widget("C", 7, 0, 2, 4, chart_config=LINE))
        errs = self.errors(chain)
        self.assertTrue(any(e.startswith('widget 1 "B": overlaps') for e in errs))
        self.assertTrue(any(e.startswith('widget 2 "C": overlaps') for e in errs))

    def test_duplicate_ids_without_before(self):
        dash = dashboard(widget("A", 0, 0, 6, 4, wid="w1", chart_config=LINE), widget("B", 6, 0, 6, 4, wid="w1", chart_config=LINE))
        self.assertTrue(any("'w1' appears twice" in e for e in self.errors(dash)))

    def test_widgets_left_out(self):
        self.assertEqual(validate.check({"title": "Renamed"}), ([], []))

    def test_bad_ids_and_widgets(self):
        self.assertTrue(any("widgets must be an array" in e for e in self.errors({"widgets": 5})))
        dash = dashboard(widget("A", 0, 0, 6, 4, wid="w1", chart_config=LINE))
        dash["widgets"][0]["id"] = ["w1"]
        self.assertTrue(any("id must be a string" in e for e in self.errors(dash)))

    def test_empty_streams_read_every_stream(self):
        notice = 'filter event_type::str == "notice" | stats count() as count by bin(1h) as time'
        dash = dashboard(widget("Errors", 0, 0, 6, 4, query=notice, chart_config=LINE, streams=[]))
        self.assertEqual(self.warnings(dash), [])

    def test_parameter_warning(self):
        dash = dashboard(widget("A", 0, 0, 6, 4, query='filter env::str == "${env:-production}" | stats count() as count by bin(1h) as time', chart_config=LINE))
        self.assertTrue(any("has parameters" in w for w in self.warnings(dash)))

    def test_internal_stream_warning(self):
        notice = 'filter event_type::str == "notice" | stats count() as count by klass::str'
        bar = {"categoryField": "klass", "valueField": "count"}
        missing = dashboard(widget("Errors", 0, 0, 6, 4, query=notice, view="bar", chart_config=bar, streams=["default"]))
        self.assertTrue(any('lacks "internal"' in w for w in self.warnings(missing)))
        present = dashboard(widget("Errors", 0, 0, 6, 4, query=notice, view="bar", chart_config=bar, streams=["internal"]))
        self.assertFalse(any('lacks "internal"' in w for w in self.warnings(present)))
        deployments = dashboard(widget("Deploys", 0, 0, 6, 4, wtype="deployments"))
        self.assertEqual(self.warnings(deployments), [])
        every_stream = dashboard(widget("Errors", 0, 0, 6, 4, query=notice, view="bar", chart_config=bar))
        self.assertEqual(self.warnings(every_stream), [])


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
        errors, warnings, lines = validate.diff(self.before, after)
        self.assertTrue(any("'w1' appears twice" in e for e in validate.check(after)[0]))
        self.assertTrue(any("'w9' is not on the existing dashboard" in w for w in warnings))
        self.assertIn('added (1): widget 3 "Invented"', "\n".join(lines))

    def test_widgets_only_update(self):
        after = {"widgets": json.loads(json.dumps(self.before["widgets"]))}
        errors, _, lines = validate.diff(self.before, after)
        self.assertEqual(errors, [])
        self.assertNotIn("title:", "\n".join(lines))

    def test_title_and_default_ts_changes(self):
        after = json.loads(json.dumps(self.before))
        after.update({"title": "Shop 2", "default_ts": "P7D"})
        _, warnings, lines = validate.diff(self.before, after)
        text = "\n".join(lines)
        self.assertIn("title: 'Shop' -> 'Shop 2'", text)
        self.assertIn("default_ts: 'P1D' -> 'P7D'", text)
        self.assertEqual(warnings, [])

    def test_left_out_title_and_default_ts_warn(self):
        after = {"widgets": json.loads(json.dumps(self.before["widgets"]))}
        _, warnings, _ = validate.diff(self.before, after)
        self.assertTrue(any("leaves out title, default_ts" in w for w in warnings))

    def test_left_out_widgets_are_kept(self):
        errors, warnings, lines = validate.diff(self.before, {"title": "Shop", "default_ts": "P1D"})
        self.assertEqual((errors, warnings), ([], []))
        self.assertIn("widgets: not sent", "\n".join(lines))


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
                   view="billboard", chart_config={"valueField": "count"}, streams=["default"]),
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

    def test_malformed_input_does_not_crash(self):
        before = dashboard(widget("Requests", 0, 0, 6, 4, wid="w1", chart_config=LINE))
        code, lines = validate.run(self.write({"widgets": 5}), self.write(before))
        self.assertEqual(code, 1)
        listed = dashboard(widget("Requests", 0, 0, 6, 4, chart_config=LINE))
        listed["widgets"][0]["id"] = ["w1"]
        code, lines = validate.run(self.write(listed), self.write(before))
        self.assertEqual(code, 1)
        self.assertTrue(any("id must be a string" in line for line in lines))

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
