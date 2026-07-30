MATCH (n)
WHERE n:CanonicalComponent AND n:RuntimeEvent
RETURN
  id(n) AS internalId,
  labels(n) AS labels,
  properties(n) AS props,
  n.mostar_sig IS NOT NULL AS hasSig,
  n.content_seal IS NOT NULL AS hasSeal,
  COUNT { (n)--() } AS degree;

MATCH (n)
WHERE n:CanonicalComponent AND n:RuntimeEvent
MATCH (n)-[r]-(other)
RETURN
  id(n) AS internalId,
  type(r) AS relType,
  startNode(r) = n AS outgoingFromNode,
  id(other) AS otherId,
  labels(other) AS otherLabels,
  properties(r) AS relProps
ORDER BY relType, otherId;
