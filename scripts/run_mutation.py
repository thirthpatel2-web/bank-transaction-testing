"""Runs Cosmic Ray mutation testing using this environment's Python, then reports the real outcomes.

The test command must name the interpreter by absolute path: on Windows a bare "python" can resolve
to the system install, whose missing pytest makes every mutant look killed.
"""

import shutil
import sqlite3
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
EVIDENCE = ROOT / "docs" / "evidence"
CONFIG = REPORTS / "cosmic-ray.toml"
SESSION = REPORTS / "mutation.sqlite"
TEST_ARGS = "-m pytest -x -q --no-header -p no:cacheprovider --ignore=tests/test_properties.py"
SKIP_DIFF_PREFIXES = ("+++", "---")


def cosmic_ray() -> str:
    return str(Path(sys.executable).with_name("cosmic-ray"))


def write_config() -> None:
    command = f'"{Path(sys.executable).as_posix()}" {TEST_ARGS}'
    CONFIG.write_text(
        "[cosmic-ray]\n"
        'module-path = "src/bank"\n'
        "timeout = 60.0\n"
        "excluded-modules = []\n"
        f"test-command = '{command}'\n\n"
        "[cosmic-ray.distributor]\n"
        'name = "local"\n',
        encoding="utf-8",
    )


def require_green_baseline() -> None:
    """Mutation results mean nothing unless the unmutated code passes with this exact command."""
    args = [sys.executable, *TEST_ARGS.split()]
    if subprocess.run(args, cwd=ROOT, capture_output=True).returncode != 0:
        sys.exit("Baseline tests failed on unmutated code, so mutation results would be meaningless.")


def summarize() -> str:
    db = sqlite3.connect(SESSION)
    rows = db.execute(
        """select m.module_path, m.start_pos_row, m.operator_name, r.test_outcome, r.diff
           from work_results r join mutation_specs m on m.job_id = r.job_id
           order by m.module_path, m.start_pos_row"""
    ).fetchall()
    db.close()
    outcomes = Counter(row[3].split(".")[-1].upper() for row in rows)
    killed, survived = outcomes["KILLED"], outcomes["SURVIVED"]
    scored = killed + survived
    score = 100 * killed / scored if scored else 0.0
    lines = [
        f"Mutants: {len(rows)}",
        f"Killed: {killed}",
        f"Survived: {survived}",
        f"Incompetent: {outcomes['INCOMPETENT']}",
        f"Mutation score: {score:.1f}%",
        "",
    ]
    for module, row, operator, outcome, diff in rows:
        if outcome.split(".")[-1].upper() == "SURVIVED":
            lines.append(f"{module} line {row + 1 if row == 0 else row} {operator}")
            lines += [
                f"    {line}"
                for line in (diff or "").splitlines()
                if line[:1] in ("+", "-") and not line.startswith(SKIP_DIFF_PREFIXES)
            ]
    return "\n".join(lines) + "\n"


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(ROOT / "src" / "bank" / "__pycache__", ignore_errors=True)
    write_config()
    require_green_baseline()
    shutil.rmtree(ROOT / "src" / "bank" / "__pycache__", ignore_errors=True)
    subprocess.run([cosmic_ray(), "init", str(CONFIG), str(SESSION), "--force"], cwd=ROOT, check=True)
    subprocess.run([cosmic_ray(), "exec", str(CONFIG), str(SESSION)], cwd=ROOT, check=True)
    summary = summarize()
    (EVIDENCE / "03-mutation-summary.txt").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
