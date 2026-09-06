"""
CYPHER_GUARD — deny-by-default Cypher policy layer.

Enforces that no Cypher query reaches the Neo4j driver without
normalisation, classification, and explicit permission.

Doctrine:
  - Destructive clauses (DELETE, DETACH DELETE, REMOVE, DROP, destructive
    procedures) are hard-denied in runtime execution.
  - Unknown or unclassifiable write syntax fails closed.
  - Migrations and fixtures may perform destructive work only through an
    attested MigrationGuard that records migration_id and reason.
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from neo4j import AsyncDriver, AsyncSession, Driver, Session

logger = logging.getLogger("cypher_guard")


class CypherGuardViolation(RuntimeError):
    """Raised when a Cypher query is not allowed by the active guard."""


class CypherClassification:
    READ = "READ"
    WRITE_ALLOWED = "WRITE_ALLOWED"
    DESTRUCTIVE = "DESTRUCTIVE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CypherVerdict:
    classification: str
    normalized: str
    hash: str
    attested: bool = False
    migration_id: Optional[str] = None
    reason: Optional[str] = None


class CypherGuard:
    """Stateful guard.  By default denies all writes and all destructives.

    Runtime callers can request ``allow_write`` context for ``CREATE``,
    ``MERGE`` and ``SET``.  Migrations must use an AttestedMigrationGuard.
    """

    # Core destructive keywords.  These are detected after normalisation and
    # literal extraction, so a keyword inside a string will not trigger them.
    DESTRUCTIVE_KEYWORDS: set[str] = {
        "delete",
        "remove",
        "drop",
    }

    # Keywords that promote a query from READ to WRITE_ALLOWED.
    WRITE_KEYWORDS: set[str] = {
        "create",
        "merge",
        "set",
    }

    # Read-only structural keywords.  Their presence alone does not elevate
    # classification above READ.
    READ_KEYWORDS: set[str] = {
        "match",
        "optional",
        "return",
        "with",
        "unwind",
        "union",
        "all",
        "where",
        "case",
        "when",
        "then",
        "else",
        "end",
        "order",
        "by",
        "asc",
        "desc",
        "limit",
        "skip",
        "as",
        "in",
        "is",
        "null",
        "not",
        "and",
        "or",
        "xor",
        "distinct",
        "count",
        "sum",
        "avg",
        "min",
        "max",
        "collect",
        "exists",
        "starts",
        "ends",
        "contains",
        "size",
        "length",
        "type",
        "labels",
        "keys",
        "properties",
        "nodes",
        "relationships",
        "shortestpath",
        "allshortestpaths",
        "apoc.coll",
        "apoc.convert",
        "apoc.map",
        "apoc.meta",
        "apoc.date",
        "apoc.temporal",
        "apoc.text",
        "apoc.number",
        "apoc.math",
    }

    # Explicitly allowed read procedures.  Anything else starting with a
    # known administrative prefix is considered destructive/unknown.
    ALLOWED_PROCEDURES: set[str] = {
        "db.index.fulltext.queryNodes",
        "db.index.fulltext.queryRelationships",
        "db.schema.visualize",
        "db.schema.nodeTypeProperties",
        "db.schema.relTypeProperties",
        "dbms.components",
        "dbms.functions",
        "dbms.procedures",
    }

    SUSPICIOUS_PROCEDURE_PREFIXES: tuple[str, ...] = (
        "db.index.drop",
        "db.indexes.drop",
        "db.createIndex",
        "db.createUniquePropertyConstraint",
        "db.createProperty.existenceConstraint",
        "db.drop",
        "dbms.kill",
        "dbms.security.",
        "apoc.refactor.",
        "apoc.nodes.delete",
        "apoc.periodic.iterate",
        "apoc.periodic.commit",
        "apoc.cypher.run",
        "apoc.algo.",
    )

    def __init__(
        self,
        allow_write: bool = False,
        attested: bool = False,
        migration_id: Optional[str] = None,
        reason: Optional[str] = None,
        allowed_procedures: Optional[set[str]] = None,
        suspicious_procedure_prefixes: Optional[tuple[str, ...]] = None,
    ):
        self.allow_write = allow_write
        self.attested = attested
        self.migration_id = migration_id
        self.reason = reason
        self.allowed_procedures = {p.lower() for p in (allowed_procedures or self.ALLOWED_PROCEDURES)}
        self.suspicious_procedure_prefixes = tuple(
            p.lower() for p in (suspicious_procedure_prefixes or self.SUSPICIOUS_PROCEDURE_PREFIXES)
        )

    # ── Normalisation ───────────────────────────────────────────────

    @staticmethod
    def normalize(query: str) -> tuple[str, list[str], list[str]]:
        """Return (normalised_query, protected_strings, protected_idents).

        Removes comments, collapses whitespace, lowercases executable Cypher,
        and protects quoted strings and backtick identifiers so literal text
        cannot produce false positives.
        """
        q = query

        # Extract double-quoted strings.
        strings: list[str] = []
        q = re.sub(r'"(?:[^"\\]|\\.)*"', lambda m: CypherGuard._stash(m, strings, "__STR__"), q)

        # Extract single-quoted strings.
        q = re.sub(r"'(?:[^'\\]|\\.)*'", lambda m: CypherGuard._stash(m, strings, "__STR__"), q)

        # Extract backtick identifiers.
        idents: list[str] = []
        q = re.sub(r"`[^`]*`", lambda m: CypherGuard._stash(m, idents, "__ID__"), q)

        # Strip Cypher line comments.
        q = re.sub(r"//.*", " ", q)

        # Strip Cypher block comments (non-greedy).
        q = re.sub(r"/\*.*?\*/", " ", q, flags=re.DOTALL)

        # Collapse whitespace.
        q = " ".join(q.split())

        # Normalise case of executable Cypher; literals are already placeholders.
        q = q.lower()

        # Fold the scoped subquery form `CALL (v) { ... }` (Neo4j 5.23+, and the
        # only form accepted by the server this Grid runs) onto the importing
        # form `CALL { ... }` that classify() already understands.
        #
        # Without this, classify() reads the token after `call` as a procedure
        # name, gets "(v)", takes the part before the paren — the empty string —
        # matches no whitelisted procedure, and falls through to UNKNOWN. Every
        # scoped subquery was therefore denied as unclassifiable, including the
        # sentinel-label probe behind /api/health, which is why mindgraph.ok was
        # false on a connected, healthy graph.
        #
        # This widens parsing, not policy: the variable scope carries no clause,
        # and the subquery body is still scanned token by token, so a write or
        # destructive clause inside it classifies exactly as it did before.
        q = re.sub(r"\bcall\s*\([^()]*\)\s*\{", "call {", q)

        return q, strings, idents

    @staticmethod
    def _stash(match: re.Match, bucket: list[str], token: str) -> str:
        bucket.append(match.group(0))
        return f" {token}_{len(bucket) - 1} "

    # ── Classification ──────────────────────────────────────────────

    def classify(self, query: str) -> CypherVerdict:
        """Classify a Cypher query and return a verdict."""
        normalised, strings, idents = self.normalize(query)
        digest = hashlib.sha256(query.encode("utf-8")).hexdigest()[:24]

        if not normalised:
            return CypherVerdict(
                classification=CypherClassification.UNKNOWN,
                normalized=normalised,
                hash=digest,
                attested=self.attested,
                migration_id=self.migration_id,
                reason=self.reason,
            )

        tokens = normalised.split()
        classification = CypherClassification.READ

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token == "detach" and i + 1 < len(tokens) and tokens[i + 1] == "delete":
                classification = CypherClassification.DESTRUCTIVE
                i += 2
                continue

            if token in self.DESTRUCTIVE_KEYWORDS:
                classification = CypherClassification.DESTRUCTIVE
                i += 1
                continue

            if token in self.WRITE_KEYWORDS:
                if classification == CypherClassification.READ:
                    classification = CypherClassification.WRITE_ALLOWED

            if token == "call":
                proc = tokens[i + 1] if i + 1 < len(tokens) else ""
                proc = proc.split("(")[0].strip()
                if proc == "{":
                    # CALL { ... } subquery — continue linear scan; inner clauses will be
                    # classified by their own tokens. Do not treat the opening brace as
                    # a procedure name.
                    i += 1
                    continue
                if proc in self.allowed_procedures:
                    # allowed read procedure; do not change classification
                    pass
                elif proc.startswith(self.suspicious_procedure_prefixes):
                    classification = CypherClassification.DESTRUCTIVE
                else:
                    # Any non-whitelisted procedure is unknown and therefore denied.
                    classification = CypherClassification.UNKNOWN

            # Administrative / bulk commands we refuse to classify safely.
            if token in {"load", "foreach", "admin", "using", "periodic", "commit"}:
                classification = CypherClassification.UNKNOWN

            i += 1

        return CypherVerdict(
            classification=classification,
            normalized=normalised,
            hash=digest,
            attested=self.attested,
            migration_id=self.migration_id,
            reason=self.reason,
        )

    # ── Enforcement ─────────────────────────────────────────────────

    def assert_allowed(self, query: str, context: Optional[dict[str, Any]] = None) -> CypherVerdict:
        """Fail closed.  Returns the verdict if allowed, raises otherwise."""
        verdict = self.classify(query)

        if self.attested:
            logger.warning(
                "Attested destructive Cypher allowed: migration=%s reason=%s hash=%s",
                self.migration_id,
                self.reason,
                verdict.hash,
            )
            return verdict

        if verdict.classification == CypherClassification.DESTRUCTIVE:
            raise CypherGuardViolation(
                f"DESTRUCTIVE Cypher denied (hash={verdict.hash}): {query[:200]}"
            )

        if verdict.classification == CypherClassification.UNKNOWN:
            raise CypherGuardViolation(
                f"Unclassifiable Cypher denied (fail closed, hash={verdict.hash}): {query[:200]}"
            )

        if verdict.classification == CypherClassification.WRITE_ALLOWED:
            ctx = context or {}
            if not (self.allow_write or ctx.get("allow_write")):
                raise CypherGuardViolation(
                    f"WRITE Cypher denied without allow_write (hash={verdict.hash}): {query[:200]}"
                )

        return verdict


class AttestedMigrationGuard(CypherGuard):
    """Explicit, machine-visible bypass for approved schema/canopy migrations.

    Constructing this guard requires a migration_id and a human-readable
    reason.  All destructive Cypher executed under this guard is logged.
    """

    def __init__(self, migration_id: str, reason: str):
        super().__init__(
            attested=True,
            migration_id=migration_id,
            reason=reason,
        )

    def assert_allowed(self, query: str, context: Optional[dict[str, Any]] = None) -> CypherVerdict:
        verdict = super().assert_allowed(query, context)
        # Record an attestation event for governance ledger compatibility.
        logger.info(
            "MIGRATION_ATTESTATION migration_id=%s reason=%s hash=%s query_start=%s",
            self.migration_id,
            self.reason,
            verdict.hash,
            query[:120],
        )
        return verdict


# ── Guarded Neo4j primitives ──────────────────────────────────────

@dataclass
class _ExecutionContext:
    guard: CypherGuard
    runtime_context: dict[str, Any] = field(default_factory=dict)


class GuardedAsyncSession:
    """Async session that asserts the guard before every run()."""

    def __init__(self, session: AsyncSession, context: _ExecutionContext):
        self._session = session
        self._ctx = context

    async def __aenter__(self) -> "GuardedAsyncSession":
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return await self._session.__aexit__(exc_type, exc, tb)

    async def run(self, query: str, *args, **kwargs):
        self._ctx.guard.assert_allowed(query, self._ctx.runtime_context)
        return await self._session.run(query, *args, **kwargs)

    # Forward other common session methods without bypass.
    async def close(self):
        return await self._session.close()

    @property
    def last_bookmark(self):
        return self._session.last_bookmark


class GuardedAsyncDriver:
    """Async driver whose session() returns a GuardedAsyncSession.

    This is the construction-point choke: every query that leaves the
    application through this driver passes the guard.
    """

    def __init__(
        self,
        driver: AsyncDriver,
        guard: Optional[CypherGuard] = None,
        context: Optional[dict[str, Any]] = None,
    ):
        self._driver = driver
        self._guard = guard or CypherGuard()
        self._runtime_context = context or {}

    def session(self, *args, **kwargs) -> GuardedAsyncSession:
        raw = self._driver.session(*args, **kwargs)
        ctx = _ExecutionContext(guard=self._guard, runtime_context=dict(self._runtime_context))
        return GuardedAsyncSession(raw, ctx)

    async def verify_connectivity(self, **kwargs):
        return await self._driver.verify_connectivity(**kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._driver.close()

    async def close(self):
        return await self._driver.close()


class GuardedSyncSession:
    """Sync session that asserts the guard before every run()."""

    def __init__(self, session: Session, context: _ExecutionContext):
        self._session = session
        self._ctx = context

    def __enter__(self) -> "GuardedSyncSession":
        return self

    def __exit__(self, exc_type, exc, tb):
        return self._session.__exit__(exc_type, exc, tb)

    def run(self, query: str, *args, **kwargs):
        self._ctx.guard.assert_allowed(query, self._ctx.runtime_context)
        return self._session.run(query, *args, **kwargs)

    def close(self):
        return self._session.close()


class GuardedSyncDriver:
    """Sync driver whose session() returns a GuardedSyncSession."""

    def __init__(
        self,
        driver: Driver,
        guard: Optional[CypherGuard] = None,
        context: Optional[dict[str, Any]] = None,
    ):
        self._driver = driver
        self._guard = guard or CypherGuard()
        self._runtime_context = context or {}

    def session(self, *args, **kwargs) -> GuardedSyncSession:
        raw = self._driver.session(*args, **kwargs)
        ctx = _ExecutionContext(guard=self._guard, runtime_context=dict(self._runtime_context))
        return GuardedSyncSession(raw, ctx)

    def verify_connectivity(self, **kwargs):
        return self._driver.verify_connectivity(**kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self._driver.close()

    def close(self):
        return self._driver.close()


# ── Convenience factories ─────────────────────────────────────────

def get_guarded_async_driver(
    *args,
    guard: Optional[CypherGuard] = None,
    allow_write: bool = False,
    **kwargs,
) -> GuardedAsyncDriver:
    """Create a GuardedAsyncDriver from neo4j AsyncGraphDatabase driver args."""
    from neo4j import AsyncGraphDatabase

    raw = AsyncGraphDatabase.driver(*args, **kwargs)
    g = guard or CypherGuard(allow_write=allow_write)
    return GuardedAsyncDriver(raw, guard=g)


def get_guarded_sync_driver(
    *args,
    guard: Optional[CypherGuard] = None,
    allow_write: bool = False,
    **kwargs,
) -> GuardedSyncDriver:
    """Create a GuardedSyncDriver from neo4j GraphDatabase driver args."""
    from neo4j import GraphDatabase

    raw = GraphDatabase.driver(*args, **kwargs)
    g = guard or CypherGuard(allow_write=allow_write)
    return GuardedSyncDriver(raw, guard=g)
