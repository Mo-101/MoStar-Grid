MATCH (n) WHERE id(n) = 256
MATCH (n)-[r]-(other)
RETURN
  type(r) AS relType,
  startNode(r) = n AS outgoingFromN,
  keys(r) AS relProps,
  count(*) AS c
ORDER BY relType, outgoingFromN;
