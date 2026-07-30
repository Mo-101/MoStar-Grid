MATCH (canon) WHERE id(canon) = 910
RETURN COUNT { (canon)-[:BELONGS_TO]-() } AS belongsToCount;
