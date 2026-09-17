"""
build_all.py -- regenerate index.html from the two raw source files.

Run this and nothing else. It rebuilds the two master tables and then the site
page, in dependency order. Each step is a script in this folder that can also
be run on its own; this only sequences them.

    python3 scripts/build_all.py            # rebuild
    python3 scripts/build_all.py --list     # show the steps without running

Inputs (the only two files anything here reads):
    raw_data/wait-times-priority-procedures-in-canada-2008-2025-data-tables-en.xlsx
    raw_data/statcan_65plus_bands_provincial.csv

Outputs:
    output/master_table.csv, output/master_table_fy.csv   what the page is built from
    index.html                                              the page GitHub Pages serves

Each step is deterministic: running twice produces byte-identical files, so a
non-empty `git diff` after a rebuild means an input or a script changed, never
the build itself.
"""

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# (label, script, args). Order matters: the page generator reads the CSVs that
# the two table steps write.
STEPS = [
    ("master table, April-September 2020-2025",
     "build_master_table.py", []),
    ("master table, fiscal year 2020-2024",
     "build_master_table.py", ["--window", "fy"]),
    ("benchmark view -> index.html",
     "make_benchmark_doc.py", []),
]


def main():
    ap = argparse.ArgumentParser(description="Rebuild index.html from raw_data/.")
    ap.add_argument("--list", action="store_true", help="print the steps and exit")
    args = ap.parse_args()

    if args.list:
        for i, (label, script, extra) in enumerate(STEPS, 1):
            print(f"{i}. {label}\n   python3 scripts/{script} {' '.join(extra)}".rstrip())
        return 0

    for i, (label, script, extra) in enumerate(STEPS, 1):
        # flush before handing the terminal to the child, or the parent's
        # buffered header lands after the child's output
        print(f"\n[{i}/{len(STEPS)}] {label}", flush=True)
        print("-" * 66, flush=True)
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, script), *extra],
            cwd=ROOT,
        )
        if result.returncode != 0:
            print(f"\nFAILED at step {i}: {script}", file=sys.stderr)
            return result.returncode

    print("\n" + "=" * 66)
    print("Built: index.html, from output/master_table.csv and master_table_fy.csv.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
