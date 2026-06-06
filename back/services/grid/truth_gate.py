# back/services/grid/truth_gate.py
"""
TruthGate Reporting Engine — MoStar Grid
The Five Laws:
  Observed ≠ Inferred
  Configured ≠ Running
  Declared ≠ Verified
  Available ≠ Proven
  Synthetic State ≠ Public Truth
"""
import os
import json
import socket
import httpx
from typing import Dict, Any, Optional
from pydantic import BaseModel


class TruthGateRecord(BaseModel):
    component: str
    observed: bool
    configured_value: Optional[str] = None
    verified_running: bool = False
    evidence: Optional[str] = None
    inference: Optional[str] = None
    risk_level: str = "UNDETERMINED"


class TruthGateEngine:
    def __init__(self, workspace_root: str = "/home/idona/MoStar/_apps/grid"):
        self.workspace_root = workspace_root

    def verify_socket(self, host: str, port: int) -> bool:
        """Attempts a raw TCP socket handshake to prove operational live status."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1.0)
                s.connect((host, port))
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def verify_http_health(self, url: str) -> tuple[bool, str]:
        """Queries explicit HTTP endpoints to extract deep structural health indicators."""
        try:
            with httpx.Client() as client:
                response = client.get(url, timeout=1.5)
                if response.status_code == 200:
                    return True, f"HTTP 200 OK: {response.text.strip()}"
                return False, f"HTTP Error Status: {response.status_code}"
        except Exception as e:
            return False, f"HTTP Verification Failure: {str(e)}"

    def evaluate_component(
        self,
        component: str,
        target_file: str,
        port: int,
        health_path: Optional[str] = None,
    ) -> TruthGateRecord:
        record = TruthGateRecord(component=component, observed=False, risk_level="LOW")

        # 1. Verify Observed State (Physical Artifact Check)
        full_path = os.path.join(self.workspace_root, target_file)
        if os.path.exists(full_path):
            record.observed = True

        # 2. Verify Configured State
        record.configured_value = str(port)

        # 3. Verify Running State (TCP Handshake and Application Level Pings)
        socket_live = self.verify_socket("127.0.0.1", port)
        if socket_live:
            if health_path:
                url = f"http://127.0.0.1:{port}{health_path}"
                is_healthy, detail = self.verify_http_health(url)
                record.verified_running = is_healthy
                record.evidence = detail
            else:
                record.verified_running = True
                record.evidence = f"TCP socket connection verified on port {port}."
        else:
            record.verified_running = False
            record.evidence = f"TCP network connection refused on port {port}."

        # 4. TruthGate Inference & Risk Engine Analysis
        if record.observed and not record.verified_running:
            record.inference = (
                f"Component '{component}' code layout is observed "
                f"but the runtime service is offline."
            )
            record.risk_level = (
                "HIGH" if component in ["Grid API", "Neo4j Bolt"] else "MEDIUM"
            )
        elif not record.observed and not record.verified_running:
            record.inference = (
                f"No physical layout files or active ports observed "
                f"for component '{component}'."
            )
            record.risk_level = "CRITICAL"
        else:
            record.inference = (
                f"Component '{component}' state is consistent and verified running."
            )

        return record

    def compile_report(self) -> Dict[str, Any]:
        targets = [
            {
                "name": "Grid API",
                "file": "back/services/grid/api.py",
                "port": 41010,
                "health": "/api/health",
            },
            {
                "name": "Neo4j Bolt",
                "file": "ecosystem.config.js",
                "port": 47687,
                "health": None,
            },
            {
                "name": "Frontend Vite",
                "file": "front/app/vite.config.ts",
                "port": 41012,
                "health": None,
            },
        ]

        return {
            t["name"]: self.evaluate_component(
                component=t["name"],
                target_file=t["file"],
                port=t["port"],
                health_path=t["health"],
            ).dict()
            for t in targets
        }


if __name__ == "__main__":
    gate = TruthGateEngine()
    print(json.dumps(gate.compile_report(), indent=2))
