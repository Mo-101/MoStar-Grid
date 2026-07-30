MATCH (n:Metric:BodyLayer)
RETURN valueType(n.timestamp) AS clockType, count(*) AS c
ORDER BY c DESC;
