# MoStar Grid Memory Layer

This directory contains the LangChain integration for the MoStar Grid.

## Components

*   **`ingest.py`**: Loads the `exports/activation_subgraph.json` snapshot and creates a FAISS vector store in `backend/data/memory_store`.
    *   Run: `python backend/memory_layer/ingest.py`
*   **`retriever.py`**: Provides the `MoStarMemory` class to query the vector store.
    *   Run: `python backend/memory_layer/retriever.py` (for testing)
*   **`agent_tool.py`**: Exports `get_memory_tool()` for use in LangChain agents.
    *   Run: `python backend/memory_layer/agent_tool.py` (for testing)

## Usage

To use the memory in an agent:

```python
from backend.memory_layer.agent_tool import get_memory_tool
from langchain.agents import initialize_agent, AgentType
from langchain_community.llms import Ollama

llm = Ollama(model="llama3")
tools = [get_memory_tool()]
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

agent.run("What happened in the Genesis Era?")
```
