// Canon survivors: seal, sig, provenance
UNWIND [910,911,912,913,914,915,916,917,918,919,920,921,922,923,924,925,927,928,929,930,931,932,933,934,935,936] AS cId
MATCH (u:Philosophy) WHERE id(u) = cId
RETURN
  cId AS canonId,
  u.name AS name,
  COUNT { (u)--() } AS totalDegree,
  u.shadow_source_ids AS shadowSourceIds,
  u.mostar_sig IS NOT NULL AS hasSig,
  u.content_seal IS NOT NULL AS hasSeal
ORDER BY canonId;

// Operational range should be entirely gone except 272
MATCH (n:Philosophy)
WHERE id(n) IN [256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282]
RETURN id(n) AS remainingId, n.core_principle AS principle
ORDER BY remainingId;
