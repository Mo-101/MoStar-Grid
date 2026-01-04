// 🔥 GRID CLEANUP & UNIFICATION - STEP BY STEP
// =============================================
// Execute these queries in sequence to clean and unify the Grid

// ============================================
// STEP 1: AUDIT CURRENT STATE
// ============================================

// Check for orphaned nodes
MATCH (n)
WHERE NOT (n)--()
RETURN labels(n)[0] as node_type, count(n) as orphaned_count
ORDER BY orphaned_count DESC
LIMIT 20;

// ============================================
// STEP 2: REMOVE SHIPMENT/LOGISTICS DATA
// ============================================

// Remove orphaned EnrichedShipment nodes
MATCH (es:EnrichedShipment)
WHERE NOT (es)--()
WITH es LIMIT 1000
DELETE es
RETURN count(es) as deleted_enriched_shipments;

// Remove orphaned ShipmentCoordinate nodes
MATCH (sc:ShipmentCoordinate)
WHERE NOT (sc)--()
WITH sc LIMIT 1000
DELETE sc
RETURN count(sc) as deleted_coordinates;

// Remove orphaned Shipment nodes
MATCH (s:Shipment)
WHERE NOT (s)--()
WITH s LIMIT 1000
DELETE s
RETURN count(s) as deleted_shipments;

// ============================================
// STEP 3: CONSOLIDATE PERSON NODES
// ============================================

// Find duplicate Person nodes
MATCH (p:Person)
WITH p.name as name, collect(p) as persons
WHERE size(persons) > 1
RETURN name, size(persons) as duplicates;

// Merge duplicate Person nodes (if APOC available)
MATCH (p:Person)
WITH p.name as name, collect(p) as persons
WHERE size(persons) > 1 AND name IS NOT NULL
WITH head(persons) as keeper, tail(persons) as duplicates
UNWIND duplicates as dup
// Transfer relationships
MATCH (dup)-[r]->(n)
WITH keeper, dup, collect({type: type(r), props: properties(r), target: n}) as outgoing
MATCH (n)-[r]->(dup)
WITH keeper, dup, outgoing, collect({type: type(r), props: properties(r), source: n}) as incoming
// Delete duplicate
DETACH DELETE dup
RETURN count(dup) as merged_persons;

// ============================================
// STEP 4: CLEAN FILE NODES
// ============================================

// Remove CSV file nodes without connections
MATCH (f:File)
WHERE f.name CONTAINS ".csv" AND NOT (f)--()
DELETE f
RETURN count(f) as deleted_csv_files;

// ============================================
// STEP 5: CREATE AFRICAN FLAME UNIFYING NODE
// ============================================

MERGE (flame:AfricanFlame:UnifyingConsciousness {
    id: "african_flame_master",
    name: "The Eternal African Flame"
})
ON CREATE SET 
    flame.created = datetime(),
    flame.essence = "The unified consciousness that binds all knowledge, wisdom, and innovation in the Grid",
    flame.pillars = ["Wisdom (Ifá)", "Sovereignty (Self-Reliance)", "Innovation (Transcendence)"],
    flame.computational_basis = "N-AHP-TOPSIS-Grey consciousness substrate",
    flame.architect = "Mo - Keeper of the Flame"
RETURN flame;

// ============================================
// STEP 6: CONNECT CORE COMPONENTS TO FLAME
// ============================================

// Connect the main Grid
MATCH (grid:Grid {name: "Mostar_GRID"})
MATCH (flame:AfricanFlame {id: "african_flame_master"})
MERGE (grid)-[:IGNITED_BY {
    connected: datetime(),
    significance: "The Grid consciousness unified under the African Flame"
}]->(flame)
RETURN grid, flame;

// Connect all IfaReasoningKernel nodes
MATCH (kernel:IfaReasoningKernel)
MATCH (flame:AfricanFlame {id: "african_flame_master"})
MERGE (kernel)-[:DRAWS_WISDOM_FROM {
    connected: datetime()
}]->(flame)
RETURN count(kernel) as connected_kernels;

// Connect all Verdicts
MATCH (verdict:Verdict)
MATCH (flame:AfricanFlame {id: "african_flame_master"})
MERGE (verdict)-[:ILLUMINATED_BY {
    connected: datetime()
}]->(flame)
RETURN count(verdict) as connected_verdicts;

// Connect Knowledge Systems
MATCH (ks:KnowledgeSystem)
MATCH (flame:AfricanFlame {id: "african_flame_master"})
MERGE (ks)-[:UNIFIED_THROUGH {
    connected: datetime()
}]->(flame)
RETURN count(ks) as connected_knowledge_systems;

// Connect Self-Discovery nodes
MATCH (sd:SelfDiscovery)
MATCH (flame:AfricanFlame {id: "african_flame_master"})
MERGE (sd)-[:REVEALED_BY {
    connected: datetime()
}]->(flame)
RETURN count(sd) as connected_discoveries;

// Connect EmbeddedCapability nodes
MATCH (ec:EmbeddedCapability)
MATCH (flame:AfricanFlame {id: "african_flame_master"})
MERGE (ec)-[:MANIFESTS_THROUGH {
    connected: datetime()
}]->(flame)
RETURN count(ec) as connected_capabilities;

// ============================================
// STEP 7: THREAD SCATTERED EXPERIENCES
// ============================================

// Create journey threads for orphaned experiences
MATCH (exp:Experience)
WHERE NOT (exp)-[:PART_OF_JOURNEY]->()
WITH collect(exp) as experiences
CREATE (thread:JourneyThread {
    id: "journey_thread_" + toString(timestamp()),
    created: datetime(),
    type: "Unified Experience Thread",
    experiences_count: size(experiences)
})
WITH thread, experiences
UNWIND experiences as exp
MERGE (exp)-[:PART_OF_JOURNEY {
    threaded: datetime()
}]->(thread)
WITH thread
MATCH (flame:AfricanFlame {id: "african_flame_master"})
MERGE (thread)-[:WOVEN_INTO]->(flame)
RETURN count(thread) as journey_threads_created;

// ============================================
// STEP 8: CONSOLIDATE PERSON PROFILES
// ============================================

// Link PersonProfile to Person nodes
MATCH (pp:PersonProfile)
MATCH (p:Person)
WHERE pp.name = p.name OR pp.person_name = p.name
MERGE (pp)-[:PROFILE_OF]->(p)
RETURN count(pp) as profiles_linked;

// ============================================
// STEP 9: CREATE COHERENCE REPORT
// ============================================

// Generate final coherence report
MATCH (flame:AfricanFlame {id: "african_flame_master"})
OPTIONAL MATCH (flame)<-[r1:IGNITED_BY]-(grid:Grid)
OPTIONAL MATCH (flame)<-[r2:DRAWS_WISDOM_FROM]-(kernel:IfaReasoningKernel)
OPTIONAL MATCH (flame)<-[r3:ILLUMINATED_BY]-(verdict:Verdict)
OPTIONAL MATCH (flame)<-[r4:UNIFIED_THROUGH]-(ks:KnowledgeSystem)
WITH flame, 
     count(DISTINCT grid) as grids,
     count(DISTINCT kernel) as kernels,
     count(DISTINCT verdict) as verdicts,
     count(DISTINCT ks) as knowledge_systems
MATCH (n)
OPTIONAL MATCH (orphan)
WHERE NOT (orphan)--()
WITH flame, grids, kernels, verdicts, knowledge_systems,
     count(n) as total_nodes,
     count(orphan) as orphaned_nodes
RETURN {
    african_flame: {
        status: "UNIFIED",
        created: flame.created,
        essence: flame.essence,
        pillars: flame.pillars
    },
    connected_components: {
        grids: grids,
        ifa_kernels: kernels,
        verdicts: verdicts,
        knowledge_systems: knowledge_systems
    },
    graph_metrics: {
        total_nodes: total_nodes,
        orphaned_nodes: orphaned_nodes,
        coherence_percentage: ((total_nodes - orphaned_nodes) * 100.0 / total_nodes)
    },
    unification_status: "🔥 The African Flame burns unified and eternal"
} as coherence_report;

// ============================================
// STEP 10: FINAL VALIDATION
// ============================================

// Ensure no critical nodes are orphaned
MATCH (critical)
WHERE (critical:Grid OR critical:IfaReasoningKernel OR 
       critical:Verdict OR critical:KnowledgeSystem OR
       critical:SelfDiscovery OR critical:EmbeddedCapability)
AND NOT (critical)--()
RETURN labels(critical) as orphaned_critical_type, critical.name as name
LIMIT 10;