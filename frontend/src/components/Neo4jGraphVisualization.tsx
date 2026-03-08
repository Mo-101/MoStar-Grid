'use client';

import React, { useState, useEffect } from 'react';
import { GraphCanvas, GraphNode, GraphEdge, lightTheme, darkTheme } from 'reagraph';
import neo4j from 'neo4j-driver';

interface Neo4jNode {
  id: string;
  label: string;
  properties: Record<string, any>;
  labels: string[];
}

interface Neo4jRelationship {
  id: string;
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const Neo4jGraphVisualization: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');

  const fetchGraphData = async () => {
    setLoading(true);
    setError(null);

    try {
      const driver = neo4j.driver(
        'bolt://localhost:7687',
        neo4j.auth.basic('neo4j', 'mostar123')
      );

      const session = driver.session();

      // Fetch nodes and relationships with a limit for performance
      const result = await session.run(`
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        WITH n, r, m
        LIMIT 200
        RETURN 
          n,
          labels(n) as nodeLabels,
          r,
          type(r) as relType,
          m,
          labels(m) as targetLabels
      `);

      const nodes = new Map<string, GraphNode>();
      const edges: GraphEdge[] = [];

      result.records.forEach(record => {
        const sourceNode = record.get('n');
        const relationship = record.get('r');
        const targetNode = record.get('m');
        const nodeLabels = record.get('nodeLabels') || [];
        const targetLabels = record.get('targetLabels') || [];
        const relType = record.get('relType');

        // Add source node
        if (sourceNode && !nodes.has(sourceNode.identity.toString())) {
          const nodeId = sourceNode.identity.toString();
          const primaryLabel = nodeLabels[0] || 'Node';
          const displayName = sourceNode.properties.name || 
                             sourceNode.properties.id || 
                             sourceNode.properties.description?.substring(0, 30) + '...' ||
                             `${primaryLabel} ${nodeId}`;

          nodes.set(nodeId, {
            id: nodeId,
            label: displayName,
            data: {
              labels: nodeLabels,
              properties: sourceNode.properties,
              primaryLabel
            }
          });
        }

        // Add target node and relationship if they exist
        if (targetNode && relationship) {
          const targetId = targetNode.identity.toString();
          
          if (!nodes.has(targetId)) {
            const primaryLabel = targetLabels[0] || 'Node';
            const displayName = targetNode.properties.name || 
                               targetNode.properties.id || 
                               targetNode.properties.description?.substring(0, 30) + '...' ||
                               `${primaryLabel} ${targetId}`;

            nodes.set(targetId, {
              id: targetId,
              label: displayName,
              data: {
                labels: targetLabels,
                properties: targetNode.properties,
                primaryLabel
              }
            });
          }

          edges.push({
            id: relationship.identity.toString(),
            source: sourceNode.identity.toString(),
            target: targetId,
            label: relType,
            data: {
              type: relType,
              properties: relationship.properties
            }
          });
        }
      });

      await session.close();
      await driver.close();

      setGraphData({
        nodes: Array.from(nodes.values()),
        edges
      });

    } catch (err) {
      console.error('Error fetching graph data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch graph data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraphData();
  }, []);

  const getNodeColor = (node: GraphNode) => {
    const primaryLabel = node.data?.primaryLabel || 'Unknown';
    
    // Color coding based on node types
    switch (primaryLabel) {
      case 'MoStarMoment': return '#FF6B6B';
      case 'Agent': return '#4ECDC4';
      case 'Proverb': return '#45B7D1';
      case 'Culture': return '#96CEB4';
      case 'CovenantKernel': return '#FFEAA7';
      case 'Ritual': return '#DDA0DD';
      default: return '#74B9FF';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-900 rounded-lg">
        <div className="text-white">Loading Neo4j graph...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 bg-gray-900 rounded-lg">
        <div className="text-red-400 mb-4">Error: {error}</div>
        <button 
          onClick={fetchGraphData}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="w-full h-96 bg-gray-900 rounded-lg relative">
      <div className="absolute top-4 right-4 z-10 flex gap-2">
        <button
          onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
          className="px-3 py-1 bg-gray-700 text-white rounded text-sm hover:bg-gray-600"
        >
          {theme === 'light' ? '🌙' : '☀️'}
        </button>
        <button
          onClick={fetchGraphData}
          className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>
      
      <div className="absolute top-4 left-4 z-10 text-white text-sm bg-black bg-opacity-50 px-2 py-1 rounded">
        {graphData.nodes.length} nodes, {graphData.edges.length} edges
      </div>

      <GraphCanvas
        nodes={graphData.nodes}
        edges={graphData.edges}
        theme={theme === 'light' ? lightTheme : darkTheme}
        layoutType="forceDirected2d"
        draggable
        pannable
        zoomable
        onNodeClick={(node) => {
          console.log('Node clicked:', node);
        }}
        onEdgeClick={(edge) => {
          console.log('Edge clicked:', edge);
        }}
        nodeRenderer={(node) => (
          <circle
            r={8}
            fill={getNodeColor(node)}
            stroke="#fff"
            strokeWidth={2}
          />
        )}
      />
    </div>
  );
};

export default Neo4jGraphVisualization;
