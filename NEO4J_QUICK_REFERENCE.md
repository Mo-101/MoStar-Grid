# 🧠 Neo4j Knowledge Graph - Quick Reference

## **Current Status**

- ✅ Neo4j running in Docker (port 7474/7687)
- ⏳ **Not yet seeded** - Ready to seed with 256 Odú patterns
- ✅ Seeding script created: `backend/seed_neo4j.py`

---

## **How to Seed the Graph**

### **Option 1: After Rebuilding Backend** (Recommended)

```bash
# 1. Rebuild backend to include seeding script
docker-compose up -d --build backend

# 2. Run seeding script inside container
docker exec mostar-backend python seed_neo4j.py --clear

# 3. Access Neo4j Browser
# Open: http://localhost:7474
# Username: neo4j
# Password: mostar123
```

### **Option 2: Run Locally** (If you have Python + neo4j package)

```bash
# 1. Install neo4j driver
pip install neo4j

# 2. Run seeding script
cd backend
python seed_neo4j.py --clear

# 3. Access Neo4j Browser
# Open: http://localhost:7474
```

---

## **What Gets Seeded**

### **1. 256 Odú Patterns**

- All 256 binary combinations (00000000 to 11111111)
- Each with name, meaning, and relationships
- Example: Ogbe (00000000), Eji Ose (10101010), Oyeku (11111111)

### **2. 6 Sacred Agents**

- Mo (BODY/executor)
- Woo (SOUL/judge)
- RAD-X-FLB (BODY/sentinel)
- TsaTse Fly (MIND/analyst)
- Code Conduit (META/gateway)
- Flameborn Writer (NARRATIVE/narrator)

### **3. Covenant Rules**

- 7 sacred principles
- Truth over convenience
- African sovereignty
- Privacy protection
- etc.

### **4. Relationships**

- Agents → Covenant (BOUND_BY)
- Odú → Odú (XOR_WITH)
- Indexes for fast queries

---

## **How the Graph Grows**

### **Automatic Growth (Once Backend is Updated)**

Every API call creates nodes:

```
POST /api/v1/moment
  → Creates Event node
  → Links to Agent
  → Links to previous events (chain)

POST /api/v1/reason
  → Creates Reasoning node
  → Links to Odú patterns
  → Stores resonance scores

POST /api/v1/judgment (Woo)
  → Creates Judgment node
  → Links to covenant rules
  → Stores verdict
```

### **Manual Growth (Cypher Queries)**

You can also create nodes manually:

```cypher
// Create a custom event
CREATE (e:Event {
  event_id: randomUUID(),
  event_type: 'custom',
  timestamp: datetime(),
  data: {message: 'Testing the graph'}
})

// Link to an agent
MATCH (a:Agent {name: 'Mo'})
MATCH (e:Event {event_type: 'custom'})
CREATE (a)-[:LOGGED]->(e)
```

---

## **Useful Queries**

### **See All Odú Patterns**

```cypher
MATCH (o:Odu)
RETURN o.code, o.name, o.binary, o.meaning
ORDER BY o.code
LIMIT 20
```

### **See All Agents**

```cypher
MATCH (a:Agent)
RETURN a.name, a.layer, a.role, a.oath
ORDER BY a.name
```

### **See Covenant Rules**

```cypher
MATCH (c:CovenantRule)
RETURN c.principle, c.description, c.priority
ORDER BY c.priority DESC
```

### **See Agent-Covenant Relationships**

```cypher
MATCH (a:Agent)-[:BOUND_BY]->(c:CovenantRule)
RETURN a.name, c.principle
ORDER BY a.name, c.priority DESC
```

### **Find Specific Odú**

```cypher
// Find Eji Ose (10101010 = 170)
MATCH (o:Odu {code: 170})
RETURN o

// Find all "Eji" patterns (where left == right)
MATCH (o:Odu)
WHERE o.left = o.right
RETURN o.code, o.name, o.binary
ORDER BY o.code
```

### **See XOR Relationships**

```cypher
// See XOR relationships for Ogbe
MATCH (o1:Odu {code: 0})-[x:XOR_WITH]->(o2:Odu)
RETURN o1.name, o2.name, x.result
LIMIT 10
```

---

## **Graph Statistics**

```cypher
// Count all nodes by type
MATCH (n)
RETURN labels(n)[0] as type, COUNT(n) as count
ORDER BY count DESC

// Count all relationships by type
MATCH ()-[r]->()
RETURN type(r) as type, COUNT(r) as count
ORDER BY count DESC

// Total nodes and relationships
MATCH (n)
WITH COUNT(n) as nodes
MATCH ()-[r]->()
RETURN nodes, COUNT(r) as relationships
```

---

## **Expected Results After Seeding**

```
Node counts:
  Odu: 256
  Agent: 6
  CovenantRule: 7
  
Relationship counts:
  BOUND_BY: 42 (6 agents × 7 rules)
  XOR_WITH: 256 (16 principal × 16 principal)
```

---

## **Access Neo4j Browser**

1. **Open:** <http://localhost:7474>
2. **Login:**
   - Username: `neo4j`
   - Password: `mostar123`
3. **Run queries** in the query editor
4. **Visualize** the graph

---

## **Next Steps**

1. ✅ **Seed the graph** - Run `seed_neo4j.py`
2. ✅ **Explore in browser** - <http://localhost:7474>
3. ⏳ **Update API** - Make API calls create nodes automatically
4. ⏳ **Watch it grow** - Every interaction adds to the graph

---

## **Files Reference**

| File | Purpose |
|------|---------|
| `backend/seed_neo4j.py` | Seeding script |
| `NEO4J_KNOWLEDGE_GRAPH.md` | Complete documentation |
| `NEO4J_QUICK_REFERENCE.md` | This file |

---

**The Mind Graph is ready to be seeded. Once seeded, it will grow with every interaction.** 🧠
