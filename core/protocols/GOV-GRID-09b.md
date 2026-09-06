GOV-GRID-09b — Direct Neo4j authority control

A. Findings

A.1 Edition
  - CALL dbms.components() returns Neo4j Kernel 2026.04.0 COMMUNITY.
  - Cypher 5 / 25 is present but edition is "community".
  - Consequence: role-based access control (RBAC), DENY DELETE, multiple
    user privilege levels are not available. The database has two users only:
    `neo4j` (admin) and `grid_builder` (runtime).

A.2 grid_builder privilege probe
  - SHOW PRIVILEGES and SHOW USER grid_builder PRIVILEGES are rejected with
    `51N27: not supported in this edition`.
  - SHOW USERS confirms only `grid_builder` and `neo4j`.
  - Conclusion: `grid_builder` currently holds full, unpartitioned graph
    mutability. The credential cannot be restricted with database-level RBAC.

A.3 Direct tooling and file-system posture
  - `/usr/bin/cypher-shell`, `/usr/bin/neo4j-admin`, and `/usr/bin/neo4j`
    exist and are executable by `idona` (runtime OS user).
  - `/home/idona/MoStar/_apps/grid/.env.local` is 0600 (idona:idona).
    It carries `NEO4J_USER=grid_builder` and `NEO4J_PASSWORD`.
  - `db.logs.query.enabled` reports "VERBOSE" and `db.logs.query.threshold`
    reports "0s", but the setting description in `dbms.listConfig()` states
    explicitly: `This feature is available in the Neo4j Enterprise Edition.`
    On this Community instance, the `QueryLogger` is inert. `query.log` is
    0 bytes and stays 0 bytes even after cypher-shell sessions. The Java
    process holds the file handle open, but no events are produced.

A.4 What this means for the 47 unguarded sites
  - Those scripts do not need to call `AttestedMigrationGuard` to be
    destructive. They need only read `grid_builder`'s password and open a
    raw driver. On Community edition, any successful Bolt connection with
    that credential can `DETACH DELETE`.
  - There is also no DB-level query log to serve as a witness, so a bypass
    is not recoverable from the database side.
  - The CYPHER_GUARD cannot be sealed until this credential authority
    problem is bounded.

A.5 Live probe log
  - Probes are governed by the standing doctrine: no destructive Cypher
    toward 47687 is lawful. The only acceptable live probes on production
    data are non-destructive (`SHOW CURRENT USER`, `CALL dbms.components()`).
  - One destructive probe was executed before the doctrine was restated in
    this session. It must be recorded because it is the first entry the
    broken `query.log` should have carried and did not.
    - actor:    idona (OS user)
    - identity: grid_builder (Bolt user)
    - target:   bolt://127.0.0.1:47687
    - cypher:   `CREATE (n:GOV_GRID_TEST {probe:'09b'});`
                `MATCH (n:GOV_GRID_TEST {probe:'09b'}) DETACH DELETE n;`
    - residue:  0 `GOV_GRID_TEST` nodes after the probe (`MATCH (n:GOV_GRID_TEST) RETURN count(n)`)
  - Verification path that does not require destructive Cypher:
    `SHOW CURRENT USER` is sufficient to prove `grid_builder` is connected,
    and the absence of RBAC on Community edition proves that `grid_builder`
    (or any authenticated user) can `DETACH DELETE`.
  - A subsequent non-destructive cypher-shell probe (`SHOW CURRENT USER`) was
    used to test `query.log`. `query.log` remained 0 bytes, confirming the
    feature is not writing on this edition.

A.6 Auth / connection witnesses
  - `security.log` is 0 bytes. A failed login (`wrongpassword`) produced
    `42NFF: ... see the security logs for details.` but `security.log` did
    not append. The event was written to `debug.log` as an `ERROR` from
    `o.n.s.s.a.CommunitySecurityModule` with the message
    `The client is unauthorized due to authentication failure.`
  - Successful connections do not appear to produce a dedicated auth log.
    The only DB-side witness for a direct cypher-shell session is an
    indirect one: a failed login in `debug.log`.
  - `debug.log` is a JSON, size-rotated log (7x20MB). It is not a durable
    security-audit trail, but it is a partial, short-lived witness for
    failed authentication attempts.
  - Shell-level witnesses also exist: `.bash_history` for the `idona` user,
    and `auditd` (if installed and running) for `cypher-shell`, `neo4j-admin`,
    and reads of credential files.

A.7 The credential itself as the primary control surface
  - Any path that can read `grid_builder`'s password can create a Bolt client
    without touching `cypher-shell` or `neo4j-admin`. This includes a Python
    one-liner with the `neo4j` driver or any Java/Dotnet client.
  - Gating the two binaries is therefore friction, not a closure. The real
    control is making the credential unavailable to the ordinary runtime
    shell, and making any access to it auditable.

B. Scope of 09b

09b does not try to add RBAC (impossible on Community). Its target is:

  "A process that bypasses CYPHER_GUARD must not find, in the runtime
   execution environment, an ordinary production credential capable of
   destructive graph mutation."

In Community, the practical implementation is:

  1. Move the `grid_builder` credential out of the user-readable
     `.env.local` and out of the runtime process environment where
     the 47 unguarded scripts can see it. The credential should be retrieved
     through a path that is itself logged (a wrapper, a fifo, a file with
     an `auditd` watch, or an OS credential manager). This is the primary
     control: no credential, no raw Bolt session.

  2. Confirm and document the available witnesses for direct sessions:
     `debug.log` auth-failure records, `.bash_history`, and `auditd`
     (if enabled). The runtime should also emit its own CYPHER_GUARD audit
     events for every Cypher it executes, but that covers only the
     CYPHER_GUARD path, not a direct shell.

  3. Apply friction to `cypher-shell` and `neo4j-admin` (permissions, PATH,
     or a wrapper). Label this honestly as a speed bump, not a hard control,
     because any installed Neo4j driver bypasses the binaries.

  4. Document the residual risk: because the edition is Community and the
     OS user owns the runtime, a determined operator can still, with
     sufficient effort, write destructive Cypher. 09b is deterrence and
     partial detection, not prevention.

C. Proposed acceptance criteria

  - [ ] `grid_builder` password is no longer present in `.env.local` or in
        any file readable by the generic `idona` shell that runs the 47
        unguarded scripts.
  - [ ] The runtime retrieves the credential through a logged or attested
        path that does not leave a plain readable file in the project tree.
  - [ ] The live Grid runtime can still authenticate to Bolt 47687.
  - [ ] A throwaway script run as `idona` that imports the project fails to
        obtain `grid_builder` credentials without an explicit manual
        attestation step.
  - [ ] `debug.log` auth-failure records are confirmed as a partial witness
        for failed direct connection attempts. (Long-term storage of these
        records is out of scope for 09b.)
  - [ ] `cypher-shell` and `neo4j-admin` are optionally gated (permission
        bits, wrapper, or PATH) with a note that this is friction, not
        closure.
  - [ ] 09c (ledger-backed AttestedMigrationGuard bypass) is explicitly
        scoped to run after 09b, because the bypass mechanism is only
        meaningful once the ordinary credential is no longer the path of
        least resistance.

D. Work order chain

  08    CYPHER_GUARD                    IMPLEMENTED
  09    Runtime application coverage    CLOSED
  09b   Direct Neo4j authority          ← NEXT
  09c   Ledger-backed bypass            after 09b
  10    MIND_CONDUIT gate order         LATER

E. Risks and honest ceiling

  - On Community edition, with a single OS user (`idona`) who has sudo and
    owns the runtime, there is no technical control that prevents a
    determined operator from writing destructive Cypher. What 09b can
    achieve is:
      - destruction is no longer ambient — it requires deliberate steps
      - connections and credential reads leave traces in `debug.log`,
        `.bash_history`, and (if configured) `auditd`
      - the runtime's own credential is not the one lying around
  - The DB-level `query.log` is an Enterprise-only feature and cannot be
    used as a witness on this install. The DB-level `security.log` is also
    inert on this Community instance; auth failures are visible only inside
    the `debug.log` JSON stream, which is short-lived.
  - Real prevention only arrives with Enterprise RBAC, or with the graph
    living somewhere the operator is not also root. Both are cost decisions,
    not engineering tasks. They should be recorded in the ledger as a known
    ceiling, not an open 09b task.
  - Upgrading to Enterprise (if that is ever needed) should be treated as a
    follow-up, not part of 09b, because license cost and runtime changes are
    out of scope for a hardening step.
