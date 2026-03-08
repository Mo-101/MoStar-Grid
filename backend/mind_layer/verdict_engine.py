#!/usr/bin/env python3
"""
🧠 Mind Layer – Verdict Engine (Real Hybrid Reasoning)
Executes AHP, Grey relational analysis, and Ifá pattern matching.
All steps governed by MoScript and grounded in Neo4j data.
"""

import json
import logging
from core_engine.moscript_engine import MoScriptEngine
from core_engine.mostar_moments_log import log_mostar_moment

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('VerdictEngine')

class VerdictEngine:
    def __init__(self, engine: MoScriptEngine = None):
        self.mo = engine or MoScriptEngine()
        self.layer = "Mind Layer"

    async def _get_verdict_config(self) -> dict:
        """Fetch the current VerdictConfig weights using governed traversal."""
        cypher = """
            MATCH (c:VerdictConfig)
            RETURN c.grey_weight AS grey_weight, c.oracle_weight AS oracle_weight
            LIMIT 1
        """
        records = await self.mo.execute_governed_query(cypher, {}, "config_retrieval")
        if records and records[0].get("grey_weight") is not None:
            return {
                "grey_weight": float(records[0]["grey_weight"]),
                "oracle_weight": float(records[0]["oracle_weight"])
            }
        return {"grey_weight": 0.7, "oracle_weight": 0.3} # Default fallback

    async def compute_verdict(self, criteria: dict, truth_score: float = 1.0) -> dict:
        """
        Compute a verdict using AHP for weights, Grey for uncertainty,
        and Ifá binary patterns for symbolic resonance.
        Included reasoning integrity guard via truth_score.
        """
        if not criteria:
            return {"error": "No criteria provided", "status": "failed"}

        # --- REASONING INTEGRITY CHECK ---
        if truth_score < 0.35:
            logger.warning(f"Reasoning integrity failed: Truth Score {truth_score} < 0.35")
            return {
                "decision": "INSUFFICIENT_TRUTH",
                "confidence": truth_score,
                "scores": {}
            }

        # Step 1: AHP to get weights
        weights = await self._ahp_weights(criteria)

        # Step 2: Grey relational analysis for uncertainty
        grey_score = await self._grey_analysis(criteria, weights)

        # Step 3: Ifá pattern resonance (query Odu nodes)
        ifa_score = await self._ifa_resonance(criteria)

        # Step 4: Fetch configuration block for weighting
        config = await self._get_verdict_config()

        # Combine scores
        final_score = (config["grey_weight"] * grey_score) + (config["oracle_weight"] * ifa_score)

        decision = "Proceed" if final_score > 0.6 else "Review" if final_score > 0.4 else "Deny"
        confidence = final_score

        verdict = {
            "decision": decision,
            "confidence": confidence,
            "scores": {
                "ahp_weights": weights,
                "grey_score": grey_score,
                "ifa_score": ifa_score,
                "final_score": final_score
            },
            "config_applied": config
        }

        ritual = {
            "operation": "seal",
            "payload": {
                "layer": self.layer,
                "verdict": verdict,
                "status": "aligned" if final_score > 0.5 else "degraded"
            }
        }
        return await self.mo.interpret(ritual)

    async def _ahp_weights(self, criteria: dict) -> dict:
        """Compute AHP weights. Replace with matrix retrieval if added."""
        n = len(criteria)
        return {k: 1.0/n for k in criteria}

    async def _grey_analysis(self, criteria: dict, weights: dict) -> float:
        """
        Perform Grey Relational Analysis.
        Uses reference sequence (ideal) from Neo4j governed queries.
        """
        ref_values = {}
        for crit in criteria:
            cypher = """
                MATCH (m:MoStarMoment)
                WHERE toLower(m.description) CONTAINS toLower($crit)
                RETURN max(m.resonance_score) AS max_val
            """
            records = await self.mo.execute_governed_query(cypher, {"crit": crit}, "grey_reference")
            
            if records and records[0].get("max_val") is not None:
                ref_values[crit] = float(records[0]["max_val"])
            else:
                ref_values[crit] = 1.0

        scores = []
        for crit, val in criteria.items():
            ref = ref_values.get(crit, 1.0)
            diff = abs(ref - val) / (ref + 1e-6)
            coef = 1 / (1 + diff)
            scores.append(coef * weights[crit])

        return sum(scores) / len(scores) if scores else 0.5

    async def _ifa_resonance(self, criteria: dict) -> float:
        """
        Compute Ifá resonance: how well the criteria match Odu patterns.
        """
        cypher = """
            MATCH (o:OduIfa)
            RETURN o.name AS name, o.interpretation AS interpretation, o.binary_pattern AS binary_pattern
            ORDER BY rand() LIMIT 1
        """
        records = await self.mo.execute_governed_query(cypher, {}, "ifa_divination")
        
        if not records:
            return 0.5
            
        odu = records[0]
        interp = (odu.get("interpretation") or "").lower()
        keywords = " ".join(criteria.keys()).lower()
        match_count = sum(1 for word in keywords.split() if word in interp)
        
        return min(0.5 + match_count * 0.1, 1.0)

async def main():
    import asyncio
    ve = VerdictEngine()
    result = await ve.compute_verdict({"equity": 0.9, "wisdom": 0.8, "accuracy": 0.85}, truth_score=0.9)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
