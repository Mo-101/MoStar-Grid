MATCH (n)
WHERE (n:Metric AND n:BodyLayer) OR n:ExecutorHeartbeat OR n:RuntimeEvent
RETURN labels(n) AS labelSet,
       count(n) AS total,
       min(n.timestamp) AS earliest,
       max(n.timestamp) AS latest,
       count(n.timestamp) AS haveTimestamp
ORDER BY total DESC;
