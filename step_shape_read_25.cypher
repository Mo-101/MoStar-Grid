UNWIND [257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,273,274,275,276,277,278,279,280,281,282] AS opId
MATCH (n:Philosophy) WHERE id(n) = opId
MATCH (n)-[r]-(other)
RETURN
  opId,
  type(r) AS relType,
  startNode(r) = n AS outgoingFromOp,
  keys(r) AS relProps,
  id(other) AS otherId,
  labels(other) AS otherLabels
ORDER BY opId;
