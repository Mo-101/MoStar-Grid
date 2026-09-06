"""CypherGuard unit and integration tests."""

import pytest

from cypher_guard import (
    CypherGuard,
    CypherGuardViolation,
    CypherClassification,
    AttestedMigrationGuard,
)


@pytest.fixture
def guard():
    return CypherGuard()


@pytest.fixture
def write_guard():
    return CypherGuard(allow_write=True)


# ── Read queries ────────────────────────────────────────────────

def test_allow_match_return(guard):
    guard.assert_allowed("MATCH (n) RETURN n")


def test_allow_fulltext_procedure(guard):
    guard.assert_allowed(
        "CALL db.index.fulltext.queryNodes('gridSearch', $query) YIELD node, score RETURN node"
    )


def test_allow_string_literal_with_destructive_text(guard):
    # The destructive words are inside a string literal; executable Cypher is
    # just a RETURN, so this must not false-positive.
    guard.assert_allowed('RETURN "DETACH DELETE" AS text')


def test_allow_parameter_with_destructive_text(guard):
    guard.assert_allowed("MATCH (n {text: $text}) RETURN n")


def test_allow_optional_match(guard):
    guard.assert_allowed("OPTIONAL MATCH (n:Memory {cluster_id: $id}) RETURN n")


def test_allow_where_order_limit(guard):
    guard.assert_allowed(
        "MATCH (n:Agent) WHERE n.status = 'Operational' RETURN n ORDER BY n.created_at DESC LIMIT 10"
    )


def test_allow_call_subquery(guard):
    guard.assert_allowed("""
        CALL {
            MATCH (n) RETURN count(n) AS nodes
        }
        CALL {
            MATCH ()-[r]->() RETURN count(r) AS relationships
        }
        RETURN nodes, relationships
    """)


# ── Allowed writes ──────────────────────────────────────────────

def test_deny_create_without_allow_write(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("CREATE (n:Agent {name: 'Mo'})")


def test_allow_create_with_allow_write(write_guard):
    write_guard.assert_allowed("CREATE (n:Agent {name: 'Mo'})")


def test_allow_merge_with_allow_write(write_guard):
    write_guard.assert_allowed("MERGE (n:Agent {canonical_id: 'agent:mo'}) ON CREATE SET n.name = 'Mo'")


def test_allow_set_with_allow_write(write_guard):
    write_guard.assert_allowed("MATCH (n:Agent {id: 'a1'}) SET n.status = 'Operational'")


# ── Destructive denials ─────────────────────────────────────────

def test_deny_delete(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("MATCH (n) DELETE n")


def test_deny_detach_delete(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("MATCH (n) DETACH DELETE n")


def test_deny_mixed_case_detach_delete(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("MATCH (n) DeTaCh DeLeTe n")


def test_deny_multiline_detach_delete(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("MATCH (n)\nDETACH\nDELETE n")


def test_deny_comment_obfuscated_destructive(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("/* safe comment */ MATCH (n) DETACH DELETE n")


def test_deny_remove(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("MATCH (n) REMOVE n.status")


def test_deny_drop(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("DROP INDEX my_index")


def test_deny_drop_constraint(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("DROP CONSTRAINT my_constraint")


def test_deny_delete_with_relabel(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("MATCH (n) SET n:ToDelete DELETE n")


# ── Unknown / unclassifiable ────────────────────────────────────

def test_deny_unknown_procedure(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("CALL some.unknown.procedure() YIELD value RETURN value")


def test_deny_load_csv(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("LOAD CSV FROM 'file:///data.csv' AS row CREATE (n:Row {name: row[0]})")


def test_deny_apoc_mutation(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("CALL apoc.nodes.delete(a) YIELD value RETURN value")


def test_deny_empty_query(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("")


def test_deny_only_whitespace(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("   \n  ")


# ── Attested migration bypass ───────────────────────────────────

def test_attested_migration_allows_destructive():
    mg = AttestedMigrationGuard("mig-2026-001", "Drop legacy constraint")
    mg.assert_allowed("DROP CONSTRAINT legacy_constraint")


def test_attested_migration_still_classifies_destructive():
    mg = AttestedMigrationGuard("mig-2026-002", "Remove test nodes")
    verdict = mg.classify("MATCH (n:Test) DETACH DELETE n")
    assert verdict.classification == CypherClassification.DESTRUCTIVE
    assert verdict.attested
    assert verdict.migration_id == "mig-2026-002"


# ── Normalisation edge cases ────────────────────────────────────

def test_deny_case_folding(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("MATCH (n) DELETE N")


def test_deny_with_inline_comment(guard):
    with pytest.raises(CypherGuardViolation):
        guard.assert_allowed("MATCH (n) // careful now\nDELETE n")


def test_allow_destructive_word_in_backtick_id(guard):
    # Node with a backtick name containing the word DELETE should not be
    # treated as the DELETE clause.
    guard.assert_allowed("MATCH (n:`DELETE`) RETURN n")


def test_classification_returns_destuctive_for_detach_delete():
    guard = CypherGuard()
    verdict = guard.classify("MATCH (a:Agent {id: $id}) WITH a, a.name AS name DETACH DELETE a RETURN name")
    assert verdict.classification == CypherClassification.DESTRUCTIVE
