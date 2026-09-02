import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parents[2])
)

from chunks import get_mock_chunks
from backend.agents.synthesis import SynthesisAgent


chunks = get_mock_chunks()

agent = SynthesisAgent()

query = "What happens when a cheque bounces because there is not enough money?"

answer = agent.synthesize(
    query,
    [chunks[0]]
)

print("\nCivicConnect Answer:")
print(answer["answer"])

print("\nSources:")

for source in answer["sources"]:
    print(
        source["chunk_id"],
        "->",
        source["act"],
        "-> Section",
        source["section"],
        "->",
        source["source_url"]
    )