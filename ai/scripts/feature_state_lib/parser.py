"""Extracted from ai/scripts/feature-state.py by a behavior-preserving refactor
(mechanical reorganization only -- no logic changes). See feature-state.py's own
module docstring and the package-level notes for the split rationale.
"""

from __future__ import annotations

import argparse


def add_common_state_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--state-file")
    parser.add_argument("--expect-revision", type=int)
    parser.add_argument("--actor", default="orchestrator")
    parser.add_argument("--event-id")
