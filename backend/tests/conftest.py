"""Shared test configuration."""

import os

os.environ.setdefault("MINDTRACE_JWT_SECRET", "test-secret-that-is-at-least-thirty-two-characters")
