MATCH (n:ExecutorHeartbeat)
RETURN
  valueType(n.created_at) AS createdAtType,
  valueType(n.last_heartbeat) AS lastHeartbeatType,
  count(*) AS c
ORDER BY c DESC;
