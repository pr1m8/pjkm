"""Shared utility functions for pjkm core."""

from __future__ import annotations


def deep_merge(target: dict, dotted_key: str, value: dict) -> None:
    """Merge a dotted key (e.g., 'ruff.lint') into a nested dict structure.

    Given target={'tool': {}}, dotted_key='ruff.lint', value={'select': ['E']},
    produces target={'tool': {'ruff': {'lint': {'select': ['E']}}}}.
    """
    parts = dotted_key.split(".")
    current = target
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current.setdefault(parts[-1], {}).update(value)
