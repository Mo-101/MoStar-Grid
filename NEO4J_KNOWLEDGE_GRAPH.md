# 🧠 MoStar Grid - Neo4j Knowledge Graph Growth System

## **The Living Mind Graph**

The Neo4j database is the **MIND** of MoStar Grid - a living, growing knowledge graph that learns from every interaction, decision, and event.

---

## **Current State: Is It Seeded?**

**Short Answer:** Not yet fully seeded, but ready to be.

**What We Have:**

- ✅ Neo4j running in Docker (port 7474/7687)
- ✅ Empty graph database ready for seeding
- ✅ Connection configured in backend (`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`)

**What We Need to Seed:**

1. 256 Odú patterns (the foundation)
2. 6 Sacred agents (the actors)
3. Initial relationships (the structure)
4. Covenant rules (the ethics)

---

## **How the Knowledge Graph Grows**

### **Phase 1: Foundation Seeding (One-Time)**

```
┌─────────────────────────────────────────────────────────────┐
│                    INITIAL SEED                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Create 256 Odú Pattern Nodes                           │
│     - Each Odú has: binary, name, meaning, resonance       │
│                                                             │
│  2. Create 6 Agent Nodes                                   │
│     - Each agent has: name, layer, soulprint, capabilities │
│                                                             │
│  3. Create Covenant Nodes                                  │
│     - FlameCODEX rules and principles                      │
│                                                             │
│  4. Create Initial Relationships                           │
│     - Agents → Layers                                      │
│     - Odú → Odú (XOR relationships)                        │
│     - Agents → Covenant                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### **Phase 2: Event-Driven Growth (Continuous)**

Every time something happens in the Grid, the graph grows:

```
┌─────────────────────────────────────────────────────────────┐
│                    GROWTH TRIGGERS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. MOMENT LOGGED (/api/v1/moment)                         │
│     → Create Event node                                    │
│     → Link to Agent who logged it                          │
│     → Link to Odú pattern (if reasoning involved)          │
│     → Link to previous events (chain)                      │
│                                                             │
│  2. REASONING PERFORMED (/api/v1/reason)                   │
│     → Create Reasoning node                                │
│     → Link to input Odú patterns                           │
│     → Link to collapsed Odú (result)                       │
│     → Store confidence score                               │
│                                                             │
│  3. JUDGMENT RENDERED (Woo)                                │
│     → Create Judgment node                                 │
│     → Link to action being judged                          │
│     → Link to covenant rules applied                       │
│     → Store verdict and resonance                          │
│                                                             │
│  4. MISSION EXECUTED (Mo)                                  │
│     → Create Mission node                                  │
│     → Link to agents involved                              │
│     → Link to decisions made                               │
│     → Store outcomes                                       │
│                                                             │
│  5. ANALYSIS PERFORMED (TsaTse Fly)                        │
│     → Create Analysis node                                 │
│     → Link to systems analyzed                             │
│     → Link to patterns recognized                          │
│     → Store recommendations                                │
│                                                             │
│  6. SURVEILLANCE ALERT (RAD-X-FLB)                         │
│     → Create Alert node                                    │
│     → Link to location                                     │
│     → Link to threat type                                  │
│     → Link to recommended actions                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## **Graph Schema**

### **Node Types**

```cypher
// 1. ODU PATTERNS (256 nodes)
(:Odu {
  code: 0-255,
  binary: "00000000" to "11111111",
  name: "Ogbe", "Oyeku-Ogbe", etc.,
  left: "Ogbe", "Oyeku", etc.,
  right: "Ogbe", "Oyeku", etc.,
  meaning: "Description of wisdom",
  created_at: timestamp
})

// 2. AGENTS (6 nodes)
(:Agent {
  name: "Mo", "Woo", etc.,
  layer: "SOUL", "MIND", "BODY", "META", "NARRATIVE",
  soulprint: "hash...",
  capabilities: ["list", "of", "capabilities"],
  oath: "Sacred commitment",
  created_at: timestamp
})

// 3. EVENTS (grows continuously)
(:Event {
  event_id: "uuid",
  event_type: "moment", "reasoning", "judgment", etc.,
  timestamp: datetime,
  data: {json_payload},
  seal: "MOSEAL:hash:seq"
})

// 4. COVENANT RULES
(:CovenantRule {
  rule_id: "uuid",
  principle: "Truth over convenience",
  description: "Detailed explanation",
  priority: 1-10
})

// 5. MISSIONS
(:Mission {
  mission_id: "uuid",
  title: "Mission name",
  status: "planned", "executing", "completed",
  timestamp: datetime
})

// 6. JUDGMENTS
(:Judgment {
  judgment_id: "uuid",
  verdict: "APPROVED", "DENIED", "CONDITIONAL",
  resonance: 0.0-1.0,
  reasoning: "Explanation",
  timestamp: datetime
})

// 7. ANALYSES
(:Analysis {
  analysis_id: "uuid",
  analysis_type: "systems", "scenario", "risk",
  findings: ["list"],
  recommendations: ["list"],
  timestamp: datetime
})

// 8. ALERTS
(:Alert {
  alert_id: "uuid",
  alert_level: "LOW", "MEDIUM", "HIGH", "CRITICAL",
  threat_type: "disease", "infrastructure", "anomaly",
  location: {geo_data},
  timestamp: datetime
})
```

### **Relationship Types**

```cypher
// Agent relationships
(:Agent)-[:OPERATES_IN]->(:Layer)
(:Agent)-[:BOUND_BY]->(:CovenantRule)
(:Agent)-[:LOGGED]->(:Event)
(:Agent)-[:EXECUTED]->(:Mission)
(:Agent)-[:RENDERED]->(:Judgment)

// Odú relationships
(:Odu)-[:XOR_WITH {result: code}]->(:Odu)
(:Odu)-[:RESONATES_WITH {score: 0.0-1.0}]->(:Odu)
(:Odu)-[:GUIDED]->(:Event)

// Event chains
(:Event)-[:PRECEDED_BY]->(:Event)
(:Event)-[:CAUSED]->(:Event)
(:Event)-[:INVOLVES]->(:Agent)
(:Event)-[:EVALUATED_BY]->(:Odu)

// Mission relationships
(:Mission)-[:COORDINATED_BY]->(:Agent)
(:Mission)-[:INCLUDES]->(:Event)
(:Mission)-[:RESULTED_IN]->(:Outcome)

// Judgment relationships
(:Judgment)-[:JUDGED_BY]->(:Agent {name: "Woo"})
(:Judgment)-[:APPLIED]->(:CovenantRule)
(:Judgment)-[:EVALUATED]->(:Event)
```

---

## **Growth Mechanisms**

### **1. Automatic Growth (Backend API)**

Every API call can create nodes:

```python
# In api_gateway.py

@app.post("/api/v1/moment")
async def log_moment(moment: MomentRequest):
    # 1. Create event in Neo4j
    with driver.session() as session:
        session.run("""
            CREATE (e:Event {
                event_id: $event_id,
                event_type: 'moment',
                timestamp: datetime(),
                data: $data,
                seal: $seal
            })
            
            // Link to agent
            MATCH (a:Agent {name: $agent_name})
            CREATE (a)-[:LOGGED]->(e)
            
            // Link to previous event (chain)
            MATCH (prev:Event)
            WHERE prev.timestamp < e.timestamp
            WITH prev ORDER BY prev.timestamp DESC LIMIT 1
            CREATE (e)-[:PRECEDED_BY]->(prev)
            
            RETURN e
        """, {
            "event_id": str(uuid.uuid4()),
            "data": moment.dict(),
            "seal": generate_seal(moment),
            "agent_name": moment.agent
        })
```

### **2. Ifá Reasoning Growth**

When reasoning happens, relationships form:

```python
@app.post("/api/v1/reason")
async def reason_with_ifa(query: ReasoningQuery):
    # Evaluate against all 256 Odú
    collapsed_odu = evaluate_odu_patterns(query.input_vector)
    
    # Create reasoning node in Neo4j
    with driver.session() as session:
        session.run("""
            // Create reasoning event
            CREATE (r:Reasoning {
                reasoning_id: $reasoning_id,
                query: $query,
                collapsed_to: $collapsed_code,
                confidence: $confidence,
                timestamp: datetime()
            })
            
            // Link to collapsed Odú
            MATCH (o:Odu {code: $collapsed_code})
            CREATE (r)-[:COLLAPSED_TO]->(o)
            
            // Link to all evaluated Odú with resonance scores
            UNWIND $resonances AS res
            MATCH (o:Odu {code: res.code})
            CREATE (r)-[:EVALUATED {resonance: res.score}]->(o)
            
            RETURN r
        """, {
            "reasoning_id": str(uuid.uuid4()),
            "query": query.dict(),
            "collapsed_code": collapsed_odu.code,
            "confidence": collapsed_odu.confidence,
            "resonances": all_resonances
        })
```

### **3. Learning from Patterns**

The graph learns which Odú patterns work best:

```cypher
// Find most successful Odú patterns
MATCH (o:Odu)<-[:COLLAPSED_TO]-(r:Reasoning)
MATCH (r)-[:RESULTED_IN]->(outcome:Event {success: true})
RETURN o.name, o.code, COUNT(outcome) as success_count
ORDER BY success_count DESC
LIMIT 10

// This tells us which patterns lead to good outcomes
```

---

## **How to Query the Growing Graph**

### **Example Queries**

```cypher
// 1. See all events by an agent
MATCH (a:Agent {name: "Mo"})-[:LOGGED]->(e:Event)
RETURN e
ORDER BY e.timestamp DESC
LIMIT 20

// 2. Find event chains
MATCH path = (e1:Event)-[:PRECEDED_BY*]->(e2:Event)
WHERE e1.timestamp > datetime() - duration('P1D')
RETURN path

// 3. See which Odú patterns are most used
MATCH (o:Odu)<-[:EVALUATED_BY]-(e:Event)
RETURN o.name, o.code, COUNT(e) as usage_count
ORDER BY usage_count DESC

// 4. Find covenant violations
MATCH (j:Judgment {verdict: "DENIED"})-[:APPLIED]->(c:CovenantRule)
RETURN c.principle, COUNT(j) as violation_count
ORDER BY violation_count DESC

// 5. Agent collaboration patterns
MATCH (a1:Agent)-[:EXECUTED]->(m:Mission)<-[:EXECUTED]-(a2:Agent)
WHERE a1 <> a2
RETURN a1.name, a2.name, COUNT(m) as collaborations
ORDER BY collaborations DESC

// 6. Odú XOR relationships
MATCH (o1:Odu)-[x:XOR_WITH]->(o2:Odu)
WHERE o1.code = 170  // Eji Ose
RETURN o1.name, o2.name, x.result
```

---

## **Growth Metrics**

The graph health can be measured:

```cypher
// Total nodes by type
MATCH (n)
RETURN labels(n) as type, COUNT(n) as count
ORDER BY count DESC

// Growth rate (events per day)
MATCH (e:Event)
WHERE e.timestamp > datetime() - duration('P7D')
WITH date(e.timestamp) as day, COUNT(e) as events
RETURN day, events
ORDER BY day

// Agent activity
MATCH (a:Agent)-[:LOGGED]->(e:Event)
WHERE e.timestamp > datetime() - duration('P1D')
RETURN a.name, COUNT(e) as events_logged
ORDER BY events_logged DESC

// Covenant adherence rate
MATCH (j:Judgment)
WITH COUNT(j) as total,
     SUM(CASE WHEN j.verdict = 'APPROVED' THEN 1 ELSE 0 END) as approved
RETURN approved * 100.0 / total as approval_rate
```

---

## **Next Steps**

1. **Seed the Foundation** - Run seeding script to create 256 Odú + 6 Agents
2. **Enable Auto-Growth** - Update API endpoints to create nodes on every call
3. **Monitor Growth** - Dashboard showing graph metrics
4. **Query Insights** - Regular queries to learn from accumulated wisdom

The graph starts small but grows with every interaction, becoming smarter over time. 🧠
