// ── Phase 1: Exact Word Name Binding ─────────────────────────
// Matches where the filename contains the exact Ibibio word with boundaries
MATCH (a:AudioSample), (w:IbibioWord)
WHERE a.filename =~ (".*[_\\-]" + toLower(w.word) + "[_\\-\\].].*")
   OR a.filename =~ ("^" + toLower(w.word) + "[_\\-\\.].*")
MERGE (w)-[:HAS_AUDIO]->(a);

// ── Phase 2: Exact Hyphenated English Gloss Binding ──────────
// Matches where the filename contains the full hyphenated English gloss
MATCH (a:AudioSample), (w:IbibioWord)
WHERE toLower(a.filename) CONTAINS replace(toLower(w.english), ' ', '-')
   AND NOT (toLower(a.filename) CONTAINS 'partition' AND toLower(w.word) = 'ti')
MERGE (w)-[:HAS_AUDIO]->(a);

// ── Final count ──────────────────────────────────────────────
MATCH ()-[r:HAS_AUDIO]->() RETURN count(r) AS total_bindings;
