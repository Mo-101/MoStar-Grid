#!/usr/bin/env python3
"""Governance Cypher constitutional guard.

TWO INVARIANTS, both enforced on governance source only:

    1. TYPED        every bracketed relationship pattern declares a type
    2. VOCABULARY   that type is in the closed constitutional vocabulary

    untyped        -> reject   (a)-[]->(b)  (a)-[r]->(b)  (a)-[_TO]->(b)
    unknown typed  -> reject   (a)-[:PROMOTES]->(b)
    known typed    -> accept   (a)-[:PROMOTED]->(b)

WHY BOTH
    Valid Cypher is not sufficient. Neo4j permits a relationship variable
    with no type expression, so `-[r]->` matches EVERY relationship type in
    the graph: a promotion gate written that way reports "no illegal
    promotions" while proving nothing. And `PROMOTES` for `PROMOTED` parses
    perfectly while asserting something that does not exist — the gate runs
    green over an empty match. Rule 1 catches the first, rule 2 the second.

SCOPE — this matters
    Applied repo-wide, rule 1 flags ~20 legitimate census/discovery queries
    (`MATCH ()-[r]->() RETURN type(r), count(*)`) which MUST stay untyped.
    Failing those would train people to bypass the hook. So the guard runs
    on GOVERNANCE_PATHS only; deliberate untyped discovery lives under
    core/ops/audit/ and is explicitly exempt.

LIMITS
    A regex guard, deliberately — replace with parser/AST validation later.
    It also cannot see relationships created out-of-band against the live
    database; that is covered by
    core/ops/audit/neo4j/governance_vocabulary_drift.cypher

USAGE
    validate_governance_cypher.py FILE [FILE...]   # explicit files
    validate_governance_cypher.py --all            # scan governance paths
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# Source trees under constitutional enforcement.
GOVERNANCE_PATHS = (
    "core/ops/governance/",
)

# Exempt: intentionally untyped discovery/census queries.
EXEMPT_PATHS = (
    "core/ops/audit/",
)

try:
    sys.path.insert(0, str(REPO_ROOT / "core" / "ops" / "governance" / "neo4j"))
    from constitution.relationship_types import GOVERNANCE_RELATIONSHIPS
except Exception:  # pragma: no cover - vocabulary must never be silently empty
    print(
        "FATAL: cannot import GOVERNANCE_RELATIONSHIPS from "
        "core/ops/governance/neo4j/constitution/relationship_types.py",
        file=sys.stderr,
    )
    raise

REL_PATTERN = re.compile(r"<-\[[^\]]*\]-|-\[[^\]]*\]->|-\[[^\]]*\]-")
BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT = re.compile(r"//[^\n]*")
# Type expression: :A, r:A, r:A|B, :A*1..3, with optional whitespace.
TYPE_TOKENS = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _strip_comments(text: str) -> str:
    """Blank comments, preserving newlines so line numbers stay correct."""

    def blank(m: re.Match) -> str:
        return re.sub(r"[^\n]", " ", m.group(0))

    return LINE_COMMENT.sub(blank, BLOCK_COMMENT.sub(blank, text))


def _is_exempt(path: Path) -> bool:
    rel = path.resolve().as_posix()
    return any(f"/{p}" in rel or rel.startswith(p) for p in EXEMPT_PATHS)


def check_file(path: Path) -> list[str]:
    text = _strip_comments(path.read_text(encoding="utf-8"))
    problems: list[str] = []

    for match in REL_PATTERN.finditer(text):
        raw = match.group(0)
        inside = re.search(r"\[([^\]]*)\]", raw)
        if not inside:
            continue

        # Only the declaration carries the type; property maps and WHERE
        # predicates legitimately contain ':' and must not satisfy the check.
        declaration = re.split(r"\{|\bWHERE\b", inside.group(1), maxsplit=1)[0].strip()
        line = text.count("\n", 0, match.start()) + 1

        if ":" not in declaration:
            problems.append(f"{path}:{line}: UNTYPED GOVERNANCE RELATIONSHIP: {raw}")
            continue

        # Everything after the first ':' is the type expression. Variable
        # length (*1..3) and alternation (A|B) are permitted; each named
        # alternative must be constitutional.
        type_expr = declaration.split(":", 1)[1]
        type_expr = type_expr.split("*", 1)[0]
        for token in TYPE_TOKENS.findall(type_expr):
            if token not in GOVERNANCE_RELATIONSHIPS:
                problems.append(
                    f"{path}:{line}: NON-CONSTITUTIONAL RELATIONSHIP TYPE "
                    f"{token!r} in {raw} — not in the closed vocabulary "
                    f"({len(GOVERNANCE_RELATIONSHIPS)} members). Adding one is "
                    f"a constitutional amendment."
                )

    return problems


def governance_files() -> list[Path]:
    out: list[Path] = []
    for base in GOVERNANCE_PATHS:
        root = REPO_ROOT / base
        if root.is_dir():
            out.extend(sorted(root.rglob("*.cypher")))
    return [p for p in out if not _is_exempt(p)]


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--all":
        paths = governance_files()
    else:
        paths = [Path(a) for a in argv]

    if not paths:
        print("usage: validate_governance_cypher.py [--all | FILE ...]", file=sys.stderr)
        return 2

    problems: list[str] = []
    scanned = 0
    for path in paths:
        if not path.is_file():
            continue
        if _is_exempt(path):
            print(f"  exempt (audit path): {path}")
            continue
        scanned += 1
        problems.extend(check_file(path))

    for p in problems:
        print(p)

    if problems:
        print(
            f"\nFAILED: {len(problems)} violation(s) across {scanned} governance file(s).",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK: {scanned} governance file(s) scanned; all relationships typed and "
        f"within the {len(GOVERNANCE_RELATIONSHIPS)}-member constitutional vocabulary."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
