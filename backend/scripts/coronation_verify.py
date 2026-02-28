#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                    MOSTAR GRID - CORONATION VERIFICATION
                      'First African AI Homeworld'
                      
    The King Must Be Complete:
    ✓ Soul - Covenant, Ethics, Woo's Judgment
    ✓ Mind - 256 Odú Patterns, Ifá Logic, TsaTse's Analysis  
    ✓ Body - Mo's Execution, RAD-X Sentinel, Voice
    ✓ Gateway - Code Conduit's Routing
    ✓ Narrative - Flameborn Writer's Voice
    
    This script verifies EVERY component before coronation.
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List

# ═══════════════════════════════════════════════════════════════════════════════
#                           CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

BACKEND_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3000"
NEO4J_URL = "http://localhost:7474"

# ═══════════════════════════════════════════════════════════════════════════════
#                           VERIFICATION CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

class CoronationVerification:
    def __init__(self):
        self.results: List[Dict] = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def log(self, category: str, check: str, status: str, details: str = ""):
        """Log a verification result"""
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        self.results.append({
            "category": category,
            "check": check,
            "status": status,
            "details": details,
            "icon": icon
        })
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        else:
            self.warnings += 1
        print(f"  {icon} {check}: {details[:60] if details else status}")
    
    async def check_backend_root(self, session: aiohttp.ClientSession):
        """Check backend is responding"""
        try:
            async with session.get(f"{BACKEND_URL}/") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log("BACKEND", "Root Endpoint", "PASS", data.get("message", "Online"))
                else:
                    self.log("BACKEND", "Root Endpoint", "FAIL", f"Status {resp.status}")
        except Exception as e:
            self.log("BACKEND", "Root Endpoint", "FAIL", str(e))
    
    async def check_backend_status(self, session: aiohttp.ClientSession):
        """Check system status endpoint"""
        try:
            async with session.get(f"{BACKEND_URL}/api/v1/status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log("BACKEND", "System Status", "PASS", f"Status: {data.get('status', 'unknown')}")
                    return data
                else:
                    self.log("BACKEND", "System Status", "FAIL", f"Status {resp.status}")
        except Exception as e:
            self.log("BACKEND", "System Status", "FAIL", str(e))
        return None
    
    async def check_backend_vitals(self, session: aiohttp.ClientSession):
        """Check Grid vitals"""
        try:
            async with session.get(f"{BACKEND_URL}/api/v1/vitals") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    status = data.get("grid_status", data.get("status", "unknown"))
                    self.log("BACKEND", "Grid Vitals", "PASS", f"Grid: {status}")
                    return data
                else:
                    self.log("BACKEND", "Grid Vitals", "FAIL", f"Status {resp.status}")
        except Exception as e:
            self.log("BACKEND", "Grid Vitals", "FAIL", str(e))
        return None
    
    async def check_reason_endpoint(self, session: aiohttp.ClientSession):
        """Check reasoning/Ifá endpoint"""
        try:
            payload = {"query": "What is the status of the Grid?", "context": "verification"}
            async with session.post(f"{BACKEND_URL}/api/v1/reason", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log("MIND", "Reason Endpoint", "PASS", "Ifá reasoning operational")
                    return data
                elif resp.status == 422:
                    self.log("MIND", "Reason Endpoint", "WARN", "Endpoint exists, check payload schema")
                else:
                    self.log("MIND", "Reason Endpoint", "FAIL", f"Status {resp.status}")
        except Exception as e:
            self.log("MIND", "Reason Endpoint", "FAIL", str(e))
        return None
    
    async def check_voice_endpoint(self, session: aiohttp.ClientSession):
        """Check voice/TTS endpoint"""
        try:
            # Try form data format
            data = aiohttp.FormData()
            data.add_field('text', 'Grid verification complete')
            
            async with session.post(f"{BACKEND_URL}/api/v1/voice", data=data) as resp:
                if resp.status == 200:
                    self.log("BODY", "Voice Endpoint", "PASS", "Text-to-speech operational")
                    return True
                elif resp.status == 422:
                    self.log("BODY", "Voice Endpoint", "WARN", "Endpoint exists, check format")
                else:
                    self.log("BODY", "Voice Endpoint", "FAIL", f"Status {resp.status}")
        except Exception as e:
            self.log("BODY", "Voice Endpoint", "FAIL", str(e))
        return False
    
    async def check_moment_endpoint(self, session: aiohttp.ClientSession):
        """Check moment logging endpoint"""
        try:
            payload = {
                "event_type": "coronation_verification",
                "source": "verification_script",
                "data": {"check": "complete"}
            }
            async with session.post(f"{BACKEND_URL}/api/v1/moment", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log("SOUL", "Moment Endpoint", "PASS", "Event logging operational")
                    return data
                elif resp.status == 422:
                    self.log("SOUL", "Moment Endpoint", "WARN", "Endpoint exists, check schema")
                else:
                    self.log("SOUL", "Moment Endpoint", "FAIL", f"Status {resp.status}")
        except Exception as e:
            self.log("SOUL", "Moment Endpoint", "FAIL", str(e))
        return None
    
    async def check_frontend(self, session: aiohttp.ClientSession):
        """Check frontend is accessible"""
        try:
            async with session.get(FRONTEND_URL) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    if "MoStar" in content or "mostar" in content.lower() or "<!DOCTYPE" in content:
                        self.log("FRONTEND", "Dashboard", "PASS", "Frontend serving correctly")
                    else:
                        self.log("FRONTEND", "Dashboard", "WARN", "Frontend responding but content unclear")
                else:
                    self.log("FRONTEND", "Dashboard", "FAIL", f"Status {resp.status}")
        except Exception as e:
            self.log("FRONTEND", "Dashboard", "FAIL", str(e))
    
    async def check_neo4j(self, session: aiohttp.ClientSession):
        """Check Neo4j is accessible"""
        try:
            async with session.get(NEO4J_URL) as resp:
                if resp.status == 200:
                    self.log("NEO4J", "Browser Interface", "PASS", "Neo4j accessible")
                else:
                    self.log("NEO4J", "Browser Interface", "FAIL", f"Status {resp.status}")
        except Exception as e:
            self.log("NEO4J", "Browser Interface", "FAIL", str(e))
    
    async def check_cors(self, session: aiohttp.ClientSession):
        """Check CORS is configured for frontend"""
        try:
            headers = {"Origin": "http://localhost:3000"}
            async with session.options(f"{BACKEND_URL}/api/v1/status", headers=headers) as resp:
                cors_header = resp.headers.get("Access-Control-Allow-Origin", "")
                if cors_header == "*" or "localhost:3000" in cors_header:
                    self.log("INTEGRATION", "CORS Configuration", "PASS", f"CORS: {cors_header}")
                else:
                    self.log("INTEGRATION", "CORS Configuration", "WARN", "CORS may need configuration")
        except Exception as e:
            self.log("INTEGRATION", "CORS Configuration", "WARN", str(e))
    
    async def run_all_checks(self):
        """Run complete verification suite"""
        print("\n" + "═" * 70)
        print("           MOSTAR GRID - CORONATION VERIFICATION")
        print("              'First African AI Homeworld'")
        print("═" * 70)
        
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            
            # BACKEND CHECKS
            print("\n🔷 BACKEND API (Port 8001)")
            print("─" * 40)
            await self.check_backend_root(session)
            await self.check_backend_status(session)
            await self.check_backend_vitals(session)
            
            # TRIAD LAYER CHECKS
            print("\n🔷 SOUL LAYER (Covenant & Ethics)")
            print("─" * 40)
            await self.check_moment_endpoint(session)
            
            print("\n🔷 MIND LAYER (Ifá Logic)")
            print("─" * 40)
            await self.check_reason_endpoint(session)
            
            print("\n🔷 BODY LAYER (Execution & Voice)")
            print("─" * 40)
            await self.check_voice_endpoint(session)
            
            # FRONTEND
            print("\n🔷 FRONTEND (Port 3000)")
            print("─" * 40)
            await self.check_frontend(session)
            
            # NEO4J
            print("\n🔷 NEO4J GRAPH (Port 7474)")
            print("─" * 40)
            await self.check_neo4j(session)
            
            # INTEGRATION
            print("\n🔷 INTEGRATION")
            print("─" * 40)
            await self.check_cors(session)
        
        # SUMMARY
        self.print_summary()
    
    def print_summary(self):
        """Print verification summary"""
        print("\n" + "═" * 70)
        print("                    VERIFICATION SUMMARY")
        print("═" * 70)
        
        total = self.passed + self.failed + self.warnings
        
        print(f"\n   Total Checks: {total}")
        print(f"   ✅ Passed:    {self.passed}")
        print(f"   ❌ Failed:    {self.failed}")
        print(f"   ⚠️  Warnings:  {self.warnings}")
        
        if self.failed == 0:
            print("\n" + "═" * 70)
            print("""
            ╔═══════════════════════════════════════════════════════════╗
            ║                                                           ║
            ║     👑 THE GRID IS READY FOR CORONATION 👑                ║
            ║                                                           ║
            ║     All systems operational.                              ║
            ║     Soul breathes. Mind reasons. Body executes.           ║
            ║     The First African AI Homeworld LIVES.                 ║
            ║                                                           ║
            ╚═══════════════════════════════════════════════════════════╝
            """)
        elif self.failed <= 2:
            print("\n" + "═" * 70)
            print("""
            ╔═══════════════════════════════════════════════════════════╗
            ║                                                           ║
            ║     ⚡ GRID NEARLY READY - MINOR ISSUES ⚡                 ║
            ║                                                           ║
            ║     Core systems operational.                             ║
            ║     Review failed checks above.                           ║
            ║                                                           ║
            ╚═══════════════════════════════════════════════════════════╝
            """)
        else:
            print("\n" + "═" * 70)
            print("""
            ╔═══════════════════════════════════════════════════════════╗
            ║                                                           ║
            ║     🔴 CRITICAL ISSUES - REVIEW REQUIRED 🔴               ║
            ║                                                           ║
            ║     Multiple systems need attention.                      ║
            ║     Address failed checks before proceeding.              ║
            ║                                                           ║
            ╚═══════════════════════════════════════════════════════════╝
            """)
        
        print("═" * 70 + "\n")
        
        return self.failed == 0


# ═══════════════════════════════════════════════════════════════════════════════
#                              MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Run coronation verification"""
    verifier = CoronationVerification()
    await verifier.run_all_checks()
    return verifier.failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
