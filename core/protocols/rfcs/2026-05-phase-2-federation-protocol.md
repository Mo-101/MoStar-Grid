# Phase 2 Federation Protocol RFC

**Title:** MoStar Grid Federated Local Clusters v1.0  
**Sealed:** 2026-05-27  
**Authority:** The Flame Architect  
**Status:** LOCKED for Phase 3 execution  
**Change Authority:** Flame Architect only  
**Seal:** 🜃∴🜂

## 1. Purpose & Doctrine

Phase 2 defines the federation protocol enabling multiple MoStar Grid local clusters to verify each other's decisions through portable cryptographic artifacts called scrolls and dynamic attestation sets called councils.

Doctrine:

- Local sovereignty plus portable verification.
- No central authority.
- No replicated global ledger.
- Trust is event-based, not institution-based.
- Evidence stays local; hashes travel.
- Privacy is layered through hashed participant identifiers.
- Offline survivability is required.
- Federation operations are append-only and cryptographically sealed.

## 2. Federation Principles

Each cluster is locally sovereign and owns its API runtime, Docker Neo4j, approval queue, provenance ledger, and human seal authority.

Federation is local-first and attestable. A cluster may export a sealed scroll. Peer clusters may verify, attest, dispute, or request evidence according to regional policy. No cluster becomes global truth.

## 3. Scroll Envelope Spec

A scroll is a portable, cryptographically sealed, attestable covenant artifact that carries a cluster decision with evidence references, gate receipts, attestations, lifecycle metadata, and a cryptographic seal.

Canonical envelope fields:

- `scroll_version`
- `scroll_id`
- `schema_version`
- `cluster`
- `action`
- `participants`
- `inputs`
- `gate_receipts`
- `evidence`
- `human_context`
- `attestations`
- `seal`
- `lifecycle`

Canonical serialization requirement: all scroll hashing and signing uses JSON Canonicalization Scheme (JCS). Field order and byte representation must be deterministic across implementations.

Hashing requirement: Blake3.

Signature requirement: Ed25519.

Scroll lifecycle:

```text
sealed -> attested -> revoked
```

Scrolls are immutable after seal. Attestations are appended as new evidence records referencing the sealed scroll hash.

## 4. Dynamic Council Attestation Model

Councils are not permanent entities. A council is the dynamic set of clusters that co-sign an attestation on a specific scroll.

No council CRUD, no permanent council registry, and no council lifecycle table are allowed in Phase 3.

Regional policy defines eligibility and quorum. Receiving clusters validate:

- attester cluster is eligible under regional policy
- quorum is sufficient for the scroll risk level
- each Ed25519 signature verifies against the sealed scroll hash

## 5. Regional Policy Files

Regional policy files define cluster eligibility and quorum:

```yaml
region: east-africa
eligible_clusters:
  - nairobi-alpha
  - kampala-beta
quorum:
  low: 1
  medium: 1
  high: 2
time_lock_days: 30
```

Policy interpretation beyond simple static eligibility and quorum is deferred.

## 6. Attestation Recording Model

Attestations are recorded in per-cluster append-only JSONL files:

```text
data/clusters/{cluster_id}/attestations/given.jsonl
data/clusters/{cluster_id}/attestations/received.jsonl
data/clusters/{cluster_id}/attestations/disputed_scrolls.jsonl
```

Every entry includes `cluster_id`, `scroll_id`, timestamp, status, peer cluster, signature, and referenced scroll hash.

Daily Blake3 snapshots may be exported and signed. Snapshot automation is not required in Week 1.

## 7. Import/Export Boundary

Normal export sends the scroll envelope, evidence hashes, and signatures. Raw evidence stays local.

Import verifies:

- JCS canonical seal hash
- Blake3 evidence hash format
- Ed25519 cluster signature
- regional policy eligibility when attestations are present

Dispute-triggered evidence pull is allowed only after an imported scroll is marked disputed.

## 8. MCP Gateway Integration

MCP performs light gates:

- Soulprint identity check
- ThroneLock role check
- rate limiting

Cluster API performs heavy gates:

- Woo resonance
- DeepCAL evidence
- Sacred Pause
- audit

MCP is a pre-filter only. Cluster final authority remains local. Direct `/api/propose` still runs cluster-side gates.

## 9. Security & Privacy Model

Participant names are not shared through federation. Scroll participant fields use Blake3 hashes.

Evidence remains local unless dispute access is authorized.

Keys:

- Ed25519 for cluster and guardian signatures.
- Blake3 for evidence hashes and scroll seals.
- JSONL append-only provenance and attestation logs.

## 10. Threat Model

Threats covered in Phase 3:

- tampered scroll payload
- invalid cluster signature
- unauthorized attester
- insufficient quorum
- replayed scroll hash with modified body
- malformed import payload
- unscoped attestation log writes

Threats deferred:

- Byzantine quorum analysis
- zero-knowledge selective disclosure
- cross-region arbitration
- threshold cryptography

## 11. Non-Goals

Phase 3 does not implement:

- replicated global ledger
- permanent council registry
- blockchain anchoring
- automated regional arbitration
- reputation weighting
- advanced privacy proofs

## 12. Open Questions Deferred

- reputation scoring
- key rotation ceremony
- long-term evidence retention policy
- regional appeal process
- automated snapshot publication

## 13. Phase 3 Build Scope

Week 1:

- scroll data model and JSON serializer
- JCS canonicalization and Blake3 sealing
- Ed25519 signing and verification
- per-cluster attestation logs
- unit tests
- scroll versioning support in the seal path

Week 2:

- import/export endpoints
- evidence endpoint skeleton with access control
- MCP light gate integration
- integration tests

Week 3:

- 2-cluster federation live
- dispute flow
- security audit
- load test

## 14. Acceptance Tests

Week 1 acceptance:

- JCS canonical output is deterministic
- Blake3 seal hash changes when payload changes
- Ed25519 signature verifies for sealed scroll
- tampered scroll signature fails
- scrolls carry `cluster_id`
- attestation logs are append-only JSONL
- given, received, and disputed logs are cluster-scoped
- tests pass

## 15. Migration Constraints

Phase 1 local cluster behavior must remain intact.

No existing proposal, approval, provenance, or MindGraph write path may bypass the human approval gate.

Federation adds portable verification; it does not centralize truth.
