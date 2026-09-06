# Mind Conduit Invocation Remediation Evidence

Generated: 2026-08-16T13:43:25.884472+00:00

## 1. Locked status

The literal audit state appears at the end of this report.

Invocation-surface closure precedes guard verification: Cypher, Provenance, and Attestation cannot be system-level verified while any production inference path bypasses their composition.

## 2. §3 invocation-surface ledger

Discovered surfaces: **19**  
Accounted surfaces: **19**  
Unauthorized surfaces: **0**

`discovered_surfaces == accounted_surfaces`: **PASS**

Historical grouping: ORIGINAL_AUTHORIZED=**2**, MIGRATED_FORMERLY_UNAUTHORIZED=**11**, NEWLY_DISCOVERED_NEWLY_AUTHORIZED=**6**

| ID | Source | Symbol | Mechanism | Runtime/provider | Transport | Conduit | Binding | Capability | Disposition | Evidence |
|---|---|---|---|---|---|---:|---:|---:|---|---|
| 4d57ae73ad50837d | back/services/grid/api.py | 491:_envelope | MIND_CONDUIT_CALL | mind_conduit_call / unresolved | OTHER | False | False | False | CONDUIT_INTERNAL | back/services/grid/api.py:491 |
| c0027622c66d9bd9 | back/services/grid/api.py | 495:_envelope | GOVERNED_ADAPTER_CALL | governed_adapter_call / unresolved | OTHER | False | False | False | CONDUIT_INTERNAL | back/services/grid/api.py:495 |
| a9ebb67c8e4eb559 | back/services/grid/api.py | 648:invoke_mostar_voice_model | MIND_CONDUIT_CALL | mind_conduit_call / unresolved | OTHER | False | False | False | CONDUIT_INTERNAL | back/services/grid/api.py:648 |
| e1bb12df2720b677 | back/services/grid/api.py | 652:invoke_mostar_voice_model | GOVERNED_ADAPTER_CALL | governed_adapter_call / unresolved | OTHER | False | False | False | CONDUIT_INTERNAL | back/services/grid/api.py:652 |
| 37af8a607814cdba | back/services/grid/api.py | 1035:get_autonomous_briefing | MIND_CONDUIT_CALL | mind_conduit_call / unresolved | OTHER | False | False | False | CONDUIT_INTERNAL | back/services/grid/api.py:1035 |
| 84b182515c52d36f | back/services/grid/api.py | 1040:get_autonomous_briefing | GOVERNED_DCX_CALL | governed_dcx_call / unresolved | OTHER | False | False | False | CONDUIT_INTERNAL | back/services/grid/api.py:1040 |
| de5b7b75ec5c72ca | back/services/grid/mind_conduit_runtime.py | 11:<module> | RAW_MODEL_HTTP | ollama-compatible / ollama/local | LOCAL_HTTP | True | True | True | CONDUIT_INTERNAL | back/services/grid/mind_conduit_runtime.py:11 |
| 9f02fc4dca9a0e43 | back/services/grid/mind_conduit_runtime.py | 12:<module> | RAW_MODEL_HTTP | ollama-compatible / ollama/local | LOCAL_HTTP | True | True | True | CONDUIT_INTERNAL | back/services/grid/mind_conduit_runtime.py:12 |
| e5c2c4ea7ed4d817 | back/services/grid/mind_conduit_runtime.py | 28:invoke_model | MIND_CONDUIT_CALL | mind_conduit_call / unresolved | OTHER | True | True | True | CONDUIT_INTERNAL | back/services/grid/mind_conduit_runtime.py:28 |
| 6964202e0f2753db | back/services/grid/mind_conduit_runtime.py | 48:governed_http_post | GOVERNED_ADAPTER_CALL | governed_adapter_call / unresolved | OTHER | True | True | True | CONDUIT_INTERNAL | back/services/grid/mind_conduit_runtime.py:48 |
| de5820c9b2176f27 | back/services/grid/mind_conduit_runtime.py | 55:governed_http_post | RAW_MODEL_HTTP | ollama-compatible / ollama/local | LOCAL_HTTP | True | True | True | CONDUIT_INTERNAL | back/services/grid/mind_conduit_runtime.py:55 |
| 193e7a4304a66709 | back/services/grid/mind_conduit_runtime.py | 60:invoke_dcx | GOVERNED_DCX_CALL | governed_dcx_call / unresolved | OTHER | True | True | True | CONDUIT_INTERNAL | back/services/grid/mind_conduit_runtime.py:60 |
| bcd633bda72f564f | back/services/grid/orchestrator.py | 325:think | MIND_CONDUIT_CALL | mind_conduit_call / unresolved | OTHER | False | False | False | CONDUIT_INTERNAL | back/services/grid/orchestrator.py:325 |
| 0ee5833ef166b5c6 | back/services/grid/orchestrator.py | 329:think | GOVERNED_DCX_CALL | governed_dcx_call / unresolved | OTHER | False | False | False | CONDUIT_INTERNAL | back/services/grid/orchestrator.py:329 |
| c516633d36fb6ed7 | core/engines/semantic_grid/layers.py | 158:extract_layers | MIND_CONDUIT_CALL | mind_conduit_call / unresolved | OTHER | False | False | False | CONDUIT_INTERNAL | core/engines/semantic_grid/layers.py:158 |
| eaf06b38f762f1cb | core/engines/semantic_grid/layers.py | 162:extract_layers | GOVERNED_ADAPTER_CALL | governed_adapter_call / unresolved | OTHER | False | False | False | CONDUIT_INTERNAL | core/engines/semantic_grid/layers.py:162 |
| f8ce1ecde6327288 | core/protocols/dcx/__init__.py | 282:think | GOVERNED_ADAPTER_CALL | governed_adapter_call / unresolved | OTHER | False | False | False | CONDUIT_INTERNAL | core/protocols/dcx/__init__.py:282 |
| 8d6598438483da67 | front/app/src/lib/mind/dcx-adapter.ts | 51:GridModelAdapter | MODEL_METHOD | model_method / unresolved | OTHER | True | True | True | CONDUIT_INTERNAL | front/app/src/lib/mind/dcx-adapter.ts:51 |
| 7db958a7c398ae22 | front/app/src/lib/mind/mind-conduit.ts | 79:MindConduit | MODEL_METHOD | model_method / unresolved | OTHER | True | True | True | CONDUIT_INTERNAL | front/app/src/lib/mind/mind-conduit.ts:79 |

Every row also carries the required Grid-level effect columns in the companion JSON ledger. Unproven effects are `UNRESOLVED`, not inferred.

### Addendum 05 remediation disposition for the prior 11 unauthorized rows

| Prior evidence | Disposition | Current governed evidence |
|---|---|---|
| `back/services/grid/api.py:478` | Routed deep model health through `invoke_model` and governed HTTP adapter | `api.py:491`, `api.py:495` |
| `back/services/grid/api.py:612` | Replaced direct helper boundary with governed voice-model entrypoint | `api.py:648` |
| `back/services/grid/api.py:630` | Moved raw chat transport behind governed HTTP adapter | `api.py:652` |
| `back/services/grid/api.py:859` | Announcement caller now reaches only the governed voice-model entrypoint | `api.py:648` |
| `back/services/grid/api.py:1016` | Snapshot reasoning routed through `invoke_model` and `invoke_dcx` | `api.py:1035`, `api.py:1040` |
| `back/services/grid/api.py:1147` | Voice command caller now reaches only the governed voice-model entrypoint | `api.py:648` |
| `back/services/grid/orchestrator.py:323` | Orchestrator reasoning routed through universal conduit and governed DCX adapter | `orchestrator.py:325`, `orchestrator.py:329` |
| `core/engines/semantic_grid/layers.py:152` | Semantic inference routed through universal conduit and governed HTTP adapter | `layers.py:158`, `layers.py:162` |
| `core/ops/scripts/dcx_readiness.py:66` | Unauthorized inference removed; CLI reports model presence as `LOADED` only | no inference surface |
| `core/protocols/dcx/__init__.py:265` | DCX transport requires `GridModelInvocationContext` and governed HTTP adapter | `dcx/__init__.py:282` |
| `scripts/dcx_readiness.py:52` | Unauthorized inference removed; CLI reports model presence as `LOADED` only | no inference surface |

### Six newly discovered/newly authorized backend conduit surfaces

All six are in `back/services/grid/mind_conduit_runtime.py`, introduced during Addendum 05 remediation and detected by the expanded raw-endpoint, `invoke_model`, governed-adapter, and governed-DCX signatures.

| Evidence | Surface role | Exact path / capability proof | Model effects | Commit / test evidence |
|---|---|---|---|---|
| `mind_conduit_runtime.py:11` | Ollama generate transport identifier | caller → `invoke_model` → issued `GridModelInvocationContext` → `governed_http_post` allow-list → runtime | Sees only adapter payload; retrieves/proposes/changes/remembers nothing itself | `WORKTREE_UNCOMMITTED`; canonical schema + hostile suite |
| `mind_conduit_runtime.py:12` | Ollama chat transport identifier | same governed transport boundary; no independent invocation authority | Same transport-only effects | `WORKTREE_UNCOMMITTED`; canonical schema + hostile suite |
| `mind_conduit_runtime.py:28` | Universal `invoke_model` entrypoint | verifies canonical `GRID_MIND_READY`, issues unforgeable capability, then calls governed adapter | Receives caller/model/snapshot identities; no canonical write authority | `WORKTREE_UNCOMMITTED`; direct-bypass and drift tests |
| `mind_conduit_runtime.py:48` | Governed HTTP adapter | requires `context.assert_valid()`, restricts transport path, then invokes runtime | Can send the explicitly supplied governed payload; no memory retrieval or state write | `WORKTREE_UNCOMMITTED`; HP-7 and scanner evidence |
| `mind_conduit_runtime.py:55` | Transport allow-list enforcement | reachable only inside governed HTTP adapter after capability validation | Restricts runtime endpoint; cannot retrieve/propose/change/remember | `WORKTREE_UNCOMMITTED`; static scanner evidence |
| `mind_conduit_runtime.py:60` | Governed DCX adapter | requires valid context, passes it into DCX, whose runtime transport also validates it | Sees governed query/context arguments; output remains model-originated; no direct canonical write | `WORKTREE_UNCOMMITTED`; HP-7 and scanner evidence |

The 13→19 change is architectural refactoring, not discovery of six old hidden calls: these six source surfaces were introduced with the backend conduit module. Eleven old bypass rows became eleven governed rows; two original authorized rows remained.

## 3. Sweep methodology

The scanner walks all executable Python, TypeScript, JavaScript, and shell source. Signatures cover raw model HTTP, Ollama/OpenAI/Anthropic-compatible clients, generic invoke/generate/chat/embed/predict methods, local pipelines, subprocess runners, DCX/orchestrator wrappers, and registered adapter contracts. Examples are non-exhaustive.

Excluded directories and reasons:

- `.git`: repository metadata.
- `.tmp`: temporary artifacts.
- `.venv`: third-party environment.
- `__pycache__`: generated bytecode.
- `data`: runtime data, not executable source.
- `dist`: generated build output.
- `logs`: runtime output, not source.
- `mindgraph`: runtime graph data.
- `node_modules`: vendored dependencies.
- `scratch`: non-production scratch space.

Tests are excluded from the production call-site count and validated by the hostile-path suite. Generated/vendor outputs are excluded because their source inputs are scanned.

## 4–5. Authorized and unauthorized sites

Authorized: **19**. Unauthorized: **0**. See the ledger above and JSON evidence.

## 6. HP-7 history

- Historical definition: `HP-7 rejects direct DCX invocation`.
- Later definition: `direct MODEL bypass` with DCX retained as one fixture.
- Current executable tests: `mind-conduit.hostile.test.ts` symbols `HP-7A` and `HP-7C`; static census supplies HP-7B/HP-7D evidence.
- Change reference: §4 ratification implementation; repository commit reference unavailable in the working tree.
- Audit interpretation: **UNRESOLVED — CLAUDE DECIDES**.

## 7. Gate-name history

`INVOCATION_AUDIT` is a historical alias only. It is retained in ledger history and is not a second live gate.

## 8–9. Universal enforcement and static result

`GridModelInvocationContext` and `GovernedModelAdapter` are model-name agnostic. The static gate fails whenever unauthorized sites are nonzero or constitutional scope assertions disappear.

`INVOCATION_SURFACE_GUARD = SEALED`

Canonical schema consumers:

- Builder: `builder.packet.ts` imports `deriveGridReadiness`, `deriveInvocationSurfaceGuard`, and `deriveMoScriptRegistryHealth`.
- bootConductor/dashboard: project Builder/API status and do not derive readiness.
- `/api/status`: `canonical_evidence.py` loads `MIND_CONDUIT_CANONICAL_EVIDENCE.json` without recomputation.
- CI: `canonical-schema-integration.test.ts` executes all three canonical derivations against durable artifacts.
- Seal-receipt guard: `seal-receipt-guard.ts` consumes `GridReadiness` and requires `HumanAuthorization` plus a committed source identifier.
- Deployment report: this generated evidence package projects the canonical evidence object.

## 10–12. Constitution, manifests, and receipt

- Current constitution SHA-256: `02913f525e263737d87a8625bdc97efc940ffcfb6e6e58f09cb5cbbe573be0b2`.
- Constitution hash lineage: `GENESIS`.
- Classification evidence: governance constitution entered source control at commit `16387525`; `git log -S constitution_hash` and `git log -S constitutionHash` return no prior custody record; historical Grid manifests contain no constitution-hash field; no predecessor hash is fabricated.
- HP arithmetic: nine identifiers (`HP-1`…`HP-9`) produce ten executable cases because `HP-4` has two required cases, `HP-4A` timeout and `HP-4B` unreachable/5xx.
- Manifest state: `CONSTITUTION_DRIFT`; per-model runtime details remain builder evidence and are not invented here.
- Seal receipt: **WITHHELD** — constitutional drift, unauthorized call sites, and hostile-path revalidation required.
- HP-9 implemented: **YES** at `front/app/src/lib/mind/seal-receipt-guard.test.ts`, symbol `HP-9 withholds a receipt when all six gates pass but HumanAuthorization is absent`; included in the original sixteen focused tests: **false**; actual result: **PASS**.
- MoScript/runtime mapping: `core/ops/status/MOSCRIPT_RUNTIME_IMPLEMENTATION_MAP.json`.
- Post-closure hostile evidence: `core/ops/status/HOSTILE_PATH_POST_CLOSURE_EVIDENCE.json`; isolated cases passed: **True**; live gate remains **UNVERIFIED**.

| MoScript | Source digest | Implementation | Symbol | Implementation digest | Commit |
|---|---|---|---|---|---|
| mo-mind-cypher-guard-001 | `6e123ec2865a6aa24ab089a55cfa20a1675603ae2e449a5a298dd7eaa1c778d1` | front/app/src/lib/mind/cypher-guard.ts | CypherGuard | `f56b1bb194ec62827dc106e5859239194b94c2f7e7d9431ef40c4d06456c9c28` | `WORKTREE_UNCOMMITTED` |
| mo-mind-attestation-guard-001 | `691a03b220306c7af99c252167a7b09a6121959d1ace77b6ac715c14011ea125` | front/app/src/lib/mind/attestation-guard.ts | AttestationGuard | `545bc7fd49da7947337f452904a2c49b003b03de8c8723954782367cdd4c4764` | `WORKTREE_UNCOMMITTED` |
| mo-mind-provenance-filter-001 | `18dfc6de4f88ae367098f0f353359bc83b84179e2db0432a13ac4120221a26f7` | front/app/src/lib/mind/provenance-filter.ts | ProvenanceFilter | `31724f9c0c4b163929e53fead5048fd295d2bdbd599bbff883176ff1d7d459ba` | `WORKTREE_UNCOMMITTED` |
| mo-mind-conduit-001 | `9fabf02a227be7f11d68001359cb0dc0e6859f4271d875758ec1e426f9ac7fab` | front/app/src/lib/mind/mind-conduit.ts | MindConduit | `e411d0569f159dfb2479ecd1741a9b41f310d7812418352e7088fd5fa7f2a9fa` | `WORKTREE_UNCOMMITTED` |
| mo-mind-conduit-001 | `9fabf02a227be7f11d68001359cb0dc0e6859f4271d875758ec1e426f9ac7fab` | back/services/grid/mind_conduit_runtime.py | invoke_model | `60439ee258216d0d25ec9bf8e148d1f4cc530138c97263cb0b3ef71ab62bb0e5` | `WORKTREE_UNCOMMITTED` |
| mo-mind-cypher-guard-001 | `6e123ec2865a6aa24ab089a55cfa20a1675603ae2e449a5a298dd7eaa1c778d1` | front/app/src/lib/mind/constitution-composition.ts | verifyConstitutionComposition | `cdebe429edffa3efdd9881b3e3f844325263bf083849d4390cca7a226386f529` | `WORKTREE_UNCOMMITTED` |
| mo-mind-provenance-filter-001 | `18dfc6de4f88ae367098f0f353359bc83b84179e2db0432a13ac4120221a26f7` | front/app/src/lib/mind/constitution-composition.ts | assertConstitutionComposition | `cdebe429edffa3efdd9881b3e3f844325263bf083849d4390cca7a226386f529` | `WORKTREE_UNCOMMITTED` |
| mo-mind-attestation-guard-001 | `691a03b220306c7af99c252167a7b09a6121959d1ace77b6ac715c14011ea125` | front/app/src/lib/mind/constitution-composition.ts | assertConstitutionComposition | `cdebe429edffa3efdd9881b3e3f844325263bf083849d4390cca7a226386f529` | `WORKTREE_UNCOMMITTED` |

```text
MODEL_BINDING             = CONSTITUTION_DRIFT
CYPHER_GUARD              = UNVERIFIED
PROVENANCE_FILTER         = UNVERIFIED
ATTESTATION_GUARD         = UNVERIFIED
INVOCATION_SURFACE_GUARD  = UNVERIFIED
HOSTILE_PATH_TEST         = UNVERIFIED
---------------------------------------
MIND_CONDUIT              = PARTIAL
GRID_MIND_READY           = false
```
