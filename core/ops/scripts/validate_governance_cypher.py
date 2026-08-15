#!/usr/bin/env python3
"""Governance Cypher integrity guard — relationship types must be explicit.

INVARIANT
    Every bracketed relationship pattern must declare a relationship type.

WHY THIS EXISTS
    Valid Cypher is not sufficient here. Neo4j's grammar permits a
    relationship variable with no type expression, so `-[r]->` and even
    `-[_TO]->` parse and execute happily — while matching EVERY relationship
    type in the graph. In a constitutional/governance query that is not a
    style problem, it is a correctness problem: an untyped pattern will
    silently accept a path the constitution never authorised.

        (a)-[:PROMOTED]->(b)      constrains to PROMOTED
        (a)-[_TO]->(b)            matches ANY relationship

    A promotion gate written with the second form can report "no illegal
    promotions" while proving nothing at all.

FAILS
    (a)-[]->(b)          (a)-[r]->(b)          (a)-[_TO]->(b)
PASSES
    (a)-[:PROMOTED]->(b)  (a)-[r:ASSIGNED_TO]->(b)  (a)<-[r:AUTHORIZED_BY]-(b)
    (a)-[r:A|B*1..3]->(b)                     (typed, incl. alternation/varlen)

USAGE
    python3 core/ops/scripts/validate_governance_cypher.py FILE [FILE...]
    # exit 0 = clean, exit 1 = untyped pattern found

NOTE
    This is a regex guard, deliberately. It should eventually be replaced by
    parser/AST validation, but the invariant is worth enforcing today.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Bracketed relationship patterns in either direction, or undirected.
REL_PATTERN = re.compile(r"<-\[[^\]]*\]-|-\[[^\]]*\]->|-\[[^\]]*\]-")

# Comments must be stripped first: a commented-out example must not fail CI,
# and a `//` containing a bracket must not be mistaken for a live pattern.
BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT = re.compile(r"//[^\n]*")


def _strip_comments(text: str) -> str:
    """Blank out comments while preserving newline positions for line numbers."""

    def _blank(match: re.Match) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    return LINE_COMMENT.sub(_blank, BLOCK_COMMENT.sub(_blank, text))


def assert_governance_relationship_types(path: Path) -> int:
    raw_text = path.read_text(encoding="utf-8")
    text = _strip_comments(raw_text)

    failures: list[tuple[int, str]] = []

    for match in REL_PATTERN.finditer(text):
        raw = match.group(0)

        inside_match = re.search(r"\[([^\]]*)\]", raw)
        if not inside_match:
            continue

        inside = inside_match.group(1).strip()

        # Only the declaration portion carries the type. Inline property maps
        # and WHERE predicates may legitimately contain ':' characters, so
        # they must not be allowed to satisfy the check.
        declaration = re.split(r"\{|\bWHERE\b", inside, maxsplit=1)[0].strip()

        if ":" not in declaration:
            line = text.count("\n", 0, match.start()) + 1
            failures.append((line, raw))

    for line, pattern in failures:
        print(f"{path}:{line}: UNTYPED GOVERNANCE RELATIONSHIP: {pattern}")

    return len(failures)


def main(argv: list[str]) -> int:
    paths = [Path(a) for a in argv]
    if not paths:
        print("usage: validate_governance_cypher.py FILE [FILE...]", file=sys.stderr)
        return 2

    total = 0
    scanned = 0
    for path in paths:
        if not path.is_file():
            print(f"{path}: not a file — skipped", file=sys.stderr)
            continue
        scanned += 1
        total += assert_governance_relationship_types(path)

    if total:
        print(
            f"\nFAILED: {total} untyped relationship pattern(s) across "
            f"{scanned} file(s). Declare an explicit :TYPE.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: {scanned} file(s) scanned, all relationship patterns typed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
