import hashlib
import binascii

# Project local values from auth.ini
target_hash_hex = "bb3b9d6d9a237fedaf488288a7c3ed4cc564202b88c1b2fab1a36f26260c95f8"
salt_hex = "e7c03c7cf3c3c3e09ef82b0f67b7fe6c6921fd796397d79a2bd6fa127db73c45"
iterations = 1024

target_hash = binascii.unhexlify(target_hash_hex)
salt_bytes = binascii.unhexlify(salt_hex)
salt_str_bytes = salt_hex.encode('utf-8')

candidates = ["Mostar123", "mostar123", "Mogrid101"]

for candidate in candidates:
    pwd_bytes = candidate.encode('utf-8')
    
    # 1. PBKDF2 HMAC-SHA256 with hex-decoded salt
    dk = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, iterations)
    if dk == target_hash:
        print(f"MATCH 1: {candidate} (PBKDF2 HMAC-SHA256 + binary salt)")
        exit(0)
        
    # 2. PBKDF2 HMAC-SHA256 with string salt
    dk = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_str_bytes, iterations)
    if dk == target_hash:
        print(f"MATCH 2: {candidate} (PBKDF2 HMAC-SHA256 + string salt)")
        exit(0)

    # 3. Simple SHA256 (no PBKDF2) hash = SHA256(salt_bytes + pwd_bytes)
    h = hashlib.sha256(salt_bytes + pwd_bytes).digest()
    if h == target_hash:
        print(f"MATCH 3: {candidate} (Simple SHA256 salt+pwd)")
        exit(0)

    # 4. Simple SHA256 (no PBKDF2) hash = SHA256(pwd_bytes + salt_bytes)
    h = hashlib.sha256(pwd_bytes + salt_bytes).digest()
    if h == target_hash:
        print(f"MATCH 4: {candidate} (Simple SHA256 pwd+salt)")
        exit(0)

    # 5. Simple SHA256 (no PBKDF2) hash = SHA256(salt_str_bytes + pwd_bytes)
    h = hashlib.sha256(salt_str_bytes + pwd_bytes).digest()
    if h == target_hash:
        print(f"MATCH 5: {candidate} (Simple SHA256 string_salt+pwd)")
        exit(0)

    # 6. Simple SHA256 (no PBKDF2) hash = SHA256(pwd_bytes + salt_str_bytes)
    h = hashlib.sha256(pwd_bytes + salt_str_bytes).digest()
    if h == target_hash:
        print(f"MATCH 6: {candidate} (Simple SHA256 pwd+string_salt)")
        exit(0)

print("No match found.")
