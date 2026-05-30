# Cluster Bootstrap

Phase 4.0a is one sealed sovereign local cluster. A cluster owns one API runtime,
one Docker Neo4j, one approval queue, one provenance ledger, and one human seal
authority.

## 1. Choose Cluster Identity

Set these values in `.env`:

```env
MOSTAR_CLUSTER_ID=nairobi-alpha
MOSTAR_CLUSTER_NAME=Nairobi Health Cluster
MOSTAR_CLUSTER_REGION=east-africa
```

Use lowercase URL-safe IDs for `MOSTAR_CLUSTER_ID`. The ID becomes part of the
cluster data path and every API, proposal, provenance, and graph record.

## 2. Start Cluster Neo4j

Pick a unique HTTP and Bolt port pair for each cluster on the machine.

```bash
docker rm -f mostar-neo4j 2>/dev/null || true

docker volume create mostar_neo4j_data
docker volume create mostar_neo4j_logs

docker run -d \
  --name mostar-neo4j \
  -p 47474:7474 \
  -p 47687:7687 \
  -e NEO4J_AUTH=neo4j/Mogrid101 \
  -e NEO4J_PLUGINS='["apoc"]' \
  -v mostar_neo4j_data:/data \
  -v mostar_neo4j_logs:/logs \
  neo4j:5-community
```

Then set:

```env
NEO4J_URI=bolt://localhost:47687
NEO4J_USER=neo4j
NEO4J_PASSWORD=Mogrid101
NEO4J_HTTP_URL=http://localhost:47474
```

Verify Bolt:

```bash
docker exec mostar-neo4j cypher-shell -u neo4j -p 'Mogrid101' "RETURN 1 AS ok"
```

## 3. Run Constitutional Bootstrap

```bash
source .venv/bin/activate
python scripts/bootstrap_constitutional.py
```

Expected:

```text
Bootstrap complete: 18 nodes, 17 relationships
Receipt written to: data/clusters/nairobi-alpha/bootstrap_receipt.txt
```

All constitutional nodes are tagged with `cluster_id`.

## 4. Verify API Cluster Status

```bash
./run.sh &
sleep 5
curl -s http://localhost:41010/api/status | jq '{cluster_id, cluster_name, mindgraph}'
```

Expected:

```json
{
  "cluster_id": "nairobi-alpha",
  "cluster_name": "Nairobi Health Cluster",
  "mindgraph": {
    "status": "connected"
  }
}
```

Stop the API after verification:

```bash
pkill -f "uvicorn grid.api:app" || true
```

## 5. Test Local Proposal Flow

```bash
curl -s -X POST http://localhost:41010/api/propose \
  -H "Content-Type: application/json" \
  -d '{"canon_input":"Cluster-local Phase 4.0a proposal test."}' | jq .
```

Verify the response includes:

```json
{
  "cluster_id": "nairobi-alpha",
  "state": "PROPOSED"
}
```

Approve only after human review:

```bash
curl -s -X POST http://localhost:41010/api/approve \
  -H "Content-Type: application/json" \
  -d '{"proposal_id":"REPLACE_WITH_PROPOSAL_ID","approved_by":"The Flame Architect"}' | jq .
```

Expected commit scroll fields:

```json
{
  "cluster_id": "nairobi-alpha",
  "state": "COMMITTED",
  "memory_id": "mem_...",
  "moment_id": "moment_..."
}
```

## Multiple Clusters on One Machine

Create a separate Docker container, volumes, and ports per cluster. Example:

```text
nairobi-alpha: 47474/http, 47687/bolt, volumes mostar_neo4j_data/logs
kampala-beta:  47476/http, 47689/bolt, volumes mostar_neo4j_kampala_data/logs
```

Switch `.env` to the target cluster identity and ports before running bootstrap
or the API. Do not point two active clusters at the same approval queue or
provenance path.
