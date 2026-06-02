import hashlib
import binascii

# System Neo4j hash/salt from /var/lib/neo4j/data/dbms/auth.ini
target_hash_hex = "613cdd4ce9bbc6b2433cff8c4b5331a6d39f12579aa9399654da6590ac05a723"
salt_hex = "3edd75f77e9fd34ec47c765c4a8c0d88f7822d35ecf55597785ec6e6fce51431"
iterations = 1024

target_hash = binascii.unhexlify(target_hash_hex)
salt = binascii.unhexlify(salt_hex)

candidates = [
    "Mogrid101",
    "Mogrid101\n",
    "Mogrid101\r\n",
    "Mogrid101 ",
    "mogrid101",
    "mogrid101\n",
    "mogrid101 ",
    "Mogrid101!",
    "mogrid101!",
    "Mogrid101\r",
    "mogrid101\r"
]

for candidate in candidates:
    pwd_bytes = candidate.encode('utf-8')
    h = hashlib.sha256(salt + pwd_bytes).digest()
    for _ in range(iterations - 1):
        h = hashlib.sha256(h).digest()
    if h == target_hash:
        print(f"MATCH FOUND: Password is '{candidate.encode('utf-8')}'")
        exit(0)

print("No match found in candidates.")
