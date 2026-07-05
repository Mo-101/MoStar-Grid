# 11B3 Layer Canon Decision

## Current State

During the reconciliation check between Aura and Neon, a drift was detected in the Layer counts:
* **Neon `layer_seal_snapshot`**: 4 Layers (`layer:body`, `layer:mind`, `layer:soul`, **`layer:grid-core`**)
* **Neo4j Aura `Layer` nodes**: 3 Layers (`layer:body`, `layer:mind`, `layer:soul`)

## The Question

Is `layer:grid-core` part of the **canonical Aura graph**, or is it only part of the **Neon seal layer**?

Before we can safely author and apply `11B3` (Body/Mind/Soul Progression), we need to formally decide the canonical status of `grid-core`.

---

## Path A: GridCore is Canonical in Aura

If `grid-core` represents a true foundational semantic layer that belongs in the graph, we must ensure it exists before any progression logic is built upon it.

**Required Action:**
1. Author a precursor script: `11A3_layer_canon_bootstrap.cypher`
2. This script's sole responsibility will be to ensure `layer:body`, `layer:mind`, `layer:soul`, and `layer:grid-core` exist in Aura.
3. Apply `11A3` and verify the reconciliation count becomes `4 == 4`.
4. Proceed to author `11B3`.

## Path B: GridCore is Neon-Only / Non-Canonical

If `grid-core` is purely an infrastructural or ledger-side concept that does not belong in the semantic graph, then the reconciliation script is failing on a false positive.

**Required Action:**
1. Update `reconcile_aura_to_neon.py` (and potentially `generate_neo4j_stats.py` / Neon snapshot logic) to explicitly ignore `layer:grid-core` during parity checks, ensuring only canonical semantic layers are compared.
2. Verify reconciliation passes (`3 == 3`).
3. Proceed to author `11B3`.

---

> [!IMPORTANT]
> Please review and approve either **Path A** or **Path B** so we can lock down the layer canon boundary before moving to the `11B3` progression logic.
