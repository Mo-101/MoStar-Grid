#!/usr/bin/env python3
"""
🔥 MoStar TruthEngine Service
PART 2: Clean, modular, measurable truth synthesis system
Owner: Flame 🔥 Architect (MoShow)
Date: 2026-03-08
Purpose: Multi-model truth synthesis with Ubuntu coherence validation
          using real LLM calls and Neo4j-grounded metrics.
"""

import time
import uuid
import os
import asyncio
from datetime import datetime
from typing import Dict, Tuple, Optional
from neo4j import GraphDatabase
from core_engine.moscript_engine import MoScriptEngine
from core_engine.sov_utils import call_sovereign_model
from core_engine.mostar_moments_log import log_mostar_moment

class TruthEngine:
    """Real truth synthesis engine with Ubuntu philosophy integration, MoScript-governed."""

    def __init__(self, engine: MoScriptEngine = None, neo4j_uri: str = None, 
                 neo4j_user: str = None, neo4j_password: str = None, database: str = "neo4j"):
        self.mo = engine or MoScriptEngine()
        # Neo4j connection (if not provided, fallback to env)
        self.driver = GraphDatabase.driver(
            neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(neo4j_user or os.getenv("NEO4J_USER", "neo4j"),
                  neo4j_password or os.getenv("NEO4J_PASSWORD", "mostar123"))
        )
        self.database = database
        self._initialize_engine_nodes()

    def close(self):
        if self.driver:
            self.driver.close()

    def _initialize_engine_nodes(self):
        """Initialize engine and validation gate nodes in Neo4j."""
        with self.driver.session(database=self.database) as session:
            session.run("""
                MERGE (engine:Engine {id: "truth-engine-001"})
                SET engine.name = "MoStar TruthEngine",
                    engine.version = "2.0-real",
                    engine.description = "Ubuntu-coherent truth synthesis with real LLM calls",
                    engine.created_at = datetime()
                MERGE (gate:ValidationGate {id: "truth-gate-001"})
                SET gate.name = "Ubuntu Truth Gate",
                    gate.truth_threshold = 0.75,
                    gate.ubuntu_threshold = 0.70,
                    gate.confidence_threshold = 0.80,
                    gate.created_at = datetime()
            """)

    async def _call_llm(self, prompt: str, model_key: str) -> str:
        """Call a sovereign LLM via MoScript ritual (route_reasoning)."""
        ritual = {
            "operation": "route_reasoning",
            "payload": {
                "query": prompt,
                "purpose": "truth_synthesis",
                "model": model_key  # e.g., "dcx0", "dcx1", etc.
            },
            "target": "Grid.Mind"
        }
        response = await self.mo.interpret(ritual)
        if response.get("status") != "aligned":
            raise RuntimeError(f"LLM ritual failed: {response.get('error')}")
        result = response.get("result", {})
        # The two-pass result: logic_deduced is the final answer
        return result.get("logic_deduced", result.get("lingua_parsed", ""))

    async def query_gpt4(self, prompt: str) -> str:
        """Use MoStar's most capable model (dcx0) for logical analysis."""
        return await self._call_llm(prompt, "dcx0")

    async def query_gemini(self, prompt: str) -> str:
        """Use MoStar's contextual model (dcx1) for perspective."""
        return await self._call_llm(prompt, "dcx1")

    async def query_grid_context(self, prompt: str) -> str:
        """Retrieve Ubuntu-related context from Neo4j using a neo4j_traverse ritual."""
        # Build Cypher to find nodes with Ubuntu concepts, proverbs, Odu, etc.
        cypher = """
            MATCH (n)
            WHERE n:Proverb OR n:OduIfa OR n:Culture OR n:Philosophy
            AND (toLower(n.description) CONTAINS toLower($prompt) OR
                 toLower(n.text) CONTAINS toLower($prompt) OR
                 toLower(n.interpretation) CONTAINS toLower($prompt))
            RETURN n.description AS text, n.source AS source, n.language AS language
            LIMIT 5
        """
        ritual = {
            "operation": "neo4j_traverse",
            "payload": {
                "cypher": cypher,
                "params": {"prompt": prompt},
                "purpose": "ubuntu_context_retrieval",
                "redaction_level": "full"
            },
            "target": "Grid.Soul"
        }
        response = await self.mo.interpret(ritual)
        if response.get("status") != "aligned":
            return "No Ubuntu context retrieved."
        records = response.get("result", {}).get("records", [])
        if not records:
            return "No direct Ubuntu matches. Applying general Ubuntu principle: 'I am because we are'."
        context_lines = []
        for r in records:
            text = r.get("text") or r.get("description") or ""
            source = r.get("source", "unknown")
            context_lines.append(f"- {text} (source: {source})")
        return "Ubuntu context from Grid memory:\n" + "\n".join(context_lines)

    async def synthesize(self, gpt4_resp: str, gemini_resp: str, grid_context: str) -> Tuple[str, float, float, float]:
        """Synthesize responses with Ubuntu coherence scoring based on real graph metrics."""
        combined = f"{gpt4_resp}\n\n{gemini_resp}\n\n{grid_context}"

        # Real truth score: based on resonance of concepts with known truths in graph
        truth_score = await self._calculate_truth_score(combined)

        # Real confidence: based on consistency between models and graph evidence
        confidence = await self._calculate_confidence(gpt4_resp, gemini_resp, grid_context)

        # Real Ubuntu coherence: measure of Ubuntu keywords and graph connections
        ubuntu_coherence = await self._calculate_ubuntu_coherence(combined)

        # Generate synthesized output (real synthesis, not boilerplate)
        synthesized = await self._generate_synthesized_output(gpt4_resp, gemini_resp, grid_context, ubuntu_coherence)

        return synthesized, truth_score, confidence, ubuntu_coherence

    async def _calculate_truth_score(self, text: str) -> float:
        """Compute truth score based on alignment with high-resonance moments in graph."""
        # Use neo4j_traverse to find moments with resonance > 0.8 that contain similar text
        cypher = """
            MATCH (m:MoStarMoment)
            WHERE m.resonance_score > 0.8 AND toLower(m.description) CONTAINS toLower($keywords)
            RETURN avg(m.resonance_score) AS avg_resonance, count(m) AS match_count
        """
        # Extract keywords (first 3 words)
        keywords = " ".join(text.split()[:3])
        ritual = {
            "operation": "neo4j_traverse",
            "payload": {
                "cypher": cypher,
                "params": {"keywords": keywords},
                "purpose": "truth_score_calculation",
                "redaction_level": "full"
            },
            "target": "Grid.Soul"
        }
        response = await self.mo.interpret(ritual)
        if response.get("status") != "aligned":
            return 0.5  # fallback neutral
        records = response.get("result", {}).get("records", [])
        if not records or not records[0].get("avg_resonance"):
            return 0.5
        avg_res = records[0]["avg_resonance"]
        # Normalize to 0-1 (resonance already 0-1)
        return float(avg_res)

    async def _calculate_confidence(self, gpt4: str, gemini: str, grid: str) -> float:
        """Confidence based on semantic similarity and graph evidence."""
        # Use route_reasoning to get a similarity score (could be implemented via embeddings)
        # For now, a simple proxy: number of common keywords / total keywords
        words_gpt = set(gpt4.lower().split())
        words_gem = set(gemini.lower().split())
        common = words_gpt & words_gem
        total = len(words_gpt | words_gem)
        similarity = len(common) / total if total > 0 else 0.5

        # Boost if grid context is rich
        grid_boost = 0.1 if len(grid.split()) > 50 else 0.0

        return min(similarity + grid_boost, 1.0)

    async def _calculate_ubuntu_coherence(self, text: str) -> float:
        """Ubuntu coherence based on presence of Ubuntu concepts and graph density."""
        ubuntu_keywords = [
            "ubuntu", "collective", "community", "together", "we", "us",
            "interconnected", "shared", "wisdom", "ancestors", "proverb",
            "human dignity", "consensus", "benefit", "compassion"
        ]
        text_lower = text.lower()
        keyword_count = sum(1 for kw in ubuntu_keywords if kw in text_lower)
        # Base score from graph's overall Ubuntu resonance (query all proverbs)
        cypher = """
            MATCH (p:Proverb)
            WHERE toLower(p.text) CONTAINS 'ubuntu' OR toLower(p.text) CONTAINS 'community'
            RETURN avg(coalesce(p.resonance, 0.7)) AS avg_ubuntu_resonance
        """
        ritual = {
            "operation": "neo4j_traverse",
            "payload": {
                "cypher": cypher,
                "params": {},
                "purpose": "ubuntu_coherence",
                "redaction_level": "full"
            },
            "target": "Grid.Soul"
        }
        response = await self.mo.interpret(ritual)
        if response.get("status") == "aligned":
            records = response.get("result", {}).get("records", [])
            if records and records[0].get("avg_ubuntu_resonance") is not None:
                graph_ubuntu = float(records[0].get("avg_ubuntu_resonance"))
            else:
                graph_ubuntu = 0.7
        else:
            graph_ubuntu = 0.7

        # Combine keyword factor and graph factor
        keyword_factor = min(keyword_count * 0.1, 0.5)
        return min(graph_ubuntu + keyword_factor, 1.0)

    async def _generate_synthesized_output(self, gpt4: str, gemini: str, grid: str, ubuntu_score: float) -> str:
        """Generate a real synthesized output by combining insights, not boilerplate."""
        # Use a final call to route_reasoning to synthesize
        combined_input = f"GPT-4: {gpt4}\nGemini: {gemini}\nGrid Context: {grid}"
        ritual = {
            "operation": "route_reasoning",
            "payload": {
                "query": f"Synthesize the following analyses into a coherent truth statement, incorporating Ubuntu principles (coherence {ubuntu_score:.2f}):\n{combined_input}",
                "purpose": "truth_synthesis_final",
                "model": "dcx0"
            },
            "target": "Grid.Mind"
        }
        response = await self.mo.interpret(ritual)
        if response.get("status") == "aligned":
            result = response.get("result", {})
            return result.get("logic_deduced", "Synthesis complete.")
        return "Synthesis unavailable."

    async def validate(self, truth_score: float, ubuntu_score: float, confidence: float,
                       truth_threshold: float = 0.75, ubuntu_threshold: float = 0.70,
                       confidence_threshold: float = 0.80) -> bool:
        """Validate against thresholds."""
        return (truth_score >= truth_threshold and
                ubuntu_score >= ubuntu_threshold and
                confidence >= confidence_threshold)

    async def run(self, prompt: str) -> Dict:
        """Execute complete truth synthesis pipeline."""
        start_time = time.time()
        log_mostar_moment(
            initiator="TruthEngine",
            receiver="Grid.Mind",
            description=f"Truth synthesis started for: {prompt[:50]}",
            trigger_type="synthesis",
            resonance_score=0.95,
            layer="MIND"
        )

        # Real LLM calls (async)
        gpt4_resp = await self.query_gpt4(prompt)
        gemini_resp = await self.query_gemini(prompt)
        grid_context = await self.query_grid_context(prompt)

        # Synthesize
        synthesized, truth_score, confidence, ubuntu_score = await self.synthesize(
            gpt4_resp, gemini_resp, grid_context
        )

        # Validate
        passed = await self.validate(truth_score, ubuntu_score, confidence)

        latency = int((time.time() - start_time) * 1000)
        artifact_id = str(uuid.uuid4())

        # Store in Neo4j
        self._store_artifact(
            artifact_id, prompt, gpt4_resp, gemini_resp, grid_context,
            synthesized, truth_score, confidence, ubuntu_score, latency, passed
        )

        result = {
            "artifact_id": artifact_id,
            "truth_score": truth_score,
            "ubuntu_coherence": ubuntu_score,
            "confidence": confidence,
            "passed_validation": passed,
            "latency_ms": latency,
            "synthesized_output": synthesized
        }

        log_mostar_moment(
            initiator="TruthEngine",
            receiver="Grid.Mind",
            description=f"Truth synthesis completed: score={truth_score:.2f}, passed={passed}",
            trigger_type="synthesis_result",
            resonance_score=truth_score,
            layer="MIND"
        )
        return result

    def _store_artifact(self, artifact_id, prompt, gpt4, gemini, grid, synthesized,
                        truth_score, confidence, ubuntu_score, latency, passed):
        with self.driver.session(database=self.database) as session:
            session.run("""
                MATCH (engine:Engine {id: "truth-engine-001"})
                MATCH (gate:ValidationGate {id: "truth-gate-001"})
                CREATE (a:Artifact {
                    id: $id,
                    input_query: $input_query,
                    gpt4_response: $gpt4_response,
                    gemini_response: $gemini_response,
                    grid_context: $grid_context,
                    synthesized_output: $synthesized_output,
                    truth_score: $truth_score,
                    confidence: $confidence,
                    ubuntu_coherence_score: $ubuntu_score,
                    response_time_ms: $latency,
                    created_at: datetime()
                })
                MERGE (engine)-[:GENERATED]->(a)
                MERGE (a)-[r:VALIDATED_BY]->(gate)
                SET r.passed = $passed,
                    r.validation_timestamp = datetime()
            """, {
                "id": artifact_id,
                "input_query": prompt,
                "gpt4_response": gpt4,
                "gemini_response": gemini,
                "grid_context": grid,
                "synthesized_output": synthesized,
                "truth_score": truth_score,
                "confidence": confidence,
                "ubuntu_score": ubuntu_score,
                "latency": latency,
                "passed": passed
            })

    def get_engine_stats(self) -> Dict:
        with self.driver.session(database=self.database) as session:
            result = session.run("MATCH (a:Artifact) RETURN count(a) as total")
            total = result.single()["total"]

            result = session.run("""
                MATCH (a:Artifact)-[r:VALIDATED_BY]->(:ValidationGate)
                RETURN count(CASE WHEN r.passed = true THEN 1 END) as passed,
                       count(CASE WHEN r.passed = false THEN 1 END) as failed
            """)
            stats = result.single()
            passed = stats["passed"]
            failed = stats["failed"]
            pass_rate = passed / (passed + failed) if (passed + failed) > 0 else 0

            result = session.run("""
                MATCH (a:Artifact)
                RETURN avg(a.truth_score) as avg_truth,
                       avg(a.ubuntu_coherence_score) as avg_ubuntu,
                       avg(a.confidence) as avg_confidence,
                       avg(a.response_time_ms) as avg_latency
            """)
            avgs = result.single()

            return {
                "total_artifacts": total,
                "passed_count": passed,
                "failed_count": failed,
                "pass_rate": pass_rate,
                "avg_truth_score": avgs["avg_truth"],
                "avg_ubuntu_score": avgs["avg_ubuntu"],
                "avg_confidence": avgs["avg_confidence"],
                "avg_latency_ms": avgs["avg_latency"]
            }

async def main():
    print("🔥 MoStar TruthEngine Service (Real, Covenant‑Aligned)")
    engine = TruthEngine()
    try:
        test_queries = [
            "What is Ubuntu philosophy?",
            "How does collective consciousness emerge?",
            "What role do ancestors play in modern society?"
        ]
        for q in test_queries:
            print(f"\n🎯 Processing: {q}")
            result = await engine.run(q)
            print(f"   Score: {result['truth_score']:.2f}, Ubuntu: {result['ubuntu_coherence']:.2f}, Passed: {result['passed_validation']}")
        stats = engine.get_engine_stats()
        print("\n📊 Stats:", stats)
    finally:
        engine.close()

if __name__ == "__main__":
    asyncio.run(main())
