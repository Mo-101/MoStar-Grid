"""Runtime tests for `mo-mind-cypher-guard-001`."""
from __future__ import annotations

import hashlib


def test_sealed_template_allowed(engine):
    query = "MATCH (m:Memory {subject: $subject_id}) RETURN m"
    h = hashlib.sha256(query.encode()).hexdigest()
    engine.register_cypher_template("memory-by-subject-001", query, h)
    dec = engine.evaluate(
        "mo-mind-cypher-guard-001",
        {
            "query_key": "memory-by-subject-001",
            "params": {"subject_id": "abc"},
            "request_origin": "mind",
        },
        principal="user-1",
    )
    assert dec.decision == "ALLOW"
    assert dec.result["query"] == query
    assert "$subject_id" in dec.result["query"]
    assert dec.result["params"]["subject_id"] == "abc"


def test_unknown_template_denied(engine):
    dec = engine.evaluate(
        "mo-mind-cypher-guard-001",
        {
            "query_key": "memory-by-unknown-001",
            "params": {},
            "request_origin": "mind",
        },
        principal="user-1",
    )
    assert dec.decision == "DENY"
    assert "UNKNOWN_TEMPLATE" in dec.reason_codes


def test_raw_cypher_denied(engine):
    dec = engine.evaluate(
        "mo-mind-cypher-guard-001",
        {
            "query_key": "MATCH (n) DETACH DELETE n",
            "params": {},
            "request_origin": "mind",
        },
        principal="user-1",
    )
    assert dec.decision == "DENY"
    assert "RAW_CYPHER" in dec.reason_codes


def test_bad_template_hash_denied(engine):
    query = "MATCH (m:Memory {subject: $subject_id}) RETURN m"
    engine.register_cypher_template("bad-hash-001", query, "deadbeef")
    dec = engine.evaluate(
        "mo-mind-cypher-guard-001",
        {
            "query_key": "bad-hash-001",
            "params": {},
            "request_origin": "mind",
        },
        principal="user-1",
    )
    assert dec.decision == "DENY"
    assert "TAMPERED_TEMPLATE" in dec.reason_codes


def test_parameter_value_cannot_alter_query(engine):
    query = "MATCH (m:Memory {subject: $subject_id}) RETURN m"
    h = hashlib.sha256(query.encode()).hexdigest()
    engine.register_cypher_template("memory-by-subject-001", query, h)
    dec = engine.evaluate(
        "mo-mind-cypher-guard-001",
        {
            "query_key": "memory-by-subject-001",
            "params": {"subject_id": "DETACH DELETE n"},
            "request_origin": "mind",
        },
        principal="user-1",
    )
    assert dec.decision == "ALLOW"
    assert dec.result["query"] == query
    assert "DETACH DELETE n" in dec.result["params"]["subject_id"]
