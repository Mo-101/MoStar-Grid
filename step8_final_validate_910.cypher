MATCH (u) WHERE id(u) = 910
RETURN
  COUNT { (u)--() } AS totalDegree,
  u.shadow_source_ids AS shadowSourceIds,
  u.mostar_sig IS NOT NULL AS hasSig,
  u.content_seal IS NOT NULL AS hasSeal;
