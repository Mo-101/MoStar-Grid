"""
═══════════════════════════════════════════════════════════════════════════════
Register Neo4j Aura Fleet Management Token
A MoStar Industries Product
═══════════════════════════════════════════════════════════════════════════════

This script registers the Neo4j Aura Fleet Management token to enable
cloud management capabilities.

License: African Sovereignty License (ASL) v1.0
Copyright © 2026 MoStar Industries
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# The token from Neo4j Aura
FLEET_TOKEN = "eyJraWQiOiJjYjNiY2ZkMS1iZjdkLTRkM2EtODlkNS1iYjZhYmVhZDRiZDkiLCJwcml2YXRlX2tleSI6Ik1JR0hBZ0VBTUJNR0J5cUdTTTQ5QWdFR0NDcUdTTTQ5QXdFSEJHMHdhd0lCQVFRZzN3WDVzVThYdmJYYTZDMmgwbXJhWitxT2xuNUQxVEZmMHZjRjV5L0hvMzJoUkFOQ0FBVFZrTU9QVmtJNGlWVlR5ZUFhZ2VXLzU0TURGVU5INFpSdlZUQWo0S2tHdzJTdXA2UExnbWZOcUg2TVIrWExBMkVYemFTUHY4T3JnUDZieFBTMGdoV2giLCJwcm9qZWN0X2lkIjoiNGNkOGE4ZjYtYTU0ZC00MjQxLWE3ZTQtMWVmMzJjN2U4Njg3IiwiZXhwaXJ5X3RpbWUiOiIyMDI3LTAxLTMwVDE2OjAzOjUwLjIzMzQ0Nzg2M1oifQ=="

def register_fleet_token():
    """Register the Neo4j Aura Fleet Management token."""
    
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'neo4j')
    
    print("=" * 80)
    print("MoStar Grid - Registering Neo4j Aura Fleet Token")
    print("=" * 80)
    print(f"\nConnecting to: {uri}")
    print(f"User: {user}")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session(database="system") as session:
            print("\n✓ Connected to Neo4j")
            print("✓ Switched to system database")
            print("\nRegistering fleet management token...")
            
            # Register the token
            result = session.run(
                "CALL fleetManagement.registerToken($token)",
                token=FLEET_TOKEN
            )
            
            record = result.single()
            
            print("\n✅ SUCCESS! Fleet management token registered.")
            print(f"\nResult: {record}")
            print("\n" + "=" * 80)
            print("Neo4j Aura Fleet Management is now enabled for MoStar Grid")
            print("Token expires: 2027-01-30T16:03:50Z")
            print("=" * 80)
        
        driver.close()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Neo4j is running (docker ps)")
        print("2. Check connection settings in .env")
        print("3. Verify you have admin privileges")
        print("4. Confirm Neo4j version supports Fleet Management")

if __name__ == "__main__":
    register_fleet_token()
