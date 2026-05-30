from langchain_core.tools import Tool
try:
    from .retriever import MoStarMemory
except ImportError:
    # Fallback for running as script
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from backend.memory_layer.retriever import MoStarMemory

def get_memory_tool():
    """Create a LangChain tool for querying the MoStar Grid memory."""
    memory = MoStarMemory()
    
    return Tool(
        name="mostar_memory_search",
        func=memory.get_relevant_context,
        description="Useful for answering questions about the history, moments, and resonance of the MoStar Grid. Input should be a search query."
    )

if __name__ == "__main__":
    # Test the tool
    tool = get_memory_tool()
    print(tool.run("What is the Genesis Era?"))
