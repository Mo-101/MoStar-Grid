// TRANSACTION — panel membership, ONE adjudicator per transaction
//
// ══════════════════════════════════════════════════════════════════════
// DO NOT batch multiple members into a single statement.
// ══════════════════════════════════════════════════════════════════════
//
// The rejected shape:
//
//     MERGE (p)-[m1:HAS_MEMBER]->(r1) SET ...
//     MERGE (p)-[m2:HAS_MEMBER]->(r2) SET ...
//
// PROFILE of that shape (2026-08-15) showed two problems:
//
//   1. LOCK ORDER. Each MERGE is a LockingMerge and each lookup a
//      NodeUniqueIndexSeek(Locking). Two concurrent panel writes acquiring
//      (p, r1) and (p, r2) in different orders can invert and block. A
//      19.8s observation on this exact operation was consistent with lock
//      wait, not query cost — the plan itself was optimal at 21ms.
//
//   2. EAGER. Reading and writing HAS_MEMBER twice in one query forced an
//      `Eager` operator ("read/set conflict for relationship type:
//      HAS_MEMBER"). Harmless at one row; a materialisation hazard for
//      bulk panel seeding.
//
// The caller must sort adjudicators by canonical_id ASC and submit this
// statement once per member. Deterministic acquisition order removes the
// inversion class; one HAS_MEMBER write per transaction removes the Eager.
//
// :param panel_id       => 'panel:...'
// :param adjudicator_id => 'adjudicator:...'
// :param seat_type      => 'INDEPENDENT_REVIEWER' | 'LOCAL_DOMAIN_REVIEWER'
// :param voting         => true

MATCH (p:ReviewPanel {canonical_id: $panel_id})
MATCH (r:Adjudicator {canonical_id: $adjudicator_id})

MERGE (p)-[m:HAS_MEMBER]->(r)
SET m.seat_type = $seat_type,
    m.voting = $voting,
    m.updated_at = datetime()

RETURN
  p.canonical_id AS panel,
  r.canonical_id AS adjudicator,
  m.seat_type AS seat_type,
  m.voting AS voting;
