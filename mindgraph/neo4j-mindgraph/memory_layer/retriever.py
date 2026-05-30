import os
from typing import Any, List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

# Configuration
STORE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "memory_store"
)
MODEL_NAME = "all-MiniLM-L6-v2"


class MoStarMemory:
    def __init__(self):
        if not os.path.exists(STORE_PATH):
            raise FileNotFoundError(
                f"Memory store not found at {STORE_PATH}. Run ingest.py first."
            )

        self.embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
        self.vectorstore = FAISS.load_local(
            STORE_PATH,
            self.embeddings,
            allow_dangerous_deserialization=True,  # Safe since we created it
        )
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity", search_kwargs={"k": 5}
        )

    def search(self, query: str, k: int = 5) -> List[Document]:
        """Raw search against the vector store."""
        return self.vectorstore.similarity_search(query, k=k)

    def get_relevant_context(self, query: str) -> str:
        """Get a formatted string of relevant context for LLM injection."""
        docs = self.search(query)
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"--- Context {i} ---\n{doc.page_content}")
        return "\n\n".join(context_parts)


if __name__ == "__main__":
    # Test the retriever
    memory = MoStarMemory()
    test_query = "Who is Woo?"
    print(f"🔍 Query: {test_query}")
    results = memory.search(test_query)
    for doc in results:
        print(f"\n📄 {doc.page_content}")
        print(
            f"   (Score info not available in simple search, Metadata: {doc.metadata})"
        )
