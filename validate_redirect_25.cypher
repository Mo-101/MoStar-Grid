UNWIND [911,912,913,914,915,916,917,918,919,920,921,922,923,924,925,927,928,929,930,931,932,933,934,935,936] AS canonId
MATCH (canon:Philosophy) WHERE id(canon) = canonId
RETURN canonId, canon.name AS name, COUNT { (canon)-[:BELONGS_TO]->() } AS belongsToCount
ORDER BY canonId;
