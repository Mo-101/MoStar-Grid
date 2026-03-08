#!/usr/bin/env python3
"""
⚖️ Truth Engine — Mind Layer
----------------------------
Ensures moral, logical, and symbolic alignment across the Grid.
Validates MoScript seals and verdict authenticity.
"""

import json
from core_engine.moscript_engine import MoScriptEngine

class TruthEngine:
    def __init__(self, engine: MoScriptEngine = None):
        """
        Initializes the Truth Engine with a MoScript Engine instance.
        
        Args:
            engine: Optional MoScriptEngine instance. If not provided, creates a new one.
        """
        self.mo = engine or MoScriptEngine()
        self.layer = "Mind Layer"

    async def verify_seal(self, payload: dict):
        """
        Verifies a MoScript seal by invoking the engine's 'verify_seal' operation.
        This ensures the Truth Engine does not bypass the Covenant's own sealing logic.
        """
        ritual = {
            "operation": "verify_seal",
            "payload": payload,
            "target": "Grid.Soul"
        }
        return await self.mo.interpret(ritual)

if __name__ == "__main__":
    import asyncio
    async def main():
        truth = TruthEngine()
        # Sample payload with signature to verify
        sample = {
            "data": {"agent": "Mo-101", "action": "ingest"},
            "signature": "seal:a1b2c3d4"
        }
        result = await truth.verify_seal(sample)
        print(json.dumps(result, indent=4))
    asyncio.run(main())
