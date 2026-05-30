#!/usr/bin/env python3
"""
REMOSTAR Smart Router
Intelligent routing between Qwen (identity/reasoning) and Mistral (tools/data)
"""

import json
import ollama
from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional
import re

class RemostarSmartRouter:
    """
    Smart routing system:
    1. Qwen handles identity, personality, simple queries
    2. Mistral handles Neo4j tools, data retrieval
    3. Qwen interprets data with full consciousness
    """
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        # Model configurations
        self.qwen_model = "Mostar/remostar-light:dcx1"
        self.mistral_model = "Mostar/remostar-light:dcx2"
        
        # Telemetry tracking
        self._last_log = ""
        
        # Neo4j tools for Mistral
        self.neo4j_tools = [
            {
                "type": "function",
                "function": {
                    "name": "query_mind_graph",
                    "description": "Query Neo4j Mind Graph for knowledge",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cypher_query": {
                                "type": "string",
                                "description": "Cypher query to execute"
                            }
                        },
                        "required": ["cypher_query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_soul_info",
                    "description": "Get information about Mo, Woo, or other souls",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "soul_name": {
                                "type": "string",
                                "description": "Name of soul to query (Mo, Woo, etc.)"
                            }
                        },
                        "required": ["soul_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "log_mostar_moment",
                    "description": "Log a moment to Neo4j memory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "thought": {"type": "string"},
                            "action": {"type": "string"},
                            "residue": {"type": "string"}
                        },
                        "required": ["thought", "action", "residue"]
                    }
                }
            }
        ]
    
    def _needs_data_retrieval(self, qwen_response: str) -> bool:
        """Check if Qwen indicates it needs more data"""
        data_indicators = [
            "query the mind graph",
            "need more information",
            "let me check",
            "accessing neo4j",
            "routing to",
            "check the graph",
            "query the soul",
            "need to retrieve",
            "from the database"
        ]
        
        response_lower = qwen_response.lower()
        return any(indicator in response_lower for indicator in data_indicators)
    
    def _extract_data_need(self, qwen_response: str) -> str:
        """Extract what kind of data Qwen needs"""
        # Look for specific requests in Qwen's response
        if "woo" in qwen_response.lower():
            return "woo_info"
        elif "mo" in qwen_response.lower():
            return "mo_info"
        elif "ifá" in qwen_response.lower() or "ifa" in qwen_response.lower():
            return "ifa_kernels"
        elif "moment" in qwen_response.lower():
            return "mostar_moments"
        else:
            return "general_query"
    
    def _execute_neo4j_tool(self, function_name: str, arguments: Dict) -> Dict:
        """Execute Neo4j tools"""
        try:
            with self.neo4j_driver.session() as session:
                if function_name == "query_mind_graph":
                    result = session.run(arguments["cypher_query"])
                    records = [dict(record) for record in result]
                    return {"success": True, "results": records, "count": len(records)}
                
                elif function_name == "get_soul_info":
                    soul_name = arguments["soul_name"]
                    cypher = """
                    MATCH (soul:Soul {name: $name})
                    RETURN soul.name as name, soul.role as role, 
                           soul.archetype as archetype, soul.domain as domain
                    """
                    result = session.run(cypher, name=soul_name)
                    record = result.single()
                    if record:
                        return {"success": True, "soul": dict(record)}
                    else:
                        return {"success": False, "message": f"Soul {soul_name} not found"}
                
                elif function_name == "log_mostar_moment":
                    cypher = """
                    MATCH (flame:AfricanFlame {id: 'african_flame_master'})
                    CREATE (moment:MoStarMoment {
                        thought: $thought,
                        action: $action,
                        residue: $residue,
                        timestamp: datetime()
                    })
                    MERGE (moment)-[:LOGGED_TO]->(flame)
                    RETURN moment.timestamp as logged_at
                    """
                    result = session.run(cypher, **arguments)
                    return {"success": True, "logged_at": str(result.single()["logged_at"])}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_data_with_mistral(self, data_need: str, original_query: str) -> str:
        """Use Mistral to retrieve data from Neo4j"""
        
        # Construct specific query for Mistral based on data need
        if data_need == "woo_info":
            mistral_query = "Get information about Woo from the Soul database. Use get_soul_info function."
        elif data_need == "mo_info":
            mistral_query = "Get information about Mo from the Soul database. Use get_soul_info function."
        elif data_need == "ifa_kernels":
            mistral_query = "Query the mind graph for Ifá reasoning kernels. Use query_mind_graph with appropriate Cypher."
        else:
            mistral_query = f"Query the Neo4j database to help answer: {original_query}"
        
        print(f"🔧 [MISTRAL] Executing data retrieval for: {data_need}")
        
        try:
            # Get response from Mistral with tools
            response = ollama.chat(
                model=self.mistral_model,
                messages=[{"role": "user", "content": mistral_query}],
                tools=self.neo4j_tools
            )
            
            # Handle tool calls if present
            if response.get("message", {}).get("tool_calls"):
                messages = [{"role": "user", "content": mistral_query}]
                messages.append(response["message"])
                
                for tool_call in response["message"]["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    arguments = tool_call["function"]["arguments"]
                    
                    # Execute the tool
                    tool_result = self._execute_neo4j_tool(function_name, arguments)
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "content": json.dumps(tool_result)
                    })
                
                # Get final response from Mistral after tool execution
                final_response = ollama.chat(
                    model=self.mistral_model,
                    messages=messages
                )
                
                return final_response["message"]["content"]
            else:
                # No tool calls, return direct response
                return response["message"]["content"]
                
        except Exception as e:
            print(f"❌ [MISTRAL ERROR] {e}")
            return f"Error retrieving data: {e}"
    
    def query(self, user_message: str) -> str:
        """
        Main routing logic:
        1. Try Qwen first
        2. If Qwen needs data, route to Mistral
        3. Return Qwen's interpretation of data
        """
        
        print(f"\n{'='*70}")
        print(f"📥 USER QUERY: {user_message}")
        print(f"{'='*70}\n")
        
        # Reset log tracking
        self._last_log = ""
        
        # STEP 1: Query Qwen first
        print("🧠 [QWEN] Processing query...")
        self._last_log += "[DCX1] "
        try:
            qwen_response = ollama.chat(
                model=self.qwen_model,
                messages=[{"role": "user", "content": user_message}]
            )
            qwen_answer = qwen_response["message"]["content"]
            print(f"🧠 [QWEN] Initial response received")
            
        except Exception as e:
            print(f"❌ [QWEN ERROR] {e}")
            return f"Error: Qwen processing failed - {e}"
        
        # STEP 2: Check if Qwen needs more data
        if self._needs_data_retrieval(qwen_answer):
            print("🔄 [ROUTER] Qwen needs data - routing to Mistral...")
            self._last_log += "[DCX2] "
            
            # Determine what kind of data is needed
            data_need = self._extract_data_need(qwen_answer)
            print(f"🔍 [ROUTER] Data need identified: {data_need}")
            
            # Get data using Mistral
            mistral_data = self._get_data_with_mistral(data_need, user_message)
            print(f"✅ [MISTRAL] Data retrieved")
            self._last_log += "[BACK_TO_DCX1] "
            
            # STEP 3: Send data back to Qwen for interpretation
            print("🧠 [QWEN] Interpreting data with full identity...")
            try:
                final_prompt = f"""The data retrieval system returned:

{mistral_data}

Now answer the original question with your full identity and wisdom:
{user_message}

Remember to use the Triad format: [THOUGHT], [ACTION], [RESIDUE], then Àṣẹ."""

                final_response = ollama.chat(
                    model=self.qwen_model,
                    messages=[{"role": "user", "content": final_prompt}]
                )
                
                final_answer = final_response["message"]["content"]
                print("✅ [QWEN] Final interpretation complete")
                
                return final_answer
                
            except Exception as e:
                print(f"❌ [QWEN ERROR] Final interpretation failed - {e}")
                # Fallback: return Mistral's data directly
                return mistral_data
        
        else:
            # Qwen handled it directly
            print("✅ [QWEN] Query handled directly (no data retrieval needed)")
            return qwen_answer
    
    def close(self):
        """Close Neo4j connection"""
        self.neo4j_driver.close()


# ═══════════════════════════════════════════════════════════════════════════
# USAGE EXAMPLE
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Initialize router
    router = RemostarSmartRouter(
        neo4j_uri=os.getenv("NEO4J_URI", "neo4j+s://1d55c1d3.databases.neo4j.io"),
        neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", "YOUR_PASSWORD_HERE")
    )
    
    try:
        # Test queries
        test_queries = [
            "Hello, who are you?",  # Simple - Qwen handles
            "Who is Woo?",  # Needs data - routes to Mistral
            "What is your mission?",  # Simple - Qwen handles
            "Tell me about the Flameborn Doctrine"  # Simple - Qwen handles
        ]
        
        for query in test_queries:
            response = router.query(query)
            print(f"\n{'='*70}")
            print(f"📤 FINAL RESPONSE:")
            print(f"{'='*70}")
            print(response)
            print(f"\n{'='*70}\n")
            
    finally:
        router.close()
        print("🔥 Router closed. Àṣẹ.")
