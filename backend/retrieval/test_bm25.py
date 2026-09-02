from chunks import get_mock_chunks

from bm25 import BM25Retriever


chunks = get_mock_chunks()

retriever = BM25Retriever(chunks)

results = retriever.search(
    "cheque dishonour Section 138",
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