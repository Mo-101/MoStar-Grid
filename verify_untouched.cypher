// verify_untouched.cypher — confirm the failed merge call left both nodes intact
MATCH (op:Philosophy) WHERE id(op) = 256
RETURN 'op_256' AS which, id(op) AS nid, COUNT { (op)--() } AS degree, op.core_principle AS principle
UNION ALL
MATCH (canon:Philosophy) WHERE id(canon) = 910
RETURN 'canon_910' AS which, id(canon) AS nid, COUNT { (canon)--() } AS degree, canon.name AS principle;
