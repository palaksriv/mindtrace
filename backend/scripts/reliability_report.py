"""Compute reliability statistics from ``export_pilot_data`` output.

Usage (from ``backend/``)::

    python -m scripts.reliability_report --items exports/item_responses.csv \
        --sessions exports/session_summary.csv [--bfi10 exports/bfi10_scores.csv]

Reports, per Big Five trait:

* Cronbach's alpha with a 95 % bootstrap CI (first completed session per student);
* the Spearman-Brown prediction for doubling the scale to 8 items;
* test-retest correlation for students with two or more completed sessions;
* optionally, convergent validity against an external BFI-10 file with columns
  ``pseudonym,openness,conscientiousness,extraversion,agreeableness,neuroticism``.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict

import numpy as np

from app.services.psychometrics import (
    bootstrap_ci,
    cronbach_alpha,
    pearson_r,
    retest_correlation,
    spearman_brown,
)

TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]


def load_first_sessions(items_path: str):
    """Return {trait: (n_students x 4 matrix)} using each student's first session."""
    rows = list(csv.DictReader(open(items_path, newline="")))
    first_session: dict[str, int] = {}
    for r in rows:
        sid = int(r["session_id"])
        who = r["pseudonym"]
        first_session[who] = min(first_session.get(who, sid), sid)
    per_student: dict[str, dict[str, list[tuple[int, int]]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if int(r["session_id"]) == first_session[r["pseudonym"]]:
            per_student[r["pseudonym"]][r["trait"]].append((int(r["question_order"]), int(r["keyed"])))
    matrices = {}
    for t in TRAITS:
        mat = []
        for who, by_trait in per_student.items():
            vals = [v for _, v in sorted(by_trait[t])]
            if len(vals) == 4:
                mat.append(vals)
        matrices[t] = np.array(mat, dtype=float)
    return matrices


def retest_pairs(sessions_path: str):
    by_student: dict[str, list[dict]] = defaultdict(list)
    for r in csv.DictReader(open(sessions_path, newline="")):
        by_student[r["pseudonym"]].append(r)
    pairs = {t: ([], []) for t in TRAITS}
    for who, rows in by_student.items():
        rows.sort(key=lambda r: r["completed_at"])
        if len(rows) >= 2:
            for t in TRAITS:
                pairs[t][0].append(float(rows[0][t]))
                pairs[t][1].append(float(rows[1][t]))
    return pairs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--items", required=True)
    ap.add_argument("--sessions", required=True)
    ap.add_argument("--bfi10")
    args = ap.parse_args()

    mats = load_first_sessions(args.items)
    pairs = retest_pairs(args.sessions)
    bfi = {}
    if args.bfi10:
        for r in csv.DictReader(open(args.bfi10, newline="")):
            bfi[r["pseudonym"]] = r
    sessions_first = {}
    for r in csv.DictReader(open(args.sessions, newline="")):
        sessions_first.setdefault(r["pseudonym"], r)

    print(f"{'trait':<18}{'n':>4}{'alpha':>8}{'95% CI':>18}{'alpha(8 items)':>16}{'retest n':>10}{'retest r':>10}{'r vs BFI-10':>13}")
    for t in TRAITS:
        m = mats[t]
        n = len(m)
        a = cronbach_alpha(m) if n >= 2 else float("nan")
        lo, hi = bootstrap_ci(cronbach_alpha, m) if n >= 5 else (float("nan"), float("nan"))
        a8 = spearman_brown(a, 2.0) if not np.isnan(a) else float("nan")
        rn = len(pairs[t][0])
        rr = retest_correlation(*pairs[t]) if rn >= 3 else float("nan")
        conv = float("nan")
        if bfi:
            common = [w for w in sessions_first if w in bfi]
            if len(common) >= 3:
                conv = pearson_r([float(sessions_first[w][t]) for w in common], [float(bfi[w][t]) for w in common])
        print(f"{t:<18}{n:>4}{a:>8.2f}{f'[{lo:.2f}, {hi:.2f}]':>18}{a8:>16.2f}{rn:>10}{rr:>10.2f}{conv:>13.2f}")
    print("\nnan = not estimable with the available data (too few respondents or zero variance).")


if __name__ == "__main__":
    main()
