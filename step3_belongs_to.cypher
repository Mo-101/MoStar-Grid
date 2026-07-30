MATCH (op) WHERE id(op) = 256
MATCH (canon) WHERE id(canon) = 910
MATCH (op)-[old:BELONGS_TO]->(dom)
CREATE (canon)-[new:BELONGS_TO]->(dom)
SET new = properties(old)
RETURN properties(new);
