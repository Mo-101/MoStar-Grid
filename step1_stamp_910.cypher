// step1_stamp_910.cypher — provenance stamp only, no merge yet, idempotent
MATCH (canon:Philosophy) WHERE id(canon) = 910
MATCH (op:Philosophy) WHERE id(op) = 256
SET canon.shadow_source_ids =
  CASE
    WHEN id(op) IN coalesce(canon.shadow_source_ids, [])
    THEN coalesce(canon.shadow_source_ids, [])
    ELSE coalesce(canon.shadow_source_ids, []) + id(op)
  END,
    canon.shadow_source_content =
  CASE
    WHEN op.core_principle IN coalesce(canon.shadow_source_content, [])
    THEN coalesce(canon.shadow_source_content, [])
    ELSE coalesce(canon.shadow_source_content, []) + op.core_principle
  END
RETURN canon.name, canon.shadow_source_ids, canon.shadow_source_content;
