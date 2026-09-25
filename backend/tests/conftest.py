"""Shared test configuration.

Tests run against a throw-away SQLite file so they never touch (or pollute)
a developer's local ``mindtrace.db``.
"""

import atexit
import os
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="mindtrace-tests-"))
os.environ["MINDTRACE_DATABASE_URL"] = f"sqlite:///{(_tmp / 'test.db').as_posix()}"
os.environ.setdefault("MINDTRACE_JWT_SECRET", "test-secret-that-is-at-least-thirty-two-characters")
os.environ["MINDTRACE_COUNSELLOR_INVITE_CODE"] = "test-invite-code"
os.environ["MINDTRACE_ALLOW_DATA_WIPE"] = "false"

INVITE_CODE = "test-invite-code"


@atexit.register
def _cleanup() -> None:  # pragma: no cover
    import shutil

    shutil.rmtree(_tmp, ignore_errors=True)
