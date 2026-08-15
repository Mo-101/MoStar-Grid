// GATE — QUORUM RECOMPUTATION
//
// ══════════════════════════════════════════════════════════════════════
// `d.quorum_verified = true` IS A CACHE, NOT A WITNESS.
// ══════════════════════════════════════════════════════════════════════
// Every other promotion gate trusts that boolean. But it is just a property
// somebody wrote — anyone able to SET it can manufacture a ratified decision
// with no votes behind it. The authoritative witness is the vote graph:
//
//     AdjudicationVote + CAST_BY + FOR_CASE + FOR_CLAIM
//     + panel membership + signature verification + non-recusal
//
// This gate recomputes quorum from that graph and compares it against the
// stored totals. Disagreement between the recomputation and the cache is
// itself a violation, so a forged summary cannot hide behind a valid-looking
// decision node.
//
// Vote validity requires, per reviewer:
//   - reviewer is a panel member and ACTIVE
//   - reviewer did not ingest the case (no self-review)
//   - reviewer is not RECUSED_FROM the case
//   - exactly ONE vote (size(votes) = 1) — duplicate votes from one
//     reviewer collapse to invalid rather than counting twice
//   - vote is CAST and signature_verified
//   - vote is FOR_CASE this case AND FOR_CLAIM this claim
//
// OPEN CONSTITUTIONAL ISSUE — TEMPORAL SEMANTICS (do not fix here)
//   This is a CURRENT-STATE query being used as HISTORICAL proof.
//     "reviewer ACTIVE today"      != "ACTIVE when the decision was ratified"
//     "not recused today"          != "not recused at decision time"
//   Suspending a reviewer after ratification retroactively invalidates a
//   decision that was lawful when made; un-recusing one retroactively
//   legitimises a decision that was not. Panel membership, standing and
//   recusal need effective-time semantics (valid_from / valid_until) or an
//   immutable standing snapshot attached to the decision. Recorded, not
//   solved.
//
// EXPECTED: 0 rows

MATCH (d:AdjudicationDecision)-[:DECIDES]->(c:AdjudicationCase)
MATCH (d)-[:RESOLVES]->(cl:Claim)
MATCH (d)-[:ISSUED_BY]->(p:ReviewPanel)
WHERE d.status = 'RATIFIED'

CALL (c, cl, p) {
  MATCH (p)-[:HAS_MEMBER]->(r:Adjudicator)
  WHERE r.status = 'ACTIVE'
    AND coalesce(c.ingested_by, '') <> r.canonical_id
    AND NOT EXISTS { MATCH (r)-[:RECUSED_FROM]->(c) }

  OPTIONAL MATCH (v:AdjudicationVote)-[:CAST_BY]->(r)
  WHERE v.status = 'CAST'
    AND v.signature_verified = true
    AND EXISTS { MATCH (v)-[:FOR_CASE]->(c) }
    AND EXISTS { MATCH (v)-[:FOR_CLAIM]->(cl) }

  WITH r, collect(v) AS votes
  RETURN
    count(CASE WHEN size(votes) = 1 THEN 1 END) AS recomputed_valid_votes,
    sum(CASE WHEN size(votes) = 1 AND votes[0].choice = 'ACCEPT' THEN 1 ELSE 0 END)
      AS recomputed_accept_votes,
    sum(CASE WHEN size(votes) = 1 AND votes[0].choice = 'REJECT' THEN 1 ELSE 0 END)
      AS recomputed_reject_votes
}

// A WHERE cannot follow a CALL subquery directly; project first.
WITH d, p, cl,
     recomputed_valid_votes,
     recomputed_accept_votes,
     recomputed_reject_votes

WHERE recomputed_valid_votes < coalesce(p.quorum_required, 2147483647)
   OR recomputed_valid_votes < coalesce(p.min_distinct_voters, 2147483647)
   OR recomputed_accept_votes <= recomputed_reject_votes
   OR coalesce(d.valid_vote_count, -1) <> recomputed_valid_votes
   OR coalesce(d.accept_vote_count, -1) <> recomputed_accept_votes
   OR coalesce(d.reject_vote_count, -1) <> recomputed_reject_votes
   OR coalesce(d.quorum_verified, false) <> true

RETURN
  d.canonical_id AS invalid_decision,
  p.quorum_required AS required_quorum,
  recomputed_valid_votes,
  recomputed_accept_votes,
  recomputed_reject_votes,
  d.valid_vote_count AS recorded_valid_votes,
  d.accept_vote_count AS recorded_accept_votes,
  d.reject_vote_count AS recorded_reject_votes;
