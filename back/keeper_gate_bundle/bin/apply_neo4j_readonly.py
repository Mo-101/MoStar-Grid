#!/usr/bin/env python3
"""
apply_neo4j_readonly.py — Recovery Law, Article 2 (final step ONLY).

Sets the sacred graph read-only — but REFUSES unless the runtime split
receipt exists and names all three migrated write streams. This is what
keeps CrypSide's 11-field writeback and the Confidence Gate breathing
until their data has truly left the sacred graph.

Usage:
    sudo python3 apply_neo4j_readonly.py /home/idona/.neo4j_keeper_gate.env /etc/neo4j/neo4j.conf
"""

import sys
import shutil
import time
from pathlib import Path

REQUIRED_LINES = ["Signal migrated", "ExecutionLog migrated", "ExecutorHeartbeat migrated"]
RO_LINE = 'server.databases.read_only=["neo4j"]\n'


def load_env(path: str) -> dict:
    env = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: apply_neo4j_readonly.py <env_file> <neo4j.conf path>")

    env = load_env(sys.argv[1])
    conf = Path(sys.argv[2])
    receipt = Path(env.get("RUNTIME_SPLIT_RECEIPT", "/home/idona/runtime_split_migrated.receipt"))

    # ── The refusal that protects Stage Three ────────────────────────────
    if not receipt.exists():
        sys.exit(
            f"REFUSING: receipt absent at {receipt}.\n"
            "Read-only before the runtime split strangles CrypSide writeback "
            "and stalls the Confidence Gate. Migrate Signal / ExecutionLog / "
            "ExecutorHeartbeat out of the sacred graph FIRST, write the receipt, then return."
        )
    content = receipt.read_text()
    missing = [l for l in REQUIRED_LINES if l not in content]
    if missing:
        sys.exit(f"REFUSING: receipt incomplete. Missing: {missing}")

    if not conf.exists():
        sys.exit(f"REFUSING: {conf} not found. Name the true conf path.")

    text = conf.read_text()
    if "server.databases.read_only" in text:
        sys.exit("Already configured read-only. Nothing to do.")

    backup = conf.with_suffix(conf.suffix + f".bak.{int(time.time())}")
    shutil.copy2(conf, backup)
    conf.write_text(text.rstrip("\n") + "\n\n# Keeper Gate: sacred memory is read-mostly\n" + RO_LINE)

    print(f"Patched {conf} (backup at {backup}).")
    print("Restart Neo4j to apply. To open a write/import window:")
    print("  remove the read_only line → restart → import → golden dump → restore line → restart.")


if __name__ == "__main__":
    main()
