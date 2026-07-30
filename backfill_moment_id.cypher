// Treat id as the authoritative MoStarMoment identity.
// Backfill missing id values from canonical_id as the stable fallback.
MATCH (m:MoStarMoment)
WHERE m.id IS NULL
SET m.id = m.canonical_id;
