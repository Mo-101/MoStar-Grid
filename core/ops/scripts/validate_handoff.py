#!/usr/bin/env python3
"""
MoStar Handoff Validator
Pre-commit gate: every commit must be accompanied by a same-day handoff note
under .handoff/ with the required sections filled in.

Exit codes:
  0 — valid, no warnings
  2 — valid, with warnings (commit proceeds)
  1 — invalid / missing (commit blocked)
"""
import datetime
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HANDOFF_DIR = REPO_ROOT / ".handoff"
REQUIRED_SECTIONS = ["## What was done", "## Why", "## Verification"]


def todays_handoff_notes() -> list[Path]:
    today = datetime.date.today().isoformat().replace("-", "")
    if not HANDOFF_DIR.is_dir():
        return []
    return sorted(
        p for p in HANDOFF_DIR.glob(f"{today}_*.md") if p.name != "TEMPLATE.md"
    )


def validate(note: Path) -> list[str]:
    """Return a list of problems with the note (empty = fully valid)."""
    text = note.read_text(encoding="utf-8", errors="ignore")
    problems = []

    if not re.search(r"^# Handoff Note", text, re.MULTILINE):
        problems.append("missing '# Handoff Note' header")

    for section in REQUIRED_SECTIONS:
        if section not in text:
            problems.append(f"missing '{section}' section")

    body_after_sections = len(text.strip())
    if body_after_sections < 80:
        problems.append("note looks too short to be meaningful")

    return problems


def main() -> int:
    notes = todays_handoff_notes()
    if not notes:
        print("No handoff note found for today in .handoff/")
        print("Create one: cp .handoff/TEMPLATE.md "
              ".handoff/$(date +%Y%m%d_%H%M%S)_$(whoami).md")
        return 1

    warnings = []
    for note in notes:
        problems = validate(note)
        if problems:
            warnings.append(f"{note.name}: {'; '.join(problems)}")

    if warnings:
        for w in warnings:
            print(f"WARNING: {w}")
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
