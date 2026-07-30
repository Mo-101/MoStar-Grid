// Cycle 1 PageRank baseline receipt.
// Runs before sovereign core consolidation. This stores a lightweight top-25
// PageRank sample using GDS without mutating existing domain nodes.

CALL gds.graph.drop('cycle1_pagerank_baseline', false) YIELD graphName
RETURN graphName;

CALL gds.graph.project(
  'cycle1_pagerank_baseline',
  '*',
  { ALL_RELATIONSHIPS: { type: '*', orientation: 'NATURAL' } }
)
YIELD graphName, nodeCount, relationshipCount
WITH graphName, nodeCount, relationshipCount
CALL gds.pageRank.stream(graphName, { maxIterations: 20, dampingFactor: 0.85 })
YIELD nodeId, score
WITH graphName, nodeCount, relationshipCount, nodeId, score
ORDER BY score DESC
LIMIT 25
WITH graphName, nodeCount, relationshipCount,
     collect(
       reduce(labelText = '', label IN labels(gds.util.asNode(nodeId)) |
         labelText + CASE WHEN labelText = '' THEN '' ELSE ':' END + label
       )
       + '|'
       + coalesce(
         gds.util.asNode(nodeId).id,
         gds.util.asNode(nodeId).entity_id,
         gds.util.asNode(nodeId).agent_id,
         gds.util.asNode(nodeId).artifact_id,
         gds.util.asNode(nodeId).canonical_id,
         gds.util.asNode(nodeId).name,
         'node-' + toString(nodeId)
       )
       + '|'
       + toString(score)
     ) AS top_nodes
MERGE (b:GraphMetricBaseline {baseline_id: 'cycle1_pagerank_baseline_20260714'})
SET b.algorithm = 'pageRank',
    b.graph_name = graphName,
    b.node_count = nodeCount,
    b.relationship_count = relationshipCount,
    b.top_nodes = top_nodes,
    b.created_at = datetime(),
    b.migration_run_id = 'mig-sovereign-core-consolidation-20260714',
    b.verification_status = 'COMPUTED',
    b.origin_model = 'codex',
    b.attested_by = 'grid_builder'
WITH graphName, b
CALL gds.graph.drop(graphName, false) YIELD graphName AS dropped_graph
RETURN b.baseline_id AS baseline_id, b.node_count AS node_count, b.relationship_count AS relationship_count, dropped_graph;
