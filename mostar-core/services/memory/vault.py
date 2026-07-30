import hashlib
from typing import Dict, Optional
from core.fgrid.models import Entity, Relationship
from core.fgrid.graph import fgrid_graph

class VaultMemory:
    """Manages encrypted metadata, secure system configuration, and audit records."""
    
    def __init__(self):
        # Local mock storage for actual secrets, keeping them out of plaintext graph properties
        self._secure_vault: Dict[str, str] = {}

    def store_secure_config(self, key: str, value: str) -> None:
        """Stores actual secret in private dict and a cryptographic hash in FGrid for auditing."""
        self._secure_vault[key] = value
        
        # Calculate secure hash
        val_hash = hashlib.sha256(value.encode('utf-8')).hexdigest()
        
        vault_entity = Entity(
            id=f"vault.{key}",
            type="VaultCredential",
            title=f"Secure Configuration: {key}",
            owner="System",
            tags=["Vault", "Security"],
            metadata={
                "value_sha256": val_hash,
                "status": "Secured"
            }
        )
        fgrid_graph.add_entity(vault_entity)

        # Link to MoStar
        fgrid_graph.add_relationship(Relationship(
            source_id="mostar.ai",
            target_id=f"vault.{key}",
            relation_type="secures"
        ))

    def get_secure_config(self, key: str) -> Optional[str]:
        return self._secure_vault.get(key)
