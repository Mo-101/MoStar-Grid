MATCH (canon) WHERE id(canon) = 910
RETURN COUNT { (canon)-[:REFERENCES]-() } AS referencesCount;
