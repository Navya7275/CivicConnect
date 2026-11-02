from unittest.mock import MagicMock, patch

from backend.agents.synthesis import SynthesisAgent
from backend.retrieval.hybrid_search import HybridRetriever


def test_retrieval_and_synthesis_pipeline():
    query = (
        "What is consumer protection?"
    )

    # Use the real retrieval pipeline.
    retriever = HybridRetriever()

    retrieved_chunks = retriever.search(
        query,
        filters={
            "jurisdiction": "Central"
        },
        limit=3
    )

    assert retrieved_chunks
    assert len(retrieved_chunks) <= 3

    for chunk in retrieved_chunks:
        assert "chunk_id" in chunk
        assert "act" in chunk
        assert "section" in chunk
        assert "source_url" in chunk
        assert chunk["jurisdiction"] == "Central"

    # Mock the LLM call so this test does not require
    # a real Groq API request.
    mock_response = MagicMock()

    mock_response.choices[0].message.content = (
        "Consumer protection is governed by the "
        "Consumer Protection Act, 2019."
    )

    with patch(
        "backend.agents.synthesis.Groq"
    ) as mock_groq:

        mock_client = mock_groq.return_value

        mock_client.chat.completions.create.return_value = (
            mock_response
        )

        agent = SynthesisAgent()

        result = agent.synthesize(
            query,
            retrieved_chunks
        )

    assert "answer" in result
    assert "citations" in result

    assert result["answer"] == (
        "Consumer protection is governed by the "
        "Consumer Protection Act, 2019."
    )

    assert result["citations"]

    for citation in result["citations"]:
        assert "chunk_id" in citation
        assert "act" in citation
        assert "section" in citation
        assert "jurisdiction" in citation
        assert "source_url" in citation