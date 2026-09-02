import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parents[2])
)

from chunks import get_mock_chunks
from hybrid_search import HybridRetriever
from backend.agents.synthesis import SynthesisAgent


# Load mock chunks
chunks = get_mock_chunks()


# Initialize retrieval and synthesis
retriever = HybridRetriever(chunks)
agent = SynthesisAgent()


# User query
query = "What happens when a cheque bounces because there is not enough money?"


# Step 1: Hybrid retrieval
retrieved_chunks = retriever.search(
    query,
    filters={
        "jurisdiction": "Central"
    },
    limit=3
)


print("\nRetrieved Chunks:")

for chunk in retrieved_chunks:
    print(
        chunk["chunk_id"],
        "->",
        chunk["act"],
        "-> Section",
        chunk["section"]
    )


# Step 2: LLM synthesis
result = agent.synthesize(
    query,
    retrieved_chunks
)


# Step 3: Final answer
print("\nCivicConnect Answer:")
print(result["answer"])


# Step 4: Sources
print("\nSources:")

for source in result["sources"]:
    print(
        source["chunk_id"],
        "->",
        source["act"],
        "-> Section",
        source["section"],
        "->",
        source["source_url"]
    )