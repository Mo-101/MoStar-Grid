"""Build the canonical runtime attestation manifest."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]

# Component files whose content identifies the executable runtime.
# These must not contain secrets or environment values.
COMPONENTS = {
    "moscript_engine": "core/protocols/moscript/__init__.py",
    "covenant": "core/ops/governance/GRID_MIND_CONSTITUTION.md",
    "truth_engine": "core/engines/woo/__init__.py",
    "heartbeat": "core/ops/runtime_attestation/heartbeat.py",
    "verifier": "core/ops/runtime_attestation/verifier.py",
    "manifest": "core/ops/runtime_attestation/manifest.py",
}


def canonical_json(value: Any) -> str:
    """Stable, deterministic JSON for hashing."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_commit() -> str:
    return _git("rev-parse", "HEAD")


def git_tree_clean() -> bool:
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
    return all(not line.strip() for line in status.splitlines())


def component_hashes() -> dict[str, str]:
    return {
        name: sha256_file(ROOT / rel)
        for name, rel in COMPONENTS.items()
    }


def build_runtime_manifest(
    system_id: str = "mostar.grid",
    runtime_id: str = "mostar.grid.runtime",
    runtime_version: str = "0.1.0",
) -> dict[str, Any]:
    components = component_hashes()

    binding = {
        "schema_version": "1",
        "system_id": system_id,
        "runtime_id": runtime_id,
        "runtime_version": runtime_version,
        "build_commit": git_commit(),
        "components": components,
    }

    runtime_digest = sha256_json(binding)

    manifest = {
        **binding,
        "build_timestamp": datetime.now(timezone.utc).isoformat(),
        "runtime_digest": runtime_digest,
    }

    return manifest


def runtime_digest_from_manifest(manifest: dict[str, Any]) -> str:
    """Recompute the digest from a manifest, ignoring observation fields."""
    binding = {
        "schema_version": manifest["schema_version"],
        "system_id": manifest["system_id"],
        "runtime_id": manifest["runtime_id"],
        "runtime_version": manifest["runtime_version"],
        "build_commit": manifest["build_commit"],
        "components": manifest["components"],
    }
    return sha256_json(binding)


def recompute_and_compare(manifest: dict[str, Any]) -> list[str]:
    """Return a list of failures if the manifest does not match the current tree."""
    failures = []

    expected_commit = git_commit()
    if manifest.get("build_commit") != expected_commit:
        failures.append(
            f"build_commit mismatch: "
            f"expected {expected_commit}, got {manifest.get('build_commit')}"
        )

    current_components = component_hashes()
    stored_components = manifest.get("components", {})
    for name, current_hash in current_components.items():
        stored_hash = stored_components.get(name)
        if stored_hash != current_hash:
            failures.append(
                f"component {name} hash mismatch: "
                f"expected {current_hash}, got {stored_hash}"
            )

    expected_digest = runtime_digest_from_manifest(manifest)
    if manifest.get("runtime_digest") != expected_digest:
        failures.append(
            f"runtime_digest mismatch: expected {expected_digest}, "
            f"got {manifest.get('runtime_digest')}"
        )

    return failures
