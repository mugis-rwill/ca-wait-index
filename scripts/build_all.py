"""
build_all.py -- regenerate every output from the two raw source files.

Run this and nothing else. It rebuilds the master tables and regenerates the
site's index.html, in dependency order, and then -- if their scripts are present
in this checkout -- the sibling deliverables (matched pairs, charts, the local
contents page). Every step is a script in this folder that can also be run on
its own; this only sequences them.

    python3 scripts/build_all.py            # everything available
    python3 scripts/build_all.py --list     # show the steps without running

The split matters for a fresh clone. Only the index steps are tracked in git:
build_master_table.py, make_benchmark_doc.py and benchmark_template.html. The
sibling scripts are gitignored (see .gitignore) and exist only on machines that
have them, so their steps are skipped, with a note, rather than failing.

Inputs (the only two files anything here reads):
    raw_data/wait-times-priority-procedures-in-canada-2008-2025-data-tables-en.xlsx
    raw_data/statcan_65plus_bands_provincial.csv

Outputs land in output/, except index.html (the page GitHub Pages serves) and
deliverables.html (a local, untracked contents page for everything else), both
written to the repo root.

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

# (label, script, args). Order matters: the page generators read the CSVs that
# the table and rule steps write.

# What index.html needs. Always run; these scripts are tracked.
INDEX_STEPS = [
    ("master table, April-September 2020-2025",
     "build_master_table.py", []),
    ("master table, fiscal year 2020-2024",
     "build_master_table.py", ["--window", "fy"]),
    ("benchmark view -> index.html",
     "make_benchmark_doc.py", []),
]

# Separate work products. Run only when the script is present -- they are
# gitignored, so a fresh clone does not have them and should not fail on them.
SIBLING_STEPS = [
    ("matching rule, April-September",
     "matched_pairs.py", []),
    ("matching rule, fiscal year",
     "matched_pairs.py", ["--table", os.path.join(ROOT, "output", "master_table_fy.csv"),
                          "--tag", "_fy"]),
    ("charts page (Task 4)",
     "make_charts.py", []),
    ("matched pairs register, April-September",
     "make_pairs_doc.py", []),
    ("matched pairs charts, fiscal year",
     "make_fy_pairs_doc.py", []),
    ("local contents page -> deliverables.html",
     "make_local_index.py", []),
]

STEPS = INDEX_STEPS + SIBLING_STEPS


def main():
    ap = argparse.ArgumentParser(description="Rebuild every output.")
    ap.add_argument("--list", action="store_true", help="print the steps and exit")
    args = ap.parse_args()

    if args.list:
        for i, (label, script, extra) in enumerate(STEPS, 1):
            present = os.path.exists(os.path.join(HERE, script))
            tag = "" if present else "   (not in this checkout -- will be skipped)"
            print(f"{i}. {label}{tag}\n   python3 scripts/{script} {' '.join(extra)}".rstrip())
        return 0

    skipped = []
    for i, (label, script, extra) in enumerate(STEPS, 1):
        # flush before handing the terminal to the child, or the parent's
        # buffered header lands after the child's output
        print(f"\n[{i}/{len(STEPS)}] {label}", flush=True)
        print("-" * 66, flush=True)

        script_path = os.path.join(HERE, script)
        if not os.path.exists(script_path):
            # Only sibling steps can be missing; index steps are tracked.
            print(f"skipped: scripts/{script} is not in this checkout", flush=True)
            skipped.append(script)
            continue

        result = subprocess.run([sys.executable, script_path, *extra], cwd=ROOT)
        if result.returncode != 0:
            print(f"\nFAILED at step {i}: {script}", file=sys.stderr)
            return result.returncode

    print("\n" + "=" * 66)
    print("Index built: site page at index.html; tables in output/.")
    if skipped:
        print(f"Skipped {len(skipped)} sibling step(s) whose scripts are not in this "
              f"checkout: {', '.join(sorted(set(skipped)))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
