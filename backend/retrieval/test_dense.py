from chunks import get_mock_chunks
from dense import DenseRetriever


chunks = get_mock_chunks()

retriever = DenseRetriever(chunks)

results = retriever.search(
    "What happens when a cheque bounces because there is not enough money?",
    limit=3
)

for chunk in results:
    print(
        chunk["chunk_id"],
        "->",
        chunk["section"],
        "->",
        chunk["act"]
    )