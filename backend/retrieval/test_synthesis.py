from unittest.mock import MagicMock, patch

import pytest

from backend.agents.synthesis import SynthesisAgent


@pytest.fixture(autouse=True)
def _dummy_api_key(monkeypatch):
    """Give every test a throwaway key.

    SynthesisAgent raises on a missing GROQ_API_KEY so a misconfigured setup
    fails loudly instead of deep inside the Groq client. The tests still never
    reach the network, because the Groq class itself is patched below.
    """
    monkeypatch.setenv("GROQ_API_KEY", "test-key-not-a-real-one")


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
    # __init__ builds a client whether or not the test calls the API.
    with patch("backend.agents.synthesis.Groq"):
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