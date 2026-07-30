// step2_merge_256_into_910.cypher — merge 256 into 910; canon (910) first = survivor
MATCH (canon:Philosophy) WHERE id(canon) = 910
MATCH (op:Philosophy) WHERE id(op) = 256
CALL apoc.refactor.mergeNodes(
  [canon, op],
  { properties: 'discard', mergeRels: true }
) YIELD node
RETURN id(node) AS survivor_id, node.name AS name, COUNT { (node)--() } AS totalDegree;
