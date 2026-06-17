"""
cypher_guard.py — Destruction Firewall (the wall).
Every Neo4j write in every service goes through run_cypher(). No exceptions.

The wall is static deny. The ONLY lawful door through it is keeper_gate.py,
which demands three keys and never opens toward the production port.
"""

import re

# Patterns of destruction — including every APOC long-way-around the cliff.
FORBIDDEN = [
    r"DETACH\s+DELETE",
    r"DROP\s+(DATABASE|CONSTRAINT|INDEX|GRAPH)",
    r"CREATE\s+OR\s+REPLACE\s+DATABASE",
    r"APOC\.PERIODIC\.ITERATE",
    r"APOC\.PERIODIC\.COMMIT",
    r"APOC\.NODES\.DELETE",
    r"APOC\.REFACTOR\.",
    r"APOC\.SCHEMA\.ASSERT",
    r"APOC\.CYPHER\.RUN",                       # arbitrary cypher tunnel
    r"APOC\.DO\.(WHEN|CASE)",                   # conditional cypher tunnel
]

_COMPILED = [re.compile(p) for p in FORBIDDEN]


class BlockedCypher(RuntimeError):
    """The wall. It does not negotiate."""


def assert_safe_cypher(query: str) -> None:
    compact = " ".join(query.strip().split())
    upper = compact.upper()

    for pat in _COMPILED:
        if pat.search(upper):
            raise BlockedCypher(f"Firewall: destructive pattern → {compact[:180]}")

    # Broad DELETE without a narrowing clause (WHERE or inline property match)
    if "DELETE" in upper and "WHERE" not in upper and not re.search(r"\{\s*\w", compact):
        raise BlockedCypher(f"Firewall: DELETE without WHERE/property match → {compact[:180]}")


def run_cypher(session, query: str, **params):
    """The one true entry point. Builders import this, never session.run directly."""
    assert_safe_cypher(query)
    return session.run(query, **params)
