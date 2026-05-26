# Neo4j Checkpoint Status

**Date:** 2026-05-26  
**Phase:** 4.0a Audit Freeze  
**Status:** Pending elevated Neo4j authority

## Observed State

```text
Neo4j HTTP port: 7474 listening
Neo4j Bolt port: 7687 listening
Neo4j service: active
cypher-shell: available
neo4j-admin: available
```

## Checkpoint Attempt

Non-disruptive checkpoint procedure attempted with `cypher-shell`:

```cypher
CALL db.checkpoint()
```

Result:

```text
42NFF: syntax error or access rule violation - permission/access denied.
Access denied, see the security logs for details.
```

## Physical Dump Note

`neo4j-admin database dump` is available, but Neo4j reports that a mounted database cannot be dumped while the server is running. Stopping Neo4j was not performed during this audit freeze because runtime/data-service interruption was not explicitly authorized.

## Required Follow-Up

Use an admin-authorized Neo4j account for logical checkpoint, or schedule a controlled Neo4j stop window for physical dump:

```bash
sudo systemctl stop neo4j
neo4j-admin database dump neo4j --to-path=data/checkpoints --overwrite-destination=true
sudo systemctl start neo4j
```

Do not run the stop/dump/start sequence without explicit Flame authorization.
