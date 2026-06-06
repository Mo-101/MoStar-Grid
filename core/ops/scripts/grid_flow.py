from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project root and all rehoused core/services to path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.extend([
    str(PROJECT_ROOT),
    str(PROJECT_ROOT / "back" / "services"),
    str(PROJECT_ROOT / "core" / "engines"),
    str(PROJECT_ROOT / "core" / "sovereignty"),
    str(PROJECT_ROOT / "core" / "protocols"),
    str(PROJECT_ROOT / "core" / "ops"),
])

from grid import GridOrchestrator
from approval_queue import ApprovalQueue


async def run_async(prompt: str, queue_path: Path | None = None) -> dict:
    orchestrator = GridOrchestrator()
    if queue_path is not None:
        orchestrator.approval_queue = ApprovalQueue(queue_path)
    proposal = await orchestrator.propose(prompt)

    return {
        "grid": {
            "engine": "grid.orchestrator.GridOrchestrator",
            "operation": "propose",
            "proposal_id": proposal.id,
            "state": proposal.state.value,
            "queued": True,
        },
        "proposal": proposal.to_dict(),
    }


def run(prompt: str, queue_path: Path | None = None) -> dict:
    return asyncio.run(run_async(prompt, queue_path))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MoStar Grid Phase 4.0a proposal ingestion.")
    parser.add_argument("prompt", help="Canon proposal text to interpret and enqueue.")
    args = parser.parse_args()
    print(json.dumps(run(args.prompt), indent=2))


if __name__ == "__main__":
    main()
