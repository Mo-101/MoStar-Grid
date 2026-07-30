MATCH (n)
WHERE ((n:Metric AND n:BodyLayer) OR n:ExecutorHeartbeat OR n:RuntimeEvent)
  AND (n:CanonicalComponent OR n.status = 'EVENT_TEMPLATE' OR n.canonical = false)
RETURN labels(n) AS labelSet, n.status AS status, n.canonical AS canonical, count(n) AS c
ORDER BY c DESC;
