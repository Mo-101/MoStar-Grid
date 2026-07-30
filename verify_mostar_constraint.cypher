SHOW CONSTRAINTS
YIELD name, type, labelsOrTypes, properties, ownedIndex
WHERE name = 'unique_mostar_id'
RETURN name, type, labelsOrTypes, properties, ownedIndex;

SHOW INDEXES
YIELD name, state, labelsOrTypes, properties, owningConstraint
WHERE name = 'moment_id_idx'
   OR owningConstraint = 'unique_mostar_id'
RETURN name, state, labelsOrTypes, properties, owningConstraint;

MATCH (m:MoStarMoment)
WHERE m.id IS NOT NULL
WITH m.id AS id, count(*) AS occurrences
WHERE occurrences > 1
RETURN id, occurrences;
