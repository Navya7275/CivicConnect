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

def test_answer_token_budget_fits_the_free_tier() -> None:
    """max_tokens must stay under Groq's free-tier output budget.

    Leaving it unset sends the model's own default, 2048 for
    qwen/qwen3.8-27b. Groq checks the REQUESTED output figure against the
    per-minute allowance before running anything, so on the free tier's
    limit of 1000 every call was refused:

        429 Request too large ... output tokens per minute (OTPM):
        Limit 1000, Requested 2048 ... reduce max_tokens

    That is not a rate limit waiting would clear. It took out the synthesis
    half of the evaluation and backend/tests/test_api.py, and looked like
    flakiness because a 429 normally means "try again later".
    """
    from backend.agents.synthesis import MAX_ANSWER_TOKENS

    GROQ_FREE_TIER_OTPM = 1000
    assert 0 < MAX_ANSWER_TOKENS < GROQ_FREE_TIER_OTPM, (
        f"max_tokens is {MAX_ANSWER_TOKENS}; anything at or above "
        f"{GROQ_FREE_TIER_OTPM} is rejected outright on the free tier. "
        f"Raise it per-environment with CIVICCONNECT_MAX_ANSWER_TOKENS "
        f"rather than changing the default."
    )


def test_the_api_call_actually_passes_max_tokens() -> None:
    """Defining the constant is not the same as sending it.

    The bug was a missing argument, not a wrong value, so the test that
    matters is whether it reaches the request.
    """
    import inspect

    from backend.agents import synthesis as synthesis_module

    source = inspect.getsource(synthesis_module.SynthesisAgent.synthesize)
    code = "\n".join(line.split("#", 1)[0] for line in source.splitlines())
    assert "max_tokens=" in code, (
        "synthesize() must pass max_tokens; without it the client sends the "
        "model default and the free tier refuses every request"
    )
