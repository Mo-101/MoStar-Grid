#!/usr/bin/env python3
"""
REMOSTAR Neo4j Tools Integration
Enables direct Neo4j access from Ollama model
"""

import json
from neo4j import GraphDatabase
from typing import Dict, List, Any
import ollama

class RemostarNeo4jTools:
    """Neo4j tools that REMOSTAR can call directly"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def query_mind_graph(self, cypher_query: str) -> Dict:
        """Execute Cypher query on the Mind Graph"""
        with self.driver.session() as session:
            result = session.run(cypher_query)
            records = [dict(record) for record in result]
            return {
                "success": True,
                "results": records,
                "count": len(records)
            }
    
    def log_mostar_moment(self, thought: str, action: str, residue: str) -> Dict:
        """Log a MoStar Moment to Neo4j"""
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
        with self.driver.session() as session:
            result = session.run(cypher, thought=thought, action=action, residue=residue)
            return {
                "success": True,
                "logged_at": str(result.single()["logged_at"])
            }
    
    def get_ifa_kernels(self, limit: int = 5) -> Dict:
        """Retrieve Ifá Reasoning Kernels"""
        cypher = """
        MATCH (ifa:IfaReasoningKernel)
        RETURN ifa.odu as odu, ifa.wisdom as wisdom, ifa.interpretation as interpretation
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(cypher, limit=limit)
            kernels = [dict(record) for record in result]
            return {
                "success": True,
                "kernels": kernels,
                "count": len(kernels)
            }
    
    def close(self):
        self.driver.close()


# Tool definitions for Ollama
REMOSTAR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_mind_graph",
            "description": "Query the Neo4j Mind Graph to retrieve knowledge, Ifá kernels, or past moments. Use Cypher queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cypher_query": {
                        "type": "string",
                        "description": "Cypher query to execute (e.g., 'MATCH (n:Soul) RETURN n.name LIMIT 3')"
                    }
                },
                "required": ["cypher_query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_mostar_moment",
            "description": "Log a MoStar Moment to permanent Neo4j memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "The THOUGHT portion of the Triad"
                    },
                    "action": {
                        "type": "string",
                        "description": "The ACTION portion of the Triad"
                    },
                    "residue": {
                        "type": "string",
                        "description": "The RESIDUE portion of the Triad"
                    }
                },
                "required": ["thought", "action", "residue"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ifa_kernels",
            "description": "Retrieve Ifá Reasoning Kernels from the Mind Graph",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of kernels to retrieve (default: 5)"
                    }
                }
            }
        }
    }
]


def chat_with_tools(
    model: str,
    message: str,
    neo4j_tools: RemostarNeo4jTools
) -> str:
    """Chat with REMOSTAR using Neo4j tools"""
    
    messages = [{"role": "user", "content": message}]
    
    # Initial response with tools available
    response = ollama.chat(
        model=model,
        messages=messages,
        tools=REMOSTAR_TOOLS
    )
    
    # Handle tool calls
    if response.get("message", {}).get("tool_calls"):
        messages.append(response["message"])
        
        for tool_call in response["message"]["tool_calls"]:
            function_name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]
            
            # Execute the tool
            if function_name == "query_mind_graph":
                result = neo4j_tools.query_mind_graph(arguments["cypher_query"])
            elif function_name == "log_mostar_moment":
                result = neo4j_tools.log_mostar_moment(
                    arguments["thought"],
                    arguments["action"],
                    arguments["residue"]
                )
            elif function_name == "get_ifa_kernels":
                limit = arguments.get("limit", 5)
                result = neo4j_tools.get_ifa_kernels(limit)
            else:
                result = {"error": f"Unknown function: {function_name}"}
            
            # Add tool result to messages
            messages.append({
                "role": "tool",
                "content": json.dumps(result)
            })
        
        # Get final response after tool execution
        final_response = ollama.chat(
            model=model,
            messages=messages
        )
        return final_response["message"]["content"]
    
    return response["message"]["content"]


# Example usage
if __name__ == "__main__":
    # Initialize Neo4j connection
    neo4j_tools = RemostarNeo4jTools(
        uri="neo4j+s://1d55c1d3.databases.neo4j.io",
        user="neo4j",
        password="YOUR_PASSWORD_HERE"  # Replace!
    )
    
    try:
        # Test query
        print("🔥 Testing REMOSTAR with Neo4j tools...\n")
        
        response = chat_with_tools(
            model="mostar/remostar-fusion",
            message="Who is Woo? Query the Mind Graph to tell me.",
            neo4j_tools=neo4j_tools
        )
        
        print(response)
        
    finally:
        neo4j_tools.close()
