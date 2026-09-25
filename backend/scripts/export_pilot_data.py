"""Export a pseudonymised research dataset for pilot-study analysis.

Usage (from ``backend/``)::

    export MINDTRACE_EXPORT_SALT="<long random secret kept off the dataset>"
    python -m scripts.export_pilot_data --out exports

Writes two CSV files:

* ``item_responses.csv``  - one row per answered item (keyed score, latency).
* ``session_summary.csv`` - one row per completed session (trait scores and
  behavioural indicators).

Student identifiers are replaced by a salted HMAC-SHA256 pseudonym; names and
e-mail addresses are never exported. Only sessions with a *granted* consent
record are included, so unconsented data cannot leak into analysis.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import os
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import SessionLocal, create_database_tables
from app.models.assessment import (
    BehaviorTelemetry,
    ConsentRecord,
    Response,
    Session,
    SessionStatus,
)
from app.services.analytics.behavior_analytics import calculate_behavioral_analytics
from app.services.scoring import calculate_trait_scores


def pseudonym(student_id: int, salt: str) -> str:
    digest = hmac.new(salt.encode(), str(student_id).encode(), hashlib.sha256)
    return digest.hexdigest()[:16]


def keyed_score(response: Response) -> int:
    return 6 - response.response if response.question.reverse_scored else response.response


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="exports", help="output directory")
    args = parser.parse_args()

    salt = os.environ.get("MINDTRACE_EXPORT_SALT", "")
    if len(salt) < 16:
        raise SystemExit("Set MINDTRACE_EXPORT_SALT to a random secret of at least 16 characters.")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    create_database_tables()

    with SessionLocal() as db, (out / "item_responses.csv").open("w", newline="") as f_items, (
        out / "session_summary.csv"
    ).open("w", newline="") as f_sessions:
        items = csv.writer(f_items)
        sessions = csv.writer(f_sessions)
        items.writerow(["pseudonym", "session_id", "question_order", "trait", "reverse_keyed", "raw", "keyed", "latency_ms"])
        traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        sessions.writerow(
            ["pseudonym", "session_id", "completed_at", *traits, "telemetry_samples", "face_presence_pct",
             "center_both_pct", "movement_score", "deviation_score", "deviation_level", "mean_latency_ms"]
        )
        completed = db.scalars(
            select(Session).where(Session.status == SessionStatus.COMPLETED).order_by(Session.completed_at)
        ).all()
        exported = skipped = 0
        for s in completed:
            consent = db.scalar(select(ConsentRecord).where(ConsentRecord.session_id == s.id))
            if consent is None or not consent.granted:
                skipped += 1
                continue
            who = pseudonym(s.student_id, salt)
            responses = db.scalars(
                select(Response).options(joinedload(Response.question)).where(Response.session_id == s.id)
            ).all()
            for r in sorted(responses, key=lambda x: x.question.order):
                items.writerow([who, s.id, r.question.order, r.question.trait.value,
                                int(r.question.reverse_scored), r.response, keyed_score(r), r.latency_ms])
            telemetry = db.scalars(
                select(BehaviorTelemetry).where(BehaviorTelemetry.session_id == s.id)
            ).all()
            a = calculate_behavioral_analytics(telemetry, responses)
            scores = calculate_trait_scores(responses)
            sessions.writerow([
                who, s.id, s.completed_at.isoformat(), *[scores[t] for t in traits],
                a["sample_count"], a["face_presence_percent"],
                a["gaze_distribution"].get("center_both_percent", 0.0), a["head_movement"]["movement_score"],
                a["behavioral_deviation"]["score"], a["behavioral_deviation"]["level"],
                a["response_latency"]["average_latency_ms"],
            ])
            exported += 1
    print(f"Exported {exported} consented sessions to {out}/ (skipped {skipped} without granted consent).")


if __name__ == "__main__":
    main()
