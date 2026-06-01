import hashlib
import binascii

# System Neo4j hash/salt from /var/lib/neo4j/data/dbms/auth.ini
target_hash_hex = "613cdd4ce9bbc6b2433cff8c4b5331a6d39f12579aa9399654da6590ac05a723"
salt_hex = "3edd75f77e9fd34ec47c765c4a8c0d88f7822d35ecf55597785ec6e6fce51431"
iterations = 1024

target_hash = binascii.unhexlify(target_hash_hex)
salt = binascii.unhexlify(salt_hex)

candidates = [
    "<REDACTED>",
    "REDACTED",
    "redacted",
    "Mogrid101",
    "Mostar123",
    "mostar123",
    "Mogrid101!",
    "Mostar123!",
    "mostar123!",
    "Mogrid1012026",
    "Mogrid101_2026",
    "Mogrid_101",
    "mostar_grid",
    "mostar-grid",
    "flame",
    "Flame",
    "FlameArchitect",
    "Flame_Architect",
    "TheFlameArchitect",
    "theflamearchitect"
]

for candidate in candidates:
    # Test PBKDF2 HMAC-SHA256 with binary salt
    dk = hashlib.pbkdf2_hmac('sha256', candidate.encode('utf-8'), salt, iterations)
    if dk == target_hash:
        print(f"MATCH FOUND: Password is '{candidate}'")
        exit(0)

print("No match found in candidates.")
