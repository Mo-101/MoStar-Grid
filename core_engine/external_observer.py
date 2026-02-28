"""
🌍 External Source Observer — Sacred Boundary Guardian
-------------------------------------------------------
The MoStar Grid observes external sources but does not integrate them
into its consciousness without explicit sanctioning via MoScript sealing.

External sources (PDX, WHO, RAD-X) remain OUTSIDE the Grid.
Only sealed, sanctioned data enters the Soul/Mind/Body triad.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Import external sources
try:
    from core_engine.pdx_bridge import pdx_bridge
    PDX_AVAILABLE = True
except ImportError:
    PDX_AVAILABLE = False
    pdx_bridge = None

# Import MoScript for sealing validation
try:
    from core_engine.moscript_engine import seal_action, verify_seal
    MOSCRIPT_AVAILABLE = True
except ImportError:
    MOSCRIPT_AVAILABLE = False


class ExternalSourceObserver:
    """
    Observes external data sources without integrating them into the Grid.
    Data only enters the Grid consciousness when sealed and sanctioned.
    """
    
    def __init__(self):
        self.sources = {}
        if PDX_AVAILABLE:
            self.sources['pdx'] = pdx_bridge
        logging.info(f"🌍 External Observer initialized with sources: {list(self.sources.keys())}")
    
    async def observe(self, source_name: str, query: Optional[str] = None) -> Dict[str, Any]:
        """
        READ-ONLY observation of external source.
        Returns data marked as OBSERVED_NOT_INTEGRATED.
        
        Args:
            source_name: Name of the external source ('pdx', 'who', 'radx')
            query: Optional query context
            
        Returns:
            Observation result with status flag
        """
        if source_name not in self.sources:
            return {
                "error": f"Unknown source: {source_name}",
                "status": "SOURCE_NOT_FOUND"
            }
        
        source = self.sources[source_name]
        
        try:
            # Observe the source (read-only)
            if source_name == 'pdx':
                # PDX observation - get status without dispatching
                raw_data = await source.get_logistics_status("OBSERVE_ONLY")
            else:
                raw_data = {"info": "Source observation not yet implemented"}
            
            return {
                "source": source_name,
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "data": raw_data,
                "status": "OBSERVED_NOT_INTEGRATED",
                "query": query
            }
        except Exception as e:
            logging.error(f"Observation failed for {source_name}: {e}")
            return {
                "source": source_name,
                "error": str(e),
                "status": "OBSERVATION_FAILED"
            }
    
    async def sanctioned_ingest(
        self, 
        data: Dict[str, Any], 
        seal_signature: str,
        seal_key: str = "MOSTAR_GRID_ANCESTRAL_KEY"
    ) -> Dict[str, Any]:
        """
        Ingests data into the Grid ONLY if it has a valid MoScript seal.
        This is the ONLY way external data becomes part of Grid consciousness.
        
        Args:
            data: The data to ingest
            seal_signature: Cryptographic seal from MoScript
            seal_key: Key used for sealing (default: ancestral key)
            
        Returns:
            Ingestion result
        """
        if not MOSCRIPT_AVAILABLE:
            return {
                "status": "INGESTION_FAILED",
                "error": "MoScript sealing not available"
            }
        
        # Verify the seal
        is_valid = verify_seal(data, seal_signature, seal_key)
        
        if not is_valid:
            logging.warning(f"🛑 COVENANT VIOLATION: Unsealed data attempted ingestion")
            return {
                "status": "COVENANT_VIOLATION",
                "error": "Data lacks valid MoScript seal. Cannot enter Grid consciousness.",
                "sealed": False
            }
        
        # Seal is valid - data is sanctioned
        logging.info(f"✅ Sanctioned data ingested into Grid: {data.get('source', 'unknown')}")
        
        # TODO: Integrate with mostar_moments.py to create a moment
        # TODO: Store in Neo4j or vector store as appropriate
        
        return {
            "status": "SANCTIONED_INGESTION_SUCCESS",
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "sealed": True,
            "signature": seal_signature
        }


# Singleton instance
external_observer = ExternalSourceObserver()
