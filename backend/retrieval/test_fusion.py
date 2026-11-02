from chunks import get_mock_chunks
from fusion import reciprocal_rank_fusion


chunks = get_mock_chunks()

# Simulated BM25 ranking
bm25_results = [
    chunks[0],
    chunks[1],
    chunks[2]
]

# Simulated Dense ranking
dense_results = [
    chunks[0],
    chunks[2],
    chunks[1]
]

results = reciprocal_rank_fusion(
    [bm25_results, dense_results],
    limit=3
)

print("RRF results:")

for chunk in results:
    print(
        chunk["chunk_id"],
        "->",
        chunk["section"],
        "->",
        chunk["act"]
    )