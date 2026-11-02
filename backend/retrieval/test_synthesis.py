from unittest.mock import MagicMock, patch

from backend.agents.synthesis import SynthesisAgent


def test_synthesis_returns_answer_and_citations():
    retrieved_chunks = [
        {
            "chunk_id": "cpa2019-s1",
            "text": (
                "This Act may be called the Consumer Protection Act, 2019."
            ),
            "act": "Consumer Protection Act, 2019",
            "section": "Section 1",
            "jurisdiction": "Central",
            "source_url": "https://indiacode.nic.in",
        }
    ]

    mock_response = MagicMock()
    mock_response.choices[0].message.content = (
        "The Consumer Protection Act, 2019 is the relevant Act."
    )

    with patch(
        "backend.agents.synthesis.Groq"
    ) as mock_groq:

        mock_client = mock_groq.return_value
        mock_client.chat.completions.create.return_value = mock_response

        agent = SynthesisAgent()

        result = agent.synthesize(
            "What is the Consumer Protection Act?",
            retrieved_chunks
        )

    assert "answer" in result
    assert "citations" in result

    assert result["answer"] == (
        "The Consumer Protection Act, 2019 is the relevant Act."
    )

    assert len(result["citations"]) == 1
    assert result["citations"][0]["chunk_id"] == "cpa2019-s1"
    assert result["citations"][0]["act"] == (
        "Consumer Protection Act, 2019"
    )
    assert result["citations"][0]["section"] == "Section 1"


def test_synthesis_handles_no_retrieved_chunks():
    agent = SynthesisAgent()

    result = agent.synthesize(
        "What is consumer protection?",
        []
    )

    assert result["answer"] == (
        "The available sources do not contain enough information "
        "to answer this question."
    )

    assert result["citations"] == []