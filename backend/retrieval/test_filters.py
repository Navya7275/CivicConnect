from chunks import get_mock_chunks
from filters import filter_by_metadata


chunks = get_mock_chunks()

results = filter_by_metadata(
    chunks,
    {
        "jurisdiction": "Central"
    }
)

print("Filtered chunks:")

for chunk in results:
    print(
        chunk["chunk_id"],
        "->",
        chunk["jurisdiction"],
        "->",
        chunk["act"]
    )