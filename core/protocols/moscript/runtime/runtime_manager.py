"""Fail-closed MoScript RuntimeManager.

Implements the lifecycle defined in MOSCRIPT_RUNTIME_LIFECYCLE.md:
DISCOVER -> VERIFY -> GOVERN -> STAGE -> EXECUTE -> ATTEST -> AUDIT.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import pathlib
import platform
import re
import shutil
import signal
import socket
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import jcs
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .contract_decision import ContractDecision, GovernanceFailure
from .contract_engine import GovernanceEngine
from .mobc import MobcIntegrity, verify_mobc
from .process_supervisor import ProcessOutcome, ProcessSupervisor
from .provenance import ProvenanceStore, ProvenanceResult
from .receipt import (
    RECEIPT_DOMAIN,
    RuntimeReceipt,
    UnsignedRuntimeReceipt,
    sign_receipt,
    verify_receipt as verify_runtime_receipt,
)


class RuntimeState(str, Enum):
    DISCOVERED = "discovered"
    VERIFIED = "verified"
    GOVERNED = "governed"
    STAGED = "staged"
    RUNNING = "running"
    COMPLETED = "completed"
    DENIED = "denied"
    QUARANTINED = "quarantined"
    FAILED = "failed"


class MoScriptProcessError(RuntimeError):
    """Structured failure from the native MoScript binary."""

    def __init__(
        self,
        phase: str,
        returncode: int,
        stdout: str,
        stderr: str,
        reason: str = "NATIVE_FAILURE",
        signal_number: int | None = None,
    ):
        super().__init__(
            f"MoScript {phase} failed with return code {returncode} ({reason}): {stderr or stdout}"
        )
        self.phase = phase
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.reason = reason
        self.signal_number = signal_number
        self.signal_name = signal.Signals(signal_number).name if signal_number and 1 <= signal_number < signal.NSIG else None


@dataclass
class Artifact:
    """A discovered or staged MoScript artifact."""

    path: pathlib.Path
    kind: str
    program_hash: str = ""
    abi_hash: str = ""
    capabilities: list[str] = field(default_factory=list)
    bytecode_hash: str = ""
    verified: bool = False
    integrity: MobcIntegrity | None = None


@dataclass
class RuntimeResult:
    """Result of a full RuntimeManager.execute() lifecycle."""

    state: RuntimeState
    decision: ContractDecision | None = None
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    runtime_output: dict[str, Any] = field(default_factory=dict)
    transitions: list[dict[str, Any]] = field(default_factory=list)
    artifact_hash: str = ""
    attestation: RuntimeReceipt | None = None
    attestation_id: str | None = None
    failure: dict[str, Any] | None = None
    audit_evidence: dict[str, Any] | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    provenance: ProvenanceResult | None = None


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str)


def _extract_json(text: str) -> dict[str, Any] | None:
    """Return the last top-level JSON object or array in a decorated stdout stream."""
    text = text.strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
        return None
    except json.JSONDecodeError:
        pass

    for pattern in (r"\{[\s\S]*\}",):
        matches = list(re.finditer(pattern, text))
        for m in reversed(matches):
            candidate = m.group(0)
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
    return None


def _load_ed25519_private_key(path: pathlib.Path) -> Ed25519PrivateKey:
    b64 = path.read_text(encoding="utf-8").strip()
    raw = base64.b64decode(b64)
    if len(raw) == 64:
        # Go Ed25519 private key format is 32-byte seed + 32-byte public key.
        raw = raw[:32]
    if len(raw) != 32:
        raise ValueError(f"invalid Ed25519 private key length: {len(raw)}")
    return Ed25519PrivateKey.from_private_bytes(raw)


class RuntimeManager:
    """Supervise the full MoScript execution lifecycle, fail-closed."""

    def __init__(
        self,
        contracts_dir: pathlib.Path | str,
        moscript_bin: pathlib.Path | str | None = None,
        max_steps: int = 10000,
        max_depth: int = 64,
        execution_timeout: int = 60,
        max_output_bytes: int = 16 * 1024 * 1024,
        workspace: pathlib.Path | str | None = None,
        receipt_private_key: pathlib.Path | str | None = None,
        runtime_id: str | None = None,
        provenance_store: ProvenanceStore | None = None,
        capability_abi_path: pathlib.Path | str | None = None,
    ):
        self.engine = GovernanceEngine.from_path(contracts_dir)
        self.moscript_bin = (
            pathlib.Path(moscript_bin)
            if moscript_bin is not None
            else self._default_binary()
        )
        if self.moscript_bin.exists():
            mode = self.moscript_bin.stat().st_mode
            if not (mode & 0o111):
                os.chmod(self.moscript_bin, 0o755)
        self.max_steps = max_steps
        self.max_depth = max_depth
        self.execution_timeout = execution_timeout
        self.max_output_bytes = max_output_bytes
        self.workspace = pathlib.Path(
            workspace if workspace is not None else tempfile.mkdtemp(prefix="moscript-")
        )
        self.runtime_id = runtime_id or socket.gethostname()
        self._transitions: list[dict[str, Any]] = []
        self._abi_hash = self._fetch_abi_hash()
        self._capability_abi = self._load_capability_abi(
            capability_abi_path
        ) or set()
        self._receipt_key: Ed25519PrivateKey | None = None
        if receipt_private_key is not None:
            self._receipt_key = _load_ed25519_private_key(pathlib.Path(receipt_private_key))
        self.provenance = provenance_store or ProvenanceStore.from_env()

    def _default_binary(self) -> pathlib.Path:
        here = pathlib.Path(__file__).parent.parent.resolve()
        if platform.system().lower().startswith("win"):
            return here / "moscript-v0.1.1-windows-amd64.exe"
        return here / "moscript-v0.1.1-linux-amd64"

    def _fetch_abi_hash(self) -> str:
        out = self._moscript("abi")
        data = _extract_json(out)
        if not isinstance(data, dict):
            return ""
        return data.get("abi_hash") or ""

    def _load_capability_abi(
        self,
        capability_abi_path: pathlib.Path | str | None,
    ) -> set[str]:
        if capability_abi_path is None:
            here = pathlib.Path(__file__).parent.parent.resolve()
            capability_abi_path = here / "MOSCRIPT_CAPABILITY_ABI_V0_2.json"
        try:
            data = json.loads(pathlib.Path(capability_abi_path).read_text(encoding="utf-8"))
        except Exception:
            return set()
        caps: set[str] = set(data.get("base_capabilities", []))
        for group in (
            "governance_capabilities",
            "entity_capabilities",
            "provenance_capabilities",
            "attestation_capabilities",
            "graph_capabilities",
        ):
            for item in data.get(group, []):
                caps.add(item["id"])
        return caps

    def _moscript(self, *args: str) -> str:
        if not self.moscript_bin.exists():
            raise GovernanceFailure(f"MoScript binary not found: {self.moscript_bin}")
        phase = args[0] if args else "unknown"
        # The output bound is only for native execution commands; metadata
        # commands (abi, check, verify, compile) may emit larger amounts.
        max_output = self.max_output_bytes if phase in ("run", "run-scroll") else None

        supervisor = ProcessSupervisor(
            execution_timeout=self.execution_timeout,
            max_output_bytes=max_output,
        )
        outcome = supervisor.run([str(self.moscript_bin), *args], phase=phase)

        stdout = outcome.stdout.decode("utf-8", errors="replace")
        stderr = outcome.stderr.decode("utf-8", errors="replace")
        if outcome.termination == "exit" and outcome.returncode == 0:
            return stdout

        returncode = outcome.returncode if outcome.returncode is not None else -1
        reason = outcome.termination.upper()
        if outcome.termination == "timeout":
            raise MoScriptProcessError(
                phase=phase,
                returncode=returncode,
                stdout=stdout,
                stderr=stderr or f"TIMEOUT after {self.execution_timeout}s",
                reason="TIMEOUT",
            )
        if outcome.termination == "output_limit":
            raise MoScriptProcessError(
                phase=phase,
                returncode=returncode,
                stdout=stdout,
                stderr=stderr or f"OUTPUT_LIMIT_EXCEEDED: {outcome.stdout_bytes_observed + outcome.stderr_bytes_observed} bytes",
                reason="OUTPUT_LIMIT_EXCEEDED",
            )
        if outcome.termination == "signal":
            raise MoScriptProcessError(
                phase=phase,
                returncode=returncode,
                stdout=stdout,
                stderr=stderr or f"PROCESS_TERMINATED: {outcome.signal_name}",
                reason="PROCESS_TERMINATED",
                signal_number=outcome.signal_number,
            )
        if outcome.termination == "spawn_error":
            raise MoScriptProcessError(
                phase=phase,
                returncode=returncode,
                stdout=stdout,
                stderr=stderr or f"SPAWN_ERROR: errno {outcome.spawn_errno}",
                reason="SPAWN_ERROR",
            )
        raise MoScriptProcessError(
            phase=phase,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr or f"NATIVE_FAILURE: process terminated with code {returncode}",
            reason="NATIVE_FAILURE",
        )

    def _log(self, state: RuntimeState, detail: dict[str, Any] | None = None) -> None:
        self._transitions.append(
            {
                "state": state.value,
                "at": datetime.now(timezone.utc).isoformat(),
                "detail": detail or {},
            }
        )

    def _effective_capabilities(
        self,
        artifact: Artifact,
        allow: list[str] | None,
    ) -> list[str]:
        declared = set(artifact.capabilities)
        principal_allowed = set(allow) if allow is not None else declared

        # Reject capabilities the artifact did not declare.
        if not principal_allowed.issubset(declared):
            raise GovernanceFailure(
                f"capability escalation: {sorted(principal_allowed - declared)} not declared by artifact"
            )

        # Reject capabilities outside the frozen capability ABI.
        if self._capability_abi:
            unknown = declared - self._capability_abi
            if unknown:
                raise GovernanceFailure(
                    f"unknown capabilities: {sorted(unknown)}"
                )

        effective = declared & self._capability_abi & principal_allowed
        return sorted(effective)

    def discover(self, artifact_path: pathlib.Path | str) -> Artifact:
        path = pathlib.Path(artifact_path).resolve()
        if not path.exists():
            raise GovernanceFailure(f"artifact not found: {path}")

        if path.suffix == ".ms":
            kind = "source"
        elif path.suffix == ".mobc":
            kind = "bytecode"
        elif path.suffix == ".moscroll":
            kind = "sealed"
        else:
            raise GovernanceFailure(f"unknown MoScript artifact type: {path.suffix}")

        self._log(RuntimeState.DISCOVERED, {"path": str(path), "kind": kind})
        return Artifact(path=path, kind=kind)

    def stage(self, artifact: Artifact, workspace: pathlib.Path) -> Artifact:
        workspace.mkdir(parents=True, exist_ok=True)
        staged_path = workspace / (
            f"{artifact.path.stem}_{artifact.program_hash[:16] or 'no-hash'}{artifact.path.suffix}"
        )
        shutil.copy2(artifact.path, staged_path)
        staged = Artifact(
            path=staged_path,
            kind=artifact.kind,
            program_hash=artifact.program_hash,
            abi_hash=artifact.abi_hash,
            capabilities=list(artifact.capabilities),
            bytecode_hash=artifact.bytecode_hash,
        )
        self._log(RuntimeState.STAGED, {
            "workspace": str(workspace),
            "staged": str(staged_path),
            "sha256": _sha256_file(staged_path),
        })
        return staged

    def verify(
        self,
        artifact: Artifact,
        public_key: pathlib.Path | str | None = None,
    ) -> Artifact:
        if artifact.kind == "source":
            out = self._moscript("check", str(artifact.path))
            data = _extract_json(out)
            if not isinstance(data, dict):
                raise GovernanceFailure("source check produced no JSON")
            artifact.program_hash = data.get("program_hash", "")
            artifact.abi_hash = data.get("abi_hash", "")
            artifact.capabilities = data.get("required_capabilities") or []

        elif artifact.kind == "bytecode":
            integrity = verify_mobc(artifact.path, self._abi_hash)
            if not integrity.valid:
                raise GovernanceFailure(
                    f"bytecode integrity failed: {integrity.errors}"
                )
            artifact.integrity = integrity
            artifact.program_hash = integrity.program_hash_declared
            artifact.bytecode_hash = integrity.bytecode_hash_computed
            artifact.abi_hash = integrity.abi_hash_declared
            artifact.capabilities = list(integrity.capabilities)

        elif artifact.kind == "sealed":
            args = ["verify"]
            if public_key is not None:
                args.extend(["--pub", str(public_key)])
            args.append(str(artifact.path))
            out = self._moscript(*args)
            data = _extract_json(out)
            if not isinstance(data, dict):
                raise GovernanceFailure("sealed verify produced no JSON")
            if data.get("status") != "verified" and public_key is not None:
                raise GovernanceFailure("sealed scroll verification failed")
            artifact.program_hash = data.get("program_hash", "")
            artifact.bytecode_hash = data.get("bytecode_hash", "")
            artifact.abi_hash = self._abi_hash
            artifact.capabilities = data.get("capabilities") or []

        if artifact.abi_hash and self._abi_hash and artifact.abi_hash != self._abi_hash:
            raise GovernanceFailure(
                f"ABI hash mismatch: artifact {artifact.abi_hash} vs runtime {self._abi_hash}"
            )

        artifact.verified = True
        self._log(RuntimeState.VERIFIED, {
            "program_hash": artifact.program_hash,
            "abi_hash": artifact.abi_hash,
            "capabilities": artifact.capabilities,
        })
        return artifact

    def _govern_contracts(
        self,
        principal: str,
        governing_contracts: list[str] | None,
        governing_events: dict[str, dict] | None,
    ) -> list[ContractDecision]:
        decisions: list[ContractDecision] = []
        governing_contracts = governing_contracts or []
        governing_events = governing_events or {}

        for cid in governing_contracts:
            event = governing_events.get(cid, {})
            decision = self.engine.evaluate(cid, event, principal=principal)
            decisions.append(decision)
            if decision.decision in {"DENY", "ERROR", "QUARANTINE"}:
                return decisions
        return decisions

    def authorize(
        self,
        artifact: Artifact,
        principal: str,
        *,
        governing_contracts: list[str] | None = None,
        governing_events: dict[str, dict] | None = None,
        ecosystem: Any | None = None,
        agent_id: str | None = None,
        action: str | None = None,
    ) -> ContractDecision:
        if ecosystem is not None and agent_id is not None and action is not None:
            decision = self.engine.govern(
                agent_id,
                action,
                ecosystem=ecosystem,
            )
            if not decision.allowed:
                self._log(RuntimeState.DENIED, decision.to_dict())
                return decision

        decisions = self._govern_contracts(
            principal,
            governing_contracts,
            governing_events,
        )
        if decisions and not all(
            d.decision in {"ALLOW", "STAGE_CANDIDATE"} for d in decisions
        ):
            last = decisions[-1]
            self._log(RuntimeState.DENIED, last.to_dict())
            return last

        final = decisions[-1] if decisions else ContractDecision(
            contract_id="runtime.no-governance",
            decision="DENY",
            reason_codes=("NO_GOVERNANCE",),
            input_hash="",
        )
        if not final.allowed:
            self._log(RuntimeState.DENIED, final.to_dict())
            return final

        self._log(RuntimeState.GOVERNED, final.to_dict())
        return final

    def _run(
        self,
        artifact: Artifact,
        effective: list[str],
        public_key: pathlib.Path | str | None,
        workspace: pathlib.Path,
    ) -> tuple[int, str, str, dict[str, Any], dict[str, Any]]:
        allow_str = ",".join(effective) if effective else ""
        common = [
            "--max-steps", str(self.max_steps),
            "--max-depth", str(self.max_depth),
            "--workspace", str(workspace),
        ]
        if allow_str:
            common = ["--allow", allow_str, *common]

        native_meta: dict[str, Any] = {
            "command": None,
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "phase": "run",
        }

        staged = artifact.path
        if staged.suffix == ".moscroll":
            if public_key is None:
                raise GovernanceFailure("sealed scroll execution requires a public key")
            out = self._moscript(
                "run-scroll",
                "--pub", str(public_key),
                *common,
                str(staged),
            )
            native_meta["command"] = "run-scroll"
        else:
            if staged.suffix == ".ms":
                mobc = workspace / (staged.stem + ".mobc")
                self._moscript("compile", "-o", str(mobc), str(staged))
                integrity = verify_mobc(mobc, self._abi_hash)
                if not integrity.valid:
                    raise GovernanceFailure(
                        f"compiled .mobc integrity failed: {integrity.errors}"
                    )
                artifact.bytecode_hash = integrity.bytecode_hash_computed
                staged = mobc
            out = self._moscript("run", *common, str(staged))
            native_meta["command"] = "run"

        native_meta["stdout"] = out
        data = _extract_json(out)
        if data is None:
            data = {"raw_output": out}
        return 0, out, "", data, native_meta

    def _build_and_sign_receipt(
        self,
        execution_id: str,
        attestation_id: str,
        artifact: Artifact,
        effective: list[str],
        decision: ContractDecision,
        runtime_output: dict[str, Any],
        native_meta: dict[str, Any],
        previous_receipt_hash: str | None,
    ) -> RuntimeReceipt:
        issued_at = datetime.now(timezone.utc).isoformat()
        evidence = {
            "execution_id": execution_id,
            "artifact": {
                "path": str(artifact.path),
                "kind": artifact.kind,
                "program_hash": artifact.program_hash,
                "bytecode_hash": artifact.bytecode_hash,
                "abi_hash": artifact.abi_hash,
            },
            "governance": decision.to_dict(),
            "execution": {
                "command": native_meta.get("command"),
                "capabilities": effective,
                "result": runtime_output,
            },
            "binary_hash": self._moscript_bin_hash(),
        }
        evidence_hash = _sha256_canonical(evidence)

        unsigned = UnsignedRuntimeReceipt(
            schema_version=1,
            attestation_id=attestation_id,
            execution_id=execution_id,
            issued_at=issued_at,
            runtime_id=self.runtime_id,
            binary_hash=evidence["binary_hash"],
            program_hash=artifact.program_hash,
            bytecode_hash=artifact.bytecode_hash,
            abi_hash=artifact.abi_hash,
            capabilities=tuple(effective),
            decision=decision.decision,
            result=runtime_output,
            evidence_hash=evidence_hash,
            previous_receipt_hash=previous_receipt_hash,
        )

        if self._receipt_key is not None:
            return sign_receipt(unsigned, self._receipt_key)

        # Unsigned receipt for environments with no configured signing key.
        return RuntimeReceipt(
            **unsigned.to_dict(),
            receipt_hash=unsigned.receipt_hash(),
            signature="",
            signature_algorithm="Ed25519",
            key_id="unsigned",
        )

    def execute(
        self,
        artifact_path: pathlib.Path | str,
        principal: str,
        *,
        governing_contracts: list[str] | None = None,
        governing_events: dict[str, dict] | None = None,
        ecosystem: Any | None = None,
        agent_id: str | None = None,
        action: str | None = None,
        allow: list[str] | None = None,
        public_key: pathlib.Path | str | None = None,
        cleanup: bool = True,
        execution_id: str | None = None,
        woo_judgment: dict[str, Any] | None = None,
    ) -> RuntimeResult:
        """Run the full fail-closed lifecycle."""
        self._transitions = []
        execution_id = execution_id or str(uuid.uuid4())
        exec_workspace = self.workspace / execution_id

        result = RuntimeResult(state=RuntimeState.DISCOVERED)
        artifact: Artifact | None = None
        attestation_id: str | None = None

        try:
            # 1. Discover the original artifact.
            original = self.discover(artifact_path)

            # 2. Stage into an isolated, 0700 workspace to eliminate TOCTOU.
            staged = self.stage(original, exec_workspace)

            # 3. Verify the staged bytes (the same bytes that will execute).
            artifact = self.verify(staged, public_key=public_key)
            attestation_id = self._deterministic_attestation_id(execution_id, artifact)

            # Replay guard: identical (program, execution_id) cannot re-execute.
            attestation_id = self._deterministic_attestation_id(execution_id, artifact)
            if self.provenance.has_attestation(attestation_id):
                existing = self.provenance.get_receipt(attestation_id)
                result.state = RuntimeState.FAILED
                result.artifact_hash = artifact.program_hash
                result.transitions = list(self._transitions)
                result.failure = {
                    "reason": "REPLAY_DETECTED",
                    "execution_id": execution_id,
                    "attestation_id": attestation_id,
                }
                result.audit_evidence = {
                    "program_hash": artifact.program_hash,
                    "failure": result.failure,
                }
                if existing is not None:
                    result.attestation = existing
                    result.attestation_id = existing.attestation_id
                result.evidence = _build_evidence(
                    execution_id,
                    artifact,
                    None,
                    result.transitions,
                    result.attestation,
                    result.audit_evidence,
                )
                return result

            # 4. Govern.
            decision = self.authorize(
                artifact,
                principal,
                governing_contracts=governing_contracts,
                governing_events=governing_events,
                ecosystem=ecosystem,
                agent_id=agent_id,
                action=action,
            )
            result.decision = decision

            if not decision.allowed and decision.decision != "STAGE_CANDIDATE":
                result.state = (
                    RuntimeState.QUARANTINED
                    if decision.decision == "QUARANTINE"
                    else RuntimeState.DENIED
                )
                result.artifact_hash = artifact.program_hash
                result.transitions = list(self._transitions)
                result.audit_evidence = {
                    "program_hash": artifact.program_hash,
                    "governance": {
                        "contract_id": decision.contract_id,
                        "decision": decision.decision,
                        "reason_codes": list(decision.reason_codes),
                        "input_hash": decision.input_hash,
                    },
                }
                result.evidence = _build_evidence(
                    execution_id, artifact, decision, result.transitions,
                    None, result.audit_evidence,
                )
                result.provenance = self.provenance.record_receipt_builder(
                    lambda previous: self._build_unsigned_receipt_from_denial(
                        execution_id,
                        attestation_id,
                        artifact,
                        decision,
                        result.audit_evidence,
                        previous,
                    )
                )
                return result

            # 5. Optional pre-execution Woo gate.
            if woo_judgment is not None and not woo_judgment.get("approved"):
                woo_decision = ContractDecision(
                    contract_id="woo.gate",
                    decision="DENY",
                    reason_codes=("WOO_DENIED",),
                    input_hash="",
                    result={"woo_judgment": woo_judgment},
                )
                self._log(RuntimeState.DENIED, {"woo_judgment": woo_judgment})
                result.state = RuntimeState.DENIED
                result.decision = woo_decision
                result.artifact_hash = artifact.program_hash
                result.transitions = list(self._transitions)
                result.audit_evidence = {
                    "program_hash": artifact.program_hash,
                    "governance": decision.to_dict(),
                    "woo_judgment": woo_judgment,
                }
                result.evidence = _build_evidence(
                    execution_id, artifact, woo_decision, result.transitions,
                    None, result.audit_evidence,
                )
                result.provenance = self.provenance.record_receipt_builder(
                    lambda previous: self._build_unsigned_receipt_from_denial(
                        execution_id,
                        attestation_id,
                        artifact,
                        woo_decision,
                        result.audit_evidence,
                        previous,
                    )
                )
                result.attestation = result.provenance.receipt
                result.attestation_id = result.attestation.attestation_id
                return result

            # 6. Resolve effective capabilities.
            effective = self._effective_capabilities(artifact, allow)
            self._log(RuntimeState.RUNNING, {"staged": str(artifact.path), "capabilities": effective})

            # 6. Execute the exact staged, verified artifact.
            exit_code, stdout, stderr, runtime, native_meta = self._run(
                artifact, effective, public_key, exec_workspace
            )
            result.exit_code = exit_code
            result.stdout = stdout
            result.stderr = stderr
            result.runtime_output = runtime
            result.state = RuntimeState.COMPLETED
            self._log(RuntimeState.COMPLETED, {"exit_code": exit_code})
            result.artifact_hash = artifact.program_hash
            result.transitions = list(self._transitions)

            # 7-8. Attestation, audit, and provenance under a single chain-head lock.
            result.audit_evidence = {
                "transitions": result.transitions,
                "program_hash": artifact.program_hash,
                "governance": decision.to_dict(),
                "execution": {
                    "exit_code": exit_code,
                    "command": native_meta.get("command"),
                    "max_steps": self.max_steps,
                    "max_depth": self.max_depth,
                    "capabilities": effective,
                    "native_meta": native_meta,
                },
            }
            result.provenance = self.provenance.record_receipt_builder(
                lambda previous: self._build_and_sign_receipt(
                    execution_id,
                    attestation_id,
                    artifact,
                    effective,
                    decision,
                    runtime,
                    native_meta,
                    previous,
                )
            )
            result.attestation = result.provenance.receipt
            result.attestation_id = result.attestation.attestation_id
            result.evidence = _build_evidence(
                execution_id, artifact, decision, result.transitions,
                result.attestation, result.audit_evidence,
            )

            # 9. Cleanup on successful completion.
            if cleanup and result.state == RuntimeState.COMPLETED:
                shutil.rmtree(exec_workspace, ignore_errors=True)

        except MoScriptProcessError as exc:
            result.state = RuntimeState.FAILED
            result.stderr = str(exc)
            result.exit_code = exc.returncode
            result.artifact_hash = getattr(artifact, "program_hash", "")
            result.transitions = list(self._transitions)
            result.failure = {
                "phase": exc.phase,
                "reason": exc.reason,
                "returncode": exc.returncode,
                "signal": exc.signal_number,
                "signal_name": exc.signal_name,
                "stdout": exc.stdout,
                "stderr": exc.stderr,
            }
            result.audit_evidence = {
                "failure": result.failure,
                "program_hash": getattr(artifact, "program_hash", ""),
            }
            if (
                artifact is not None
                and artifact.program_hash
                and artifact.abi_hash
                and artifact.bytecode_hash
            ):
                result.provenance = self.provenance.record_receipt_builder(
                    lambda previous: self._build_unsigned_receipt_from_failure(
                        execution_id,
                        attestation_id,
                        artifact,
                        effective if "effective" in locals() else artifact.capabilities,
                        result.failure,
                        result.audit_evidence,
                        previous,
                    )
                )
                result.attestation = result.provenance.receipt
                result.attestation_id = result.attestation.attestation_id
            result.evidence = _build_evidence(
                execution_id, artifact, None, result.transitions,
                result.attestation, result.audit_evidence,
            )

        except Exception as exc:
            result.state = RuntimeState.FAILED
            result.stderr = str(exc)
            result.artifact_hash = getattr(artifact, "program_hash", "")
            result.transitions = list(self._transitions)
            result.audit_evidence = {"error": str(exc)}
            result.evidence = _build_evidence(
                execution_id, artifact, None, result.transitions,
                None, result.audit_evidence,
            )

        return result

    def _build_unsigned_receipt_from_denial(
        self,
        execution_id: str,
        attestation_id: str,
        artifact: Artifact,
        decision: ContractDecision,
        audit: dict[str, Any],
        previous_receipt_hash: str | None,
    ) -> RuntimeReceipt:
        unsigned = UnsignedRuntimeReceipt(
            schema_version=1,
            attestation_id=attestation_id,
            execution_id=execution_id,
            issued_at=datetime.now(timezone.utc).isoformat(),
            runtime_id=self.runtime_id,
            binary_hash=self._moscript_bin_hash(),
            program_hash=artifact.program_hash,
            bytecode_hash=artifact.bytecode_hash,
            abi_hash=artifact.abi_hash,
            capabilities=tuple(artifact.capabilities),
            decision=decision.decision,
            result={"reason_codes": list(decision.reason_codes)},
            evidence_hash=_sha256_canonical(audit),
            previous_receipt_hash=previous_receipt_hash,
        )
        if self._receipt_key is not None:
            return sign_receipt(unsigned, self._receipt_key)
        return RuntimeReceipt(
            **unsigned.to_dict(),
            receipt_hash=unsigned.receipt_hash(),
            signature="",
            signature_algorithm="Ed25519",
            key_id="unsigned",
        )

    def _build_unsigned_receipt_from_failure(
        self,
        execution_id: str,
        attestation_id: str,
        artifact: Artifact,
        effective: list[str],
        failure: dict[str, Any],
        audit: dict[str, Any],
        previous_receipt_hash: str | None,
    ) -> RuntimeReceipt:
        unsigned = UnsignedRuntimeReceipt(
            schema_version=1,
            attestation_id=attestation_id,
            execution_id=execution_id,
            issued_at=datetime.now(timezone.utc).isoformat(),
            runtime_id=self.runtime_id,
            binary_hash=self._moscript_bin_hash(),
            program_hash=artifact.program_hash,
            bytecode_hash=artifact.bytecode_hash,
            abi_hash=artifact.abi_hash,
            capabilities=tuple(effective),
            decision="FAILED",
            result={"failure": failure},
            evidence_hash=_sha256_canonical(audit),
            previous_receipt_hash=previous_receipt_hash,
        )
        if self._receipt_key is not None:
            return sign_receipt(unsigned, self._receipt_key)
        return RuntimeReceipt(
            **unsigned.to_dict(),
            receipt_hash=unsigned.receipt_hash(),
            signature="",
            signature_algorithm="Ed25519",
            key_id="unsigned",
        )

    def _moscript_bin_hash(self) -> str:
        if not self.moscript_bin.exists():
            return ""
        return _sha256_file(self.moscript_bin)

    def _deterministic_attestation_id(
        self, execution_id: str, artifact: Artifact
    ) -> str:
        namespace = uuid.uuid5(
            uuid.NAMESPACE_URL,
            "moscript:"
            f"{self.runtime_id}:"
            f"{execution_id}:"
            f"{artifact.program_hash}:"
            f"{artifact.bytecode_hash or ''}:"
            f"{artifact.abi_hash or ''}",
        )
        return str(namespace)


# ----- module helpers --------------------------------------------------------


def _sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_canonical(obj: Any) -> str:
    return hashlib.sha256(jcs.canonicalize(obj)).hexdigest()


def _build_evidence(
    execution_id: str,
    artifact: Artifact | None,
    decision: ContractDecision | None,
    transitions: list[dict[str, Any]],
    receipt: RuntimeReceipt | None,
    audit: dict[str, Any] | None,
) -> dict[str, Any]:
    ev: dict[str, Any] = {
        "execution_id": execution_id,
        "state": transitions[-1]["state"] if transitions else "failed",
        "transitions": transitions,
    }
    if artifact is not None:
        ev["artifact"] = {
            "path": str(artifact.path),
            "kind": artifact.kind,
            "program_hash": artifact.program_hash,
            "bytecode_hash": artifact.bytecode_hash,
            "abi_hash": artifact.abi_hash,
        }
    if decision is not None:
        ev["governance"] = decision.to_dict()
    if audit is not None:
        ev["audit"] = audit
    if receipt is not None:
        ev["attestation_id"] = receipt.attestation_id
        ev["receipt_hash"] = receipt.receipt_hash
        ev["signature"] = receipt.signature
        ev["signature_algorithm"] = receipt.signature_algorithm
        ev["key_id"] = receipt.key_id
    return ev
