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


# --------------------------------------------------------------------------
# Citations name the provisions the answer relied on, not everything searched
# --------------------------------------------------------------------------

RTI_ACT = "Right to Information Act, 2005"
CPA_ACT = "Consumer Protection Act, 2019"


def _chunk(chunk_id, act, section):
    return {"chunk_id": chunk_id, "act": act, "section": section}


RETRIEVED = [
    _chunk("rti-7", RTI_ACT, "Section 7"),
    _chunk("rti-6", RTI_ACT, "Section 6"),
    _chunk("rti-19", RTI_ACT, "Section 19"),
    _chunk("cpa-7", CPA_ACT, "Section 7"),
    _chunk("cpa-35", CPA_ACT, "Section 35"),
]


def test_citations_are_the_sections_the_answer_names() -> None:
    """One provision answered the question, so one citation is shown.

    Returning every retrieved chunk made the citation list a copy of the
    retrieval list. The interface then showed "Sources (10)" for an answer
    resting on one of them, which defeats the purpose: a citation is there
    so the reader can check the sentence against it, and ten cannot be
    checked against anything.
    """
    from backend.agents.synthesis import cited_chunks

    answer = ("You should get a reply within 30 days. This comes from "
              "Section 7 of the Right to Information Act, 2005.")
    assert [c["chunk_id"] for c in cited_chunks(answer, RETRIEVED)] == ["rti-7"]


def test_citations_cover_every_section_the_answer_names() -> None:
    from backend.agents.synthesis import cited_chunks

    answer = "See Sections 6 and 19 of the Right to Information Act, 2005."
    assert [c["chunk_id"] for c in cited_chunks(answer, RETRIEVED)] == ["rti-6", "rti-19"]


def test_a_shared_section_number_without_an_act_keeps_both() -> None:
    """Two Acts have a Section 7. Naming neither cannot resolve to one.

    Guessing would be worse than showing both: the reader can tell which is
    relevant, and silently dropping the right one cannot be noticed.
    """
    from backend.agents.synthesis import cited_chunks

    answer = "You should get a reply within 30 days under Section 7."
    assert [c["chunk_id"] for c in cited_chunks(answer, RETRIEVED)] == ["rti-7", "cpa-7"]


def test_an_answer_naming_no_section_keeps_every_source() -> None:
    """Welfare scheme answers have no sections to name, and refusals cite none.

    Falling back to the retrieved set shows what was searched. Returning
    nothing would leave the reader with an unsourced answer, which is worse
    than an imprecisely sourced one.
    """
    from backend.agents.synthesis import cited_chunks

    scheme_answer = "You can apply through the common service centre in your block."
    refusal = "The sources I have do not cover this."
    for answer in (scheme_answer, refusal, "", None):
        assert len(cited_chunks(answer, RETRIEVED)) == len(RETRIEVED)


def test_a_named_section_that_matches_nothing_keeps_every_source() -> None:
    from backend.agents.synthesis import cited_chunks

    answer = "This comes from Section 412 of an Act that was not retrieved."
    assert len(cited_chunks(answer, RETRIEVED)) == len(RETRIEVED)


def test_no_retrieval_means_no_citations() -> None:
    from backend.agents.synthesis import cited_chunks

    assert cited_chunks("Section 7 applies.", []) == []


def test_citation_filter_reuses_the_verification_parser() -> None:
    """Not a second copy of the section parser.

    The query and document tokenizers were once two implementations that
    agreed by coincidence, drifted, and cost fifty places of retrieval rank
    without failing a test. One parser, imported.
    """
    import inspect

    from backend.agents import synthesis as synthesis_module

    source = inspect.getsource(synthesis_module)
    assert "from backend.agents.verification import" in source
    assert "extract_section_numbers" in source

    from backend.agents.synthesis import extract_section_numbers as from_synthesis
    from backend.agents.verification import extract_section_numbers as from_verification
    assert from_synthesis is from_verification
