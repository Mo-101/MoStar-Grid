MATCH (n)
WHERE ((n:Metric AND n:BodyLayer) OR n:ExecutorHeartbeat OR n:RuntimeEvent)
  AND NOT n:CanonicalComponent
WITH n, coalesce(n.timestamp, n.created_at,
                  CASE WHEN n.last_heartbeat IS NOT NULL THEN datetime(n.last_heartbeat) END
             ) AS effectiveClock
RETURN labels(n) AS labelSet,
       count(n) AS total,
       min(effectiveClock) AS earliest,
       max(effectiveClock) AS latest,
       count(effectiveClock) AS haveTimestamp
ORDER BY total DESC;
