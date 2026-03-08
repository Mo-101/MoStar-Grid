"use client";

import React, { useState, useEffect, useCallback } from "react";
import { GraphCanvas, GraphNode, GraphEdge, lightTheme, darkTheme } from "reagraph";
import neo4j from "neo4j-driver";
import GridNav from "@/components/GridNav";
import styles from "./GraphExplorer.module.css";

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface FilterOptions {
  nodeLabels: string[];
  relationshipTypes: string[];
  minResonance: number;
  maxNodes: number;
}

type LayoutType = "forceDirected2d" | "forceDirected3d" | "circular2d" | "tree";

export default function GraphExplorerPage() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [filteredData, setFilteredData] = useState<GraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Customization states
  const [theme, setTheme] = useState<"light" | "dark">("dark");
  const [layout, setLayout] = useState<LayoutType>("forceDirected2d");
  const [showLabels, setShowLabels] = useState(true);
  const [showEdges, setShowEdges] = useState(true);
  const [nodeSize, setNodeSize] = useState(8);
  const [edgeWidth, setEdgeWidth] = useState(2);
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  
  // Filters
  const [availableLabels, setAvailableLabels] = useState<string[]>([]);
  const [availableRelTypes, setAvailableRelTypes] = useState<string[]>([]);
  const [selectedLabels, setSelectedLabels] = useState<string[]>([]);
  const [selectedRelTypes, setSelectedRelTypes] = useState<string[]>([]);
  const [nodeLimit, setNodeLimit] = useState(200);
  
  // Node color mapping
  const getNodeColor = useCallback((node: GraphNode) => {
    const primaryLabel = node.data?.primaryLabel || "Unknown";
    const colors: Record<string, string> = {
      MoStarMoment: "#FF6B6B",
      Agent: "#4ECDC4",
      Proverb: "#45B7D1",
      Culture: "#96CEB4",
      CovenantKernel: "#FFEAA7",
      Ritual: "#DDA0DD",
      Elder: "#F7DC6F",
      Ancestor: "#BB8FCE",
      Default: "#74B9FF",
    };
    return colors[primaryLabel] || colors.Default;
  }, []);

  const fetchGraphData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const driver = neo4j.driver(
        "bolt://localhost:7687",
        neo4j.auth.basic("neo4j", "mostar123")
      );

      const session = driver.session();

      // Fetch nodes and relationships with limit
      const result = await session.run(`
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        WITH n, r, m
        LIMIT $limit
        RETURN 
          n,
          labels(n) as nodeLabels,
          r,
          type(r) as relType,
          m,
          labels(m) as targetLabels
      `, { limit: nodeLimit });

      const nodes = new Map<string, GraphNode>();
      const edges: GraphEdge[] = [];
      const labels = new Set<string>();
      const relTypes = new Set<string>();

      result.records.forEach((record) => {
        const sourceNode = record.get("n");
        const relationship = record.get("r");
        const targetNode = record.get("m");
        const nodeLabelsArr = record.get("nodeLabels") || [];
        const targetLabelsArr = record.get("targetLabels") || [];
        const relType = record.get("relType");

        // Collect available labels and types
        nodeLabelsArr.forEach((l: string) => labels.add(l));
        if (relType) relTypes.add(relType);

        // Add source node
        if (sourceNode && !nodes.has(sourceNode.identity.toString())) {
          const nodeId = sourceNode.identity.toString();
          const primaryLabel = nodeLabelsArr[0] || "Node";
          const displayName =
            sourceNode.properties.name ||
            sourceNode.properties.id ||
            sourceNode.properties.description?.substring(0, 30) + "..." ||
            `${primaryLabel} ${nodeId}`;

          nodes.set(nodeId, {
            id: nodeId,
            label: displayName,
            data: {
              labels: nodeLabelsArr,
              properties: sourceNode.properties,
              primaryLabel,
            },
          });
        }

        // Add target node and relationship if they exist
        if (targetNode && relationship) {
          const targetId = targetNode.identity.toString();
          targetLabelsArr.forEach((l: string) => labels.add(l));

          if (!nodes.has(targetId)) {
            const primaryLabel = targetLabelsArr[0] || "Node";
            const displayName =
              targetNode.properties.name ||
              targetNode.properties.id ||
              targetNode.properties.description?.substring(0, 30) + "..." ||
              `${primaryLabel} ${targetId}`;

            nodes.set(targetId, {
              id: targetId,
              label: displayName,
              data: {
                labels: targetLabelsArr,
                properties: targetNode.properties,
                primaryLabel,
              },
            });
          }

          edges.push({
            id: relationship.identity.toString(),
            source: sourceNode.identity.toString(),
            target: targetId,
            label: relType,
            data: {
              type: relType,
              properties: relationship.properties,
            },
          });
        }
      });

      await session.close();
      await driver.close();

      const newData = {
        nodes: Array.from(nodes.values()),
        edges,
      };

      setGraphData(newData);
      setFilteredData(newData);
      setAvailableLabels(Array.from(labels).sort());
      setAvailableRelTypes(Array.from(relTypes).sort());
    } catch (err) {
      console.error("Error fetching graph data:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch graph data");
    } finally {
      setLoading(false);
    }
  }, [nodeLimit]);

  useEffect(() => {
    fetchGraphData();
  }, [fetchGraphData]);

  // Apply filters
  useEffect(() => {
    let filtered = { ...graphData };

    // Filter by node labels
    if (selectedLabels.length > 0) {
      const filteredNodes = graphData.nodes.filter((node) =>
        node.data?.labels.some((l: string) => selectedLabels.includes(l))
      );
      const nodeIds = new Set(filteredNodes.map((n) => n.id));
      const filteredEdges = graphData.edges.filter(
        (e) => nodeIds.has(e.source) && nodeIds.has(e.target)
      );
      filtered = { nodes: filteredNodes, edges: filteredEdges };
    }

    // Filter by relationship types
    if (selectedRelTypes.length > 0) {
      filtered.edges = filtered.edges.filter((e) =>
        selectedRelTypes.includes(e.data?.type)
      );
      const connectedNodeIds = new Set(
        filtered.edges.flatMap((e) => [e.source, e.target])
      );
      filtered.nodes = filtered.nodes.filter((n) =>
        connectedNodeIds.has(n.id)
      );
    }

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const matchingNodes = filtered.nodes.filter((n) =>
        n.label?.toLowerCase().includes(query)
      );
      const nodeIds = new Set(matchingNodes.map((n) => n.id));
      const connectedEdges = filtered.edges.filter(
        (e) => nodeIds.has(e.source) || nodeIds.has(e.target)
      );
      const connectedIds = new Set(
        connectedEdges.flatMap((e) => [e.source, e.target])
      );
      filtered = {
        nodes: filtered.nodes.filter((n) => connectedIds.has(n.id)),
        edges: connectedEdges,
      };
    }

    setFilteredData(filtered);
  }, [graphData, selectedLabels, selectedRelTypes, searchQuery]);

  const handleNodeClick = (node: GraphNode) => {
    setActiveNode(node.id);
    console.log("Node clicked:", node);
  };

  const exportGraph = () => {
    const data = JSON.stringify(filteredData, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `graph-export-${new Date().toISOString()}.json`;
    a.click();
  };

  const clearFilters = () => {
    setSelectedLabels([]);
    setSelectedRelTypes([]);
    setSearchQuery("");
  };

  return (
    <div className={styles.screen}>
      <GridNav />
      
      <div className={styles.container}>
        <header className={styles.header}>
          <div>
            <h1>🕸️ Graph Explorer</h1>
            <p>Interactive Neo4j visualization with advanced filtering</p>
          </div>
          <div className={styles.stats}>
            <span>{filteredData.nodes.length} nodes</span>
            <span>{filteredData.edges.length} edges</span>
          </div>
        </header>

        <div className={styles.mainContent}>
          {/* Sidebar Controls */}
          <aside className={styles.sidebar}>
            {/* Search */}
            <section className={styles.controlSection}>
              <h3>🔍 Search</h3>
              <input
                type="text"
                placeholder="Search nodes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={styles.searchInput}
              />
            </section>

            {/* Node Limit */}
            <section className={styles.controlSection}>
              <h3>📊 Node Limit</h3>
              <div className={styles.rangeControl}>
                <input
                  type="range"
                  min="50"
                  max="500"
                  step="50"
                  value={nodeLimit}
                  onChange={(e) => setNodeLimit(Number(e.target.value))}
                />
                <span>{nodeLimit}</span>
              </div>
              <button onClick={fetchGraphData} className={styles.refreshBtn}>
                🔄 Refresh Data
              </button>
            </section>

            {/* Theme */}
            <section className={styles.controlSection}>
              <h3>🎨 Theme</h3>
              <div className={styles.buttonGroup}>
                <button
                  onClick={() => setTheme("dark")}
                  className={theme === "dark" ? styles.active : ""}
                >
                  🌙 Dark
                </button>
                <button
                  onClick={() => setTheme("light")}
                  className={theme === "light" ? styles.active : ""}
                >
                  ☀️ Light
                </button>
              </div>
            </section>

            {/* Layout */}
            <section className={styles.controlSection}>
              <h3>📐 Layout</h3>
              <select
                value={layout}
                onChange={(e) => setLayout(e.target.value as LayoutType)}
                className={styles.select}
              >
                <option value="forceDirected2d">Force Directed 2D</option>
                <option value="forceDirected3d">Force Directed 3D</option>
                <option value="circular2d">Circular 2D</option>
                <option value="tree">Tree</option>
              </select>
            </section>

            {/* Display Options */}
            <section className={styles.controlSection}>
              <h3>👁️ Display</h3>
              <label className={styles.checkbox}>
                <input
                  type="checkbox"
                  checked={showLabels}
                  onChange={(e) => setShowLabels(e.target.checked)}
                />
                Show Labels
              </label>
              <label className={styles.checkbox}>
                <input
                  type="checkbox"
                  checked={showEdges}
                  onChange={(e) => setShowEdges(e.target.checked)}
                />
                Show Edges
              </label>
            </section>

            {/* Node Size */}
            <section className={styles.controlSection}>
              <h3>🔵 Node Size</h3>
              <div className={styles.rangeControl}>
                <input
                  type="range"
                  min="4"
                  max="20"
                  value={nodeSize}
                  onChange={(e) => setNodeSize(Number(e.target.value))}
                />
                <span>{nodeSize}px</span>
              </div>
            </section>

            {/* Edge Width */}
            <section className={styles.controlSection}>
              <h3>🔗 Edge Width</h3>
              <div className={styles.rangeControl}>
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={edgeWidth}
                  onChange={(e) => setEdgeWidth(Number(e.target.value))}
                />
                <span>{edgeWidth}px</span>
              </div>
            </section>

            {/* Label Filters */}
            {availableLabels.length > 0 && (
              <section className={styles.controlSection}>
                <h3>🏷️ Node Labels</h3>
                <div className={styles.filterList}>
                  {availableLabels.map((label) => (
                    <label key={label} className={styles.filterItem}>
                      <input
                        type="checkbox"
                        checked={selectedLabels.includes(label)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedLabels([...selectedLabels, label]);
                          } else {
                            setSelectedLabels(
                              selectedLabels.filter((l) => l !== label)
                            );
                          }
                        }}
                      />
                      <span
                        className={styles.colorDot}
                        style={{
                          background: getNodeColor({ data: { primaryLabel: label } } as GraphNode),
                        }}
                      />
                      {label}
                    </label>
                  ))}
                </div>
              </section>
            )}

            {/* Relationship Filters */}
            {availableRelTypes.length > 0 && (
              <section className={styles.controlSection}>
                <h3>↔️ Relationships</h3>
                <div className={styles.filterList}>
                  {availableRelTypes.map((type) => (
                    <label key={type} className={styles.filterItem}>
                      <input
                        type="checkbox"
                        checked={selectedRelTypes.includes(type)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedRelTypes([...selectedRelTypes, type]);
                          } else {
                            setSelectedRelTypes(
                              selectedRelTypes.filter((t) => t !== type)
                            );
                          }
                        }}
                      />
                      {type}
                    </label>
                  ))}
                </div>
              </section>
            )}

            {/* Actions */}
            <section className={styles.controlSection}>
              <h3>⚡ Actions</h3>
              <button onClick={clearFilters} className={styles.actionBtn}>
                🧹 Clear Filters
              </button>
              <button onClick={exportGraph} className={styles.actionBtn}>
                💾 Export JSON
              </button>
            </section>
          </aside>

          {/* Graph Canvas */}
          <main className={styles.graphContainer}>
            {loading ? (
              <div className={styles.loading}>
                <div className={styles.spinner} />
                <p>Loading Neo4j graph...</p>
              </div>
            ) : error ? (
              <div className={styles.error}>
                <p>❌ {error}</p>
                <button onClick={fetchGraphData}>Retry</button>
              </div>
            ) : (
              <>
                <GraphCanvas
                  nodes={filteredData.nodes}
                  edges={showEdges ? filteredData.edges : []}
                  theme={theme === "light" ? lightTheme : darkTheme}
                  layoutType={layout}
                  draggable
                  pannable
                  zoomable
                  onNodeClick={handleNodeClick}
                  nodeRenderer={(node) => (
                    <circle
                      r={nodeSize}
                      fill={getNodeColor(node)}
                      stroke={activeNode === node.id ? "#fff" : "transparent"}
                      strokeWidth={activeNode === node.id ? 3 : 0}
                    />
                  )}
                  edgeWidth={edgeWidth}
                  labelVisible={showLabels}
                />
                
                {activeNode && (
                  <div className={styles.nodeDetails}>
                    <h4>Node Details</h4>
                    {(() => {
                      const node = graphData.nodes.find((n) => n.id === activeNode);
                      if (!node) return null;
                      return (
                        <div className={styles.nodeInfo}>
                          <p><strong>ID:</strong> {node.id}</p>
                          <p><strong>Label:</strong> {node.label}</p>
                          <p><strong>Type:</strong> {node.data?.primaryLabel}</p>
                          <p><strong>Labels:</strong> {node.data?.labels?.join(", ")}</p>
                          <details>
                            <summary>Properties</summary>
                            <pre>{JSON.stringify(node.data?.properties, null, 2)}</pre>
                          </details>
                        </div>
                      );
                    })()}
                    <button onClick={() => setActiveNode(null)}>Close</button>
                  </div>
                )}
              </>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
