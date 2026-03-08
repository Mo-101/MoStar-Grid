#!/usr/bin/env python3
"""
⚙️ Body Layer – API Executor (Real)
Executes real HTTP requests via MoScript-governed rituals.
"""

import asyncio
import json
from core_engine.moscript_engine import MoScriptEngine
from core_engine.mostar_moments_log import log_mostar_moment

class APIExecutor:
    def __init__(self, engine: MoScriptEngine = None):
        self.mo = engine or MoScriptEngine()
        self.layer = "Body Layer"

    async def perform_action(self, endpoint: str, data: dict = None,
                             method: str = "POST", headers: dict = None) -> dict:
        """
        Execute a real HTTP request via the 'http_request' ritual.
        All actions are logged as MoStarMoments and sealed.
        """
        if headers is None:
            headers = {"Content-Type": "application/json"}

        ritual = {
            "operation": "http_request",
            "payload": {
                "url": endpoint,
                "method": method,
                "headers": headers,
                "data": data,
                "timeout": 30
            },
            "target": "Grid.Body"
        }

        # Log intent
        log_mostar_moment(
            initiator="APIExecutor",
            receiver="Grid.Body",
            description=f"Initiating {method} request to {endpoint}",
            trigger_type="api_call",
            resonance_score=0.9,
            layer="BODY"
        )

        response = await self.mo.interpret(ritual)

        if response.get("status") != "aligned":
            error = response.get("error") or "HTTP ritual failed"
            log_mostar_moment(
                initiator="APIExecutor",
                receiver="Grid.Body",
                description=f"API call failed: {error}",
                trigger_type="api_failure",
                resonance_score=0.2,
                layer="BODY"
            )
            return {"error": error, "status": "failed"}

        result = response.get("result", {})
        http_result = result.get("http_response", {})  # adjust based on actual return
        # The ritual should return status_code, headers, body
        return {
            "status": "executed",
            "endpoint": endpoint,
            "response": http_result,
            "seal": response.get("blessing")
        }

# Example usage (if run standalone)
async def main():
    exe = APIExecutor()
    # Example: call a real public API
    result = await exe.perform_action(
        endpoint="https://api.github.com/zen",
        method="GET"
    )
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
