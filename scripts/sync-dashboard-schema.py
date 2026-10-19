#!/usr/bin/env python3
"""Copy the Insights dashboard schema into the honeybadger-dashboards skill.

usage: python3 -I scripts/sync-dashboard-schema.py [--check]

Downloads insights/v1/dashboards.json from honeybadger-io/honeybadger-schemas
at REF and writes it to skills/honeybadger-dashboards/scripts/dashboards.json,
where the skill's validator reads it. To pick up a schema change, set REF to
the new commit and run this script. --check exits 1 when the copy differs from
REF instead of writing it.
"""

import argparse
import sys
import urllib.request
from pathlib import Path

REF = "623a52fe6ea9f7368ac279cc7f2f46048c85148e"
URL = f"https://raw.githubusercontent.com/honeybadger-io/honeybadger-schemas/{REF}/insights/v1/dashboards.json"
DEST = Path(__file__).resolve().parent.parent / "skills/honeybadger-dashboards/scripts/dashboards.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if the copy differs from REF")
    args = parser.parse_args()

    with urllib.request.urlopen(URL, timeout=30) as response:
        upstream = response.read()
    current = DEST.read_bytes() if DEST.exists() else None

    if args.check:
        if current != upstream:
            print(f"{DEST.name} differs from honeybadger-schemas@{REF[:7]}; run scripts/sync-dashboard-schema.py")
            return 1
        print(f"ok: {DEST.name} matches honeybadger-schemas@{REF[:7]}")
        return 0

    DEST.write_bytes(upstream)
    print(f"wrote {DEST.relative_to(Path.cwd()) if DEST.is_relative_to(Path.cwd()) else DEST} from {REF[:7]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
