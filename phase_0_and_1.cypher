MATCH (r:RetentionPolicy) RETURN r;

MATCH (q) WHERE q:QuarantinedComponent OR q:QuarantinedGate
RETURN labels(q), q.name, q.reason;

MATCH (p:Philosophy) WHERE p.name IS NULL
RETURN id(p), keys(p) AS props, size(keys(p)) AS propCount,
       count { (p)--() } AS degree
ORDER BY propCount DESC;
