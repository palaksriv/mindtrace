"""Enforce the telemetry retention period.

Usage (from ``backend/``)::

    python -m scripts.purge_telemetry --older-than-days 30 [--dry-run]

Deletes behavioural telemetry rows belonging to sessions that were completed
more than N days ago. Questionnaire responses and trait scores are kept; only
the camera-derived samples are removed. See docs/ETHICS_AND_PRIVACY.md.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import SessionLocal, create_database_tables
from app.models.assessment import BehaviorTelemetry, Session, SessionStatus


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--older-than-days", type=int, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.older_than_days < 0:
        raise SystemExit("--older-than-days must be >= 0")

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.older_than_days)
    create_database_tables()
    with SessionLocal() as db:
        ids = [
            s.id
            for s in db.scalars(
                select(Session).where(Session.status == SessionStatus.COMPLETED)
            ).all()
            if s.completed_at is not None
            and (s.completed_at if s.completed_at.tzinfo else s.completed_at.replace(tzinfo=timezone.utc)) < cutoff
        ]
        query = db.query(BehaviorTelemetry).filter(BehaviorTelemetry.session_id.in_(ids)) if ids else None
        count = query.count() if query is not None else 0
        if args.dry_run or not count:
            print(f"{'Would delete' if args.dry_run else 'Nothing to delete:'} {count} telemetry rows from {len(ids)} sessions.")
            return
        query.delete(synchronize_session=False)
        db.commit()
        print(f"Deleted {count} telemetry rows from {len(ids)} sessions completed before {cutoff.date()}.")


if __name__ == "__main__":
    main()
