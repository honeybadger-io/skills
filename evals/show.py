"""Print per-case, per-run grader results from a `claude plugin eval --json` file.
usage: python3 -I evals/show.py <results.json>"""
import json, sys
d = json.load(open(sys.argv[1]))
print(f"cost ${d.get('costUsd', 0):.2f}  overall {d.get('aggregates', {}).get('overallScore')}")
def runs(o):
    if isinstance(o, dict):
        if isinstance(o.get("graders"), list) and "score" in o and "startedAt" in o:
            yield o
        for v in o.values(): yield from runs(v)
    elif isinstance(o, list):
        for v in o: yield from runs(v)
for c in d["cases"]:
    print(f"\n== {c['name']}  score {c.get('aggregates', {}).get('score')}")
    for r in runs(c):
        print(f"  run score {r['score']}" + (f"  ERROR {str(r['error'])[:200]}" if r.get("error") else ""))
        for g in r["graders"]:
            mark = "ok " if g.get("passed") else "BAD"
            print(f"    {mark} {g.get('name')}: {str(g.get('explanation') or g.get('reason') or '')[:220]}")
