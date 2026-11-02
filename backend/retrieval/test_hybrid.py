from chunks import get_mock_chunks
from hybrid_search import HybridRetriever


chunks = get_mock_chunks()

retriever = HybridRetriever(chunks)

results = retriever.search(
    "What happens when a cheque bounces because there is not enough money?",
    filters={
        "jurisdiction": "Central"
    },
    limit=3
)

print("Hybrid Search Results:")

for chunk in results:
    print(
        chunk["chunk_id"],
        "->",
        chunk["section"],
        "->",
        chunk["act"],
        "->",
        chunk["jurisdiction"]
    )