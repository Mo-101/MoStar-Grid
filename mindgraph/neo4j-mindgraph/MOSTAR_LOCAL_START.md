# Local Neo4j (no Docker) — Windows

This repo includes a local Neo4j distribution in `backend/neo4j-mostar-industries/`.

## 1) Start Neo4j (recommended)

From File Explorer, double-click:

- `backend/neo4j-mostar-industries/start-neo4j.cmd`

Or from PowerShell:

- `cd backend/neo4j-mostar-industries`
- `.\start-neo4j.ps1`

On first run it will extract the bundled JDK 21 from `jdk21.zip` into `.tools/` at the repo root, then start Neo4j.

## 2) If Docker Neo4j is running (ports 7474/7687)

Local Neo4j and Docker Neo4j cannot both bind `7474` + `7687` at the same time.

Either stop it manually:

- `docker stop mostar-neo4j`

Or let the launcher stop it:

- `.\start-neo4j.ps1 -StopDocker`

## 3) Quick “is Java 21 working?” preflight

- `cd backend/neo4j-mostar-industries`
- `.\start-neo4j.ps1 -Preflight`

This checks Java selection and runs `neo4j-admin --version` without starting the server.

## 4) Connect

- HTTP UI: `http://localhost:7474`
- Bolt: `bolt://localhost:7687`

MoStar backend defaults are in `.env`:

- `NEO4J_URI=bolt://localhost:7687`
- `NEO4J_USER=neo4j`
- `NEO4J_PASSWORD=mostar123`

