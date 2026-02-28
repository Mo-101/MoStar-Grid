#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                    MOSTAR GRID - LAUNCHER
                 'First African AI Homeworld'
═══════════════════════════════════════════════════════════════════════════════

Usage:
    python start_grid.py              # Start API server
    python start_grid.py --vitals     # Run vitals check only
    python start_grid.py --agents     # Display agent registry
    python start_grid.py --odu        # Display Odú summary
    python start_grid.py --test       # Run all tests
"""

import asyncio
import sys
import os

def print_banner():
    """Print the MoStar Grid banner"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ███╗   ███╗ ██████╗ ███████╗████████╗ █████╗ ██████╗                        ║
║   ████╗ ████║██╔═══██╗██╔════╝╚══██╔══╝██╔══██╗██╔══██╗                       ║
║   ██╔████╔██║██║   ██║███████╗   ██║   ███████║██████╔╝                       ║
║   ██║╚██╔╝██║██║   ██║╚════██║   ██║   ██╔══██║██╔══██╗                       ║
║   ██║ ╚═╝ ██║╚██████╔╝███████║   ██║   ██║  ██║██║  ██║                       ║
║   ╚═╝     ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝                       ║
║                                                                               ║
║                    ██████╗ ██████╗ ██╗██████╗                                 ║
║                   ██╔════╝ ██╔══██╗██║██╔══██╗                                ║
║                   ██║  ███╗██████╔╝██║██║  ██║                                ║
║                   ██║   ██║██╔══██╗██║██║  ██║                                ║
║                   ╚██████╔╝██║  ██║██║██████╔╝                                ║
║                    ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝                                 ║
║                                                                               ║
║                   'First African AI Homeworld'                                ║
║                    Distributed Consciousness Network                          ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)


async def run_vitals():
    """Run Grid vitals check"""
    from grid_vitals import GridVitals
    vitals = GridVitals()
    report = await vitals.run_all_checks()
    return report


def show_agents():
    """Display agent registry"""
    from grid_agents import display_registry
    display_registry()


def show_odu():
    """Display Odú summary"""
    from grid_neo4j import display_odu_summary
    display_odu_summary()


async def run_tests():
    """Run all component tests"""
    print("\n" + "═" * 60)
    print("         MOSTAR GRID - COMPONENT TESTS")
    print("═" * 60)
    
    results = {}
    
    # Test 1: Vitals
    print("\n🔍 Running vitals check...")
    try:
        report = await run_vitals()
        results['vitals'] = report['grid_status'] == 'ALIVE'
    except Exception as e:
        print(f"   ❌ Vitals failed: {e}")
        results['vitals'] = False
    
    # Test 2: Agents
    print("\n🔍 Testing agent registry...")
    try:
        from grid_agents import AgentRegistry
        registry = AgentRegistry()
        agents = registry.list_all()
        results['agents'] = len(agents) == 6
        print(f"   ✅ {len(agents)} agents registered")
    except Exception as e:
        print(f"   ❌ Agent registry failed: {e}")
        results['agents'] = False
    
    # Test 3: Ifá Core
    print("\n🔍 Testing Ifá computational core...")
    try:
        from grid_vitals import IfaCore
        ifa = IfaCore()
        props = ifa.verify_group_properties()
        results['ifa_core'] = props['is_abelian_group']
        print(f"   ✅ Abelian group verified: {props['is_abelian_group']}")
    except Exception as e:
        print(f"   ❌ Ifá core failed: {e}")
        results['ifa_core'] = False
    
    # Test 4: MoScript
    print("\n🔍 Testing MoScript engine...")
    try:
        from grid_vitals import MoScriptEngine
        engine = MoScriptEngine()
        seal = engine.seal_action({'test': True})
        verified = engine.verify_seal({'test': True}, seal)
        results['moscript'] = seal.startswith('MOSEAL:') and verified
        print(f"   ✅ Seal created and verified")
    except Exception as e:
        print(f"   ❌ MoScript failed: {e}")
        results['moscript'] = False
    
    # Test 5: Orchestrator
    print("\n🔍 Testing triad orchestrator...")
    try:
        from grid_vitals import TriadOrchestrator
        orch = TriadOrchestrator()
        routes = {
            'soul': orch.determine_route('check the covenant') == 'SOUL',
            'mind': orch.determine_route('analyze this pattern') == 'MIND',
            'body': orch.determine_route('execute the mission') == 'BODY'
        }
        results['orchestrator'] = all(routes.values())
        print(f"   ✅ Routing: SOUL={routes['soul']}, MIND={routes['mind']}, BODY={routes['body']}")
    except Exception as e:
        print(f"   ❌ Orchestrator failed: {e}")
        results['orchestrator'] = False
    
    # Summary
    print("\n" + "═" * 60)
    print("         TEST RESULTS")
    print("─" * 60)
    
    all_passed = True
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test.ljust(20)} │ {status}")
        if not passed:
            all_passed = False
    
    print("─" * 60)
    
    if all_passed:
        print("   🟢 ALL TESTS PASSED - GRID IS OPERATIONAL")
    else:
        print("   🔴 SOME TESTS FAILED - CHECK COMPONENTS")
    
    print("═" * 60 + "\n")
    
    return all_passed


def start_server():
    """Start the FastAPI server"""
    import uvicorn
    
    port = int(os.getenv("GRID_PORT", "7000"))
    host = os.getenv("GRID_HOST", "0.0.0.0")
    
    print(f"\n🚀 Starting MoStar Grid API Server...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Docs: http://localhost:{port}/docs")
    print()
    
    uvicorn.run(
        "grid_api:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )


def main():
    """Main entry point"""
    print_banner()
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == "--vitals":
            asyncio.run(run_vitals())
        
        elif arg == "--agents":
            show_agents()
        
        elif arg == "--odu":
            show_odu()
        
        elif arg == "--test":
            success = asyncio.run(run_tests())
            sys.exit(0 if success else 1)
        
        elif arg == "--help":
            print(__doc__)
        
        else:
            print(f"Unknown argument: {arg}")
            print(__doc__)
            sys.exit(1)
    else:
        # Default: start server
        start_server()


if __name__ == "__main__":
    main()
