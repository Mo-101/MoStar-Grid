// Agent cluster identity — restores the Council to /api/agents.
//
// The canonical pantheon projection (commit a2cc1e34, "load canonical pantheon
// and govern all 14 agents") created the :Agent nodes without stamping
// cluster_id. MindGraph.get_agents() matches (a:Agent {cluster_id: $cluster_id})
// with cluster_id = 'nairobi-alpha', so /api/agents returned [] while
// /watchtower/agents — which does not filter by cluster — listed all of them.
// The Council Chamber read that empty list as the council being down.
//
// Scope is deliberately the :Agent label only. 97,970 of 136,678 nodes in this
// graph carry no cluster_id; stamping the whole graph is a separate decision
// with a far larger blast radius, and this migration does not take it.
//
// SET-only and idempotent: no DELETE, DETACH DELETE, or REMOVE. Agents that
// already carry a cluster_id are left exactly as they are, so this cannot
// reassign an agent that belongs to another cluster.

MATCH (a:Agent)
WHERE a.cluster_id IS NULL
SET a.cluster_id = 'nairobi-alpha',
    a.cluster_stamped_at = coalesce(a.cluster_stamped_at, timestamp()),
    a.cluster_stamped_by = 'migration:002_agent_cluster_identity'
RETURN count(a) AS agents_stamped;
