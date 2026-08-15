"""Constitutional negative fixtures.

Each fixture seeds a governance graph inside a transaction that is ALWAYS
rolled back. The baseline schema stays installed in the test database; the
fixture never survives. Rollback is stronger than cleanup Cypher: cleanup
that silently fails leaves state behind and poisons the next fixture.

`expect` maps gate name -> expected violating id, or None for "must be
clean". A fixture that declares an expectation and gets zero rows is an
ERROR, not a pass.
"""
from __future__ import annotations

VALID = """
CREATE (cl:Claim {canonical_id:'fx:claim', status:'ACCEPTED', active:true,
                  ingested_by:'fx:ingestor'})
CREATE (c:AdjudicationCase {canonical_id:'fx:case', status:'DECIDED',
                            ingested_by:'fx:ingestor'})
CREATE (panel:ReviewPanel {canonical_id:'fx:panel', status:'ACTIVE',
                           quorum_required:2, min_distinct_voters:2})
CREATE (r1:Adjudicator {canonical_id:'fx:adj1', status:'ACTIVE'})
CREATE (r2:Adjudicator {canonical_id:'fx:adj2', status:'ACTIVE'})
CREATE (d:AdjudicationDecision {canonical_id:'fx:decision', status:'RATIFIED',
                                outcome:'ACCEPT', quorum_verified:true,
                                valid_vote_count:2, accept_vote_count:2,
                                reject_vote_count:0})
CREATE (e:CanonicalExecutor {canonical_id:'fx:executor', status:'ACTIVE',
                             review_authority:false})
CREATE (p:CanonicalPromotion {canonical_id:'fx:promotion', status:'COMPLETED'})
CREATE (v1:AdjudicationVote {canonical_id:'fx:vote1', status:'CAST',
                             choice:'ACCEPT', signature_verified:true})
CREATE (v2:AdjudicationVote {canonical_id:'fx:vote2', status:'CAST',
                             choice:'ACCEPT', signature_verified:true})
CREATE (c)-[:REVIEWS]->(cl)
CREATE (panel)-[:ASSIGNED_TO]->(c)
CREATE (panel)-[:HAS_MEMBER]->(r1)
CREATE (panel)-[:HAS_MEMBER]->(r2)
CREATE (d)-[:DECIDES]->(c)
CREATE (d)-[:RESOLVES]->(cl)
CREATE (d)-[:ISSUED_BY]->(panel)
CREATE (p)-[:PROMOTED]->(cl)
CREATE (p)-[:AUTHORIZED_BY]->(d)
CREATE (p)-[:EXECUTED_BY]->(e)
CREATE (v1)-[:CAST_BY]->(r1)
CREATE (v1)-[:FOR_CASE]->(c)
CREATE (v1)-[:FOR_CLAIM]->(cl)
CREATE (v2)-[:CAST_BY]->(r2)
CREATE (v2)-[:FOR_CASE]->(c)
CREATE (v2)-[:FOR_CLAIM]->(cl)
"""

# name -> (extra cypher appended to VALID, expectations)
FIXTURES: list[tuple[str, str, dict[str, str | None]]] = [

    ("complete_valid_chain", "", {
        "promotion_presence": None, "promotion_shape": None,
        "authorization_cardinality": None, "executor_cardinality": None,
        "decision_topology": None, "quorum_recomputation": None,
        "vocabulary_drift": None,
    }),

    ("accepted_claim_no_promotion", """
        MATCH (p:CanonicalPromotion {canonical_id:'fx:promotion'})
        DETACH DELETE p
    """, {"promotion_presence": "fx:claim", "promotion_shape": None,
          "authorization_cardinality": None, "executor_cardinality": None,
          "decision_topology": None, "vocabulary_drift": None}),

    ("promotion_pending", """
        MATCH (p:CanonicalPromotion {canonical_id:'fx:promotion'})
        SET p.status = 'PENDING'
    """, {"promotion_presence": "fx:claim", "promotion_shape": "fx:promotion",
          "authorization_cardinality": None, "executor_cardinality": None,
          "vocabulary_drift": None}),

    ("missing_authorized_by", """
        MATCH (:CanonicalPromotion {canonical_id:'fx:promotion'})
              -[r:AUTHORIZED_BY]->() DELETE r
    """, {"promotion_presence": "fx:claim", "promotion_shape": None,
          "authorization_cardinality": "fx:promotion",
          "executor_cardinality": None, "vocabulary_drift": None}),

    # THE decisive fixture: a valid path AND a forged one.
    ("valid_plus_forged_authorized_by", """
        MATCH (p:CanonicalPromotion {canonical_id:'fx:promotion'})
        CREATE (bad:AdjudicationDecision {canonical_id:'fx:decision:forged',
                status:'DRAFT', outcome:'ACCEPT', quorum_verified:false})
        CREATE (p)-[:AUTHORIZED_BY]->(bad)
    """, {"promotion_presence": None,          # A still PASSES - that is the point
          "promotion_shape": None,
          "authorization_cardinality": "fx:promotion",   # B2 catches it
          "executor_cardinality": None, "vocabulary_drift": None}),

    ("missing_executed_by", """
        MATCH (:CanonicalPromotion {canonical_id:'fx:promotion'})
              -[r:EXECUTED_BY]->() DELETE r
    """, {"promotion_presence": "fx:claim", "promotion_shape": None,
          "authorization_cardinality": None,
          "executor_cardinality": "fx:promotion", "vocabulary_drift": None}),

    ("valid_plus_rogue_executor", """
        MATCH (p:CanonicalPromotion {canonical_id:'fx:promotion'})
        CREATE (bad:CanonicalExecutor {canonical_id:'fx:executor:rogue',
                status:'ACTIVE', review_authority:true})
        CREATE (p)-[:EXECUTED_BY]->(bad)
    """, {"promotion_presence": None,          # A PASSES
          "executor_cardinality": "fx:promotion",         # B3 catches it
          "authorization_cardinality": None, "vocabulary_drift": None}),

    ("executor_review_authority_true", """
        MATCH (e:CanonicalExecutor {canonical_id:'fx:executor'})
        SET e.review_authority = true
    """, {"promotion_presence": "fx:claim",
          "executor_cardinality": "fx:promotion",
          "authorization_cardinality": None, "vocabulary_drift": None}),

    ("executor_also_adjudicator", """
        MATCH (e:CanonicalExecutor {canonical_id:'fx:executor'})
        SET e:Adjudicator
    """, {"promotion_presence": "fx:claim",
          "executor_cardinality": "fx:promotion",
          "authorization_cardinality": None, "vocabulary_drift": None}),

    ("missing_reviews", """
        MATCH (:AdjudicationCase {canonical_id:'fx:case'})-[r:REVIEWS]->() DELETE r
    """, {"promotion_presence": "fx:claim", "decision_topology": "fx:promotion",
          "authorization_cardinality": None, "executor_cardinality": None,
          "vocabulary_drift": None}),

    ("extra_forged_decides", """
        MATCH (d:AdjudicationDecision {canonical_id:'fx:decision'})
        CREATE (c2:AdjudicationCase {canonical_id:'fx:case:forged', status:'OPEN'})
        CREATE (d)-[:DECIDES]->(c2)
    """, {"promotion_presence": None,          # A PASSES
          "decision_topology": "fx:promotion",            # B4 catches it
          "authorization_cardinality": None, "vocabulary_drift": None}),

    ("promotes_typo", """
        MATCH (p:CanonicalPromotion {canonical_id:'fx:promotion'})
        MATCH (cl:Claim {canonical_id:'fx:claim'})
        MATCH (p)-[r:PROMOTED]->(cl) DELETE r
        CREATE (p)-[:PROMOTES]->(cl)
    """, {"promotion_presence": "fx:claim",
          "vocabulary_drift": "PROMOTES"}),

    # ── quorum: the cache lies, the vote graph tells the truth ──────────
    ("forged_quorum_no_votes", """
        MATCH (v:AdjudicationVote) DETACH DELETE v
    """, {"quorum_recomputation": "fx:decision", "promotion_presence": None,
          "authorization_cardinality": None, "vocabulary_drift": None}),

    ("duplicate_votes_one_reviewer", """
        MATCH (v:AdjudicationVote {canonical_id:'fx:vote2'}) DETACH DELETE v
        WITH 1 AS _
        MATCH (r1:Adjudicator {canonical_id:'fx:adj1'})
        MATCH (c:AdjudicationCase {canonical_id:'fx:case'})
        MATCH (cl:Claim {canonical_id:'fx:claim'})
        CREATE (dup:AdjudicationVote {canonical_id:'fx:vote:dup', status:'CAST',
                choice:'ACCEPT', signature_verified:true})
        CREATE (dup)-[:CAST_BY]->(r1)
        CREATE (dup)-[:FOR_CASE]->(c)
        CREATE (dup)-[:FOR_CLAIM]->(cl)
    """, {"quorum_recomputation": "fx:decision", "vocabulary_drift": None}),

    ("unsigned_vote_counted", """
        MATCH (v:AdjudicationVote {canonical_id:'fx:vote2'})
        SET v.signature_verified = false
    """, {"quorum_recomputation": "fx:decision", "vocabulary_drift": None}),

    ("recused_reviewer_counted", """
        MATCH (r2:Adjudicator {canonical_id:'fx:adj2'})
        MATCH (c:AdjudicationCase {canonical_id:'fx:case'})
        CREATE (r2)-[:RECUSED_FROM]->(c)
    """, {"quorum_recomputation": "fx:decision", "vocabulary_drift": None}),
]
