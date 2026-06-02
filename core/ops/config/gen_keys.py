import json
import os
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

def generate_keypair(cluster_name, filename):
    key = ed25519.Ed25519PrivateKey.generate()
    privkey_bytes = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    pubkey_bytes = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    data = {
        "cluster_id": cluster_name,
        "private_key": privkey_bytes.decode(),
        "public_key": pubkey_bytes.decode()
    }
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

os.makedirs("/home/idona/MoStar/_apps/grid/config", exist_ok=True)
generate_keypair("nairobi-alpha", "/home/idona/MoStar/_apps/grid/config/nairobi-alpha-keys.json")
generate_keypair("kampala-beta", "/home/idona/MoStar/_apps/grid/config/kampala-beta-keys.json")

print("Keys generated successfully.")
