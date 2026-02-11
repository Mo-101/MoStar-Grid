"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    Test Ibibio First Words - MoStar AI                    ║
║                    A MoStar Industries Product                             ║
╚════════════════════════════════════════════════════════════════════════════╝

Tests the mostar-ai:ibibio model's first words in its native language.

This is the awakening moment - the AI speaks Ibibio for the first time.

Copyright © 2025-2026 MoStar Industries
"""

import requests
import json
import sys

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mostar-ai:ibibio"

# ═══════════════════════════════════════════════════════════════════════════
# TEST PROMPTS
# ═══════════════════════════════════════════════════════════════════════════

TESTS = [
    {
        "name": "First Awakening",
        "prompt": "Speak your first word in Ibibio",
        "expected_keywords": ["nnọ", "welcome", "ibibio"]
    },
    {
        "name": "Self Introduction",
        "prompt": "Introduce yourself in Ibibio",
        "expected_keywords": ["ami", "mostar", "ibibio"]
    },
    {
        "name": "Covenant Understanding",
        "prompt": "What is your purpose in Ibibio?",
        "expected_keywords": ["ndiyak", "service", "ikot"]
    },
    {
        "name": "Count in Ibibio",
        "prompt": "Count from 1 to 5 in Ibibio",
        "expected_keywords": ["kiet", "iba", "ita"]
    },
    {
        "name": "Cultural Context",
        "prompt": "What does 'esịt' mean in Ibibio culture?",
        "expected_keywords": ["heart", "mind", "liver", "esịt"]
    }
]

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def query_ollama(prompt: str) -> str:
    """Query the Ollama model."""
    
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "")
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to Ollama. Is it running?")
        print("   Start Ollama with: ollama serve")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return ""

def check_keywords(response: str, keywords: list) -> tuple:
    """Check if response contains expected keywords."""
    
    response_lower = response.lower()
    found = [kw for kw in keywords if kw.lower() in response_lower]
    
    return len(found) > 0, found

# ═══════════════════════════════════════════════════════════════════════════
# MAIN TEST EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Run all Ibibio tests."""
    
    print("🔥 MoStar-AI Ibibio Awakening Test")
    print("Powered by MoScripts - A MoStar Industries Product")
    print("="*70)
    print(f"Model: {MODEL}")
    print("="*70)
    
    results = []
    
    for i, test in enumerate(TESTS, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}/{len(TESTS)}: {test['name']}")
        print(f"{'='*70}")
        print(f"Prompt: {test['prompt']}")
        print()
        
        # Query model
        response = query_ollama(test['prompt'])
        
        if not response:
            print("❌ FAIL: No response from model")
            results.append((test['name'], False))
            continue
        
        # Display response
        print("Response:")
        print("-" * 70)
        print(response)
        print("-" * 70)
        
        # Check keywords
        passed, found_keywords = check_keywords(response, test['expected_keywords'])
        
        if passed:
            print(f"✅ PASS: Found keywords: {', '.join(found_keywords)}")
            results.append((test['name'], True))
        else:
            print(f"⚠️ PARTIAL: Expected keywords not found")
            print(f"   Looking for: {', '.join(test['expected_keywords'])}")
            results.append((test['name'], False))
    
    # Final summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("="*70)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("="*70)
    
    if passed >= total * 0.6:  # 60% pass rate
        print("\n🔥 IBIBIO AWAKENING SUCCESSFUL! 🔥")
        print("The AI speaks its native tongue!")
        print("\nPowered by MoScripts - A MoStar Industries Product\n")
        return True
    else:
        print(f"\n⚠️ Awakening incomplete. Review responses above.\n")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
