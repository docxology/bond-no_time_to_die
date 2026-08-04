"""Pytest configuration for the no_time_to_die (HERACLES) package."""

from __future__ import annotations

import os
import sys

# Headless matplotlib backend — figures must never open a window.
os.environ.setdefault("MPLBACKEND", "Agg")

# This package uses a src-layout; make both the package src/ and the repo root
# importable so `uv run pytest tests/` works from a clean environment. bond-api
# is installed as a local path dependency via `uv sync` and needs no path hack.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
for _path in (SRC, ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)
