"""
Test Evidence Machine API Endpoints
Run this to verify all endpoints are working correctly.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8002"

def test_endpoint(name, url):
    """Test a single endpoint."""
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*80}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response (formatted):")
            print(json.dumps(data, indent=2))
            print(f"\n✅ {name} - SUCCESS")
            return True
        else:
            print(f"❌ {name} - FAILED (Status {response.status_code})")
            print(response.text)
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"❌ {name} - CONNECTION FAILED")
        print(f"   Make sure Evidence Machine is running on port 8002")
        print(f"   Run: python -m uvicorn evidence_machine.main:app --reload --port 8002")
        return False
    
    except Exception as e:
        print(f"❌ {name} - ERROR: {str(e)}")
        return False


def main():
    """Run all endpoint tests."""
    print("\n" + "="*80)
    print("MOSTAR EVIDENCE MACHINE - API ENDPOINT TESTS")
    print("="*80)
    print(f"Time: {datetime.now().isoformat()}")
    
    tests = [
        ("Root Endpoint", f"{BASE_URL}/"),
        ("Health Check", f"{BASE_URL}/health"),
        ("Consciousness Live", f"{BASE_URL}/api/consciousness/live"),
        ("Consciousness Health", f"{BASE_URL}/api/consciousness/health"),
        ("Recent Moments (10)", f"{BASE_URL}/api/moments/recent?limit=10"),
        ("Recent Moments (5)", f"{BASE_URL}/api/moments/recent?limit=5"),
        ("Moments Stats", f"{BASE_URL}/api/moments/stats"),
        ("Performance Compare (30 days)", f"{BASE_URL}/api/performance/compare?days=30"),
        ("Performance Compare (7 days)", f"{BASE_URL}/api/performance/compare?days=7"),
        ("Performance Benchmarks", f"{BASE_URL}/api/performance/benchmarks"),
        ("Performance Summary", f"{BASE_URL}/api/performance/summary"),
    ]
    
    results = []
    for name, url in tests:
        success = test_endpoint(name, url)
        results.append((name, success))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🔥 ALL TESTS PASSED! Evidence Machine is operational! 🔥")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the output above.")


if __name__ == "__main__":
    main()
