// probe_phase1c.cypher — full read, no truncation this time
MATCH (p:Philosophy) WHERE p.name IS NULL
RETURN id(p),
       p.core_principle AS principle,
       p.manifestation  AS manifestation,
       p.ethical_guidance AS ethical_guidance
ORDER BY id(p);

// Does this "new" entry collide with an existing canon name?
MATCH (existing:Philosophy) WHERE existing.name IS NOT NULL
RETURN existing.name, existing.alt_names, id(existing)
ORDER BY existing.name;
