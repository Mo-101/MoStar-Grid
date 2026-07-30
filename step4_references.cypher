MATCH (op) WHERE id(op) = 256
MATCH (canon) WHERE id(canon) = 910
MATCH (task)-[old:REFERENCES]->(op)
WITH canon, task, old, properties(old) AS oldProps
CREATE (task)-[new:REFERENCES]->(canon)
SET new = oldProps
RETURN count(new) AS created;
