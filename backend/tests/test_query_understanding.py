"""Tests for the Query Understanding agent.

These run offline: no model download, no API key, no network. That is
deliberate — a test that needs the internet is a test that will fail in CI on
a bad day for reasons that have nothing to do with the code.
"""

from __future__ import annotations

import pytest

from backend.agents.query_understanding import (
    CENTRAL,
    QueryUnderstandingAgent,
    classify_intent,
    detect_state,
    rewrite_query,
)


@pytest.fixture
def agent() -> QueryUnderstandingAgent:
    return QueryUnderstandingAgent()


# --------------------------------------------------------------------------
# State detection
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("What are my rights as a tenant in Madhya Pradesh?", "Madhya Pradesh"),
        ("rent rules in maharashtra", "Maharashtra"),
        ("I live in Tamil Nadu", "Tamil Nadu"),
        ("landlord issue in Delhi", "Delhi"),
        ("scheme for farmers in UP", "Uttar Pradesh"),
        ("pension in Orissa", "Odisha"),          # old name still recognised
        ("housing rules in Pondicherry", "Puducherry"),
        ("What is the refund policy?", None),      # no state mentioned
    ],
)
def test_detect_state(text: str, expected: str | None) -> None:
    assert detect_state(text) == expected


def test_detect_state_prefers_full_name_over_abbreviation() -> None:
    """'Andhra Pradesh' must win over a stray 'AP' elsewhere in the text."""
    assert detect_state("scheme in Andhra Pradesh") == "Andhra Pradesh"


def test_mp_is_not_matched_when_it_means_member_of_parliament() -> None:
    """'MP' is ambiguous. Do not read it as a state when it clearly is not.

    Getting this wrong would silently filter a national question down to one
    state's law, which is exactly the confusion this project exists to avoid.
    """
    assert detect_state("How do I write to my MP, a Member of Parliament?") is None


def test_mp_is_matched_when_it_means_the_state() -> None:
    assert detect_state("rent agreement rules in MP") == "Madhya Pradesh"


def test_up_is_not_matched_inside_a_phrasal_verb() -> None:
    """'set up', 'sign up' and friends must not be read as Uttar Pradesh."""
    assert detect_state("How do I set up a consumer complaint?") is None


def test_state_alias_does_not_match_inside_another_word() -> None:
    """Word boundaries: 'ap' must not match inside 'apply'."""
    assert detect_state("How do I apply for a ration card?") is None


# --------------------------------------------------------------------------
# Intent classification
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("The shop refused a refund for a defective phone", "consumer"),
        ("Am I eligible for the PM-KISAN scheme?", "welfare"),
        ("My landlord is not returning my security deposit", "housing"),
        ("My employer has not paid my gratuity", "labour"),
        ("How do I file an RTI application?", "rti"),
        ("I got a challan for not wearing a helmet", "traffic"),
        ("The police refused to register my FIR", "police"),
    ],
)
def test_classify_intent(text: str, expected: str) -> None:
    intent, _scores = classify_intent(text)
    assert intent == expected


def test_unknown_question_falls_back_to_general() -> None:
    intent, scores = classify_intent("What is the weather like today?")
    assert intent == "general"
    assert all(score == 0 for score in scores.values())


def test_intent_scores_are_returned_for_every_intent() -> None:
    """The score table is part of the contract — tests and debugging use it."""
    _intent, scores = classify_intent("refund for a defective product")
    assert set(scores) == {"consumer", "welfare", "housing", "labour", "rti", "traffic", "police"}
    assert scores["consumer"] > 0


# --------------------------------------------------------------------------
# Query rewriting
# --------------------------------------------------------------------------

def test_rewrite_expands_abbreviations_for_keyword_search() -> None:
    rewritten = rewrite_query("How do I file an RTI?", "rti", None)
    assert "right to information" in rewritten.lower()


def test_rewrite_appends_the_state_so_bm25_can_match_on_it() -> None:
    rewritten = rewrite_query("rent rules", "housing", "Madhya Pradesh")
    assert "Madhya Pradesh" in rewritten


def test_rewrite_collapses_messy_whitespace() -> None:
    assert rewrite_query("  too    many\n\nspaces  ", "general", None) == "too many spaces"


def test_rewrite_keeps_the_users_own_wording() -> None:
    """We normalise, we do not reword. Changing the question changes the answer."""
    rewritten = rewrite_query("Can my landlord evict me without notice?", "housing", None)
    assert "landlord evict me without notice" in rewritten


# --------------------------------------------------------------------------
# The clarification rule — the behaviour that makes this not a chatbot
# --------------------------------------------------------------------------

def test_state_specific_question_without_a_state_asks_instead_of_guessing(agent) -> None:
    result = agent.understand("Can my landlord increase the rent whenever he wants?")

    assert result.intent == "housing"
    assert result.needs_clarification is True
    assert result.jurisdiction == "Unknown"
    assert result.clarification_question is not None
    assert "which state" in result.clarification_question.lower()


def test_clarification_explains_why_we_are_asking(agent) -> None:
    """Asking without a reason is annoying. Asking with one is helpful."""
    result = agent.understand("What is the minimum wage I should be paid?")
    assert result.needs_clarification is True
    assert "state" in result.clarification_question.lower()


def test_state_specific_question_with_a_state_proceeds(agent) -> None:
    result = agent.understand("Can my landlord increase the rent?", state="Madhya Pradesh")

    assert result.needs_clarification is False
    assert result.jurisdiction == "Madhya Pradesh"
    assert result.detected_state == "Madhya Pradesh"


def test_state_mentioned_in_the_question_counts_as_answering_it(agent) -> None:
    result = agent.understand("Can my landlord in Kerala increase the rent?")

    assert result.needs_clarification is False
    assert result.jurisdiction == "Kerala"


def test_central_law_question_never_asks_for_a_state(agent) -> None:
    """Consumer protection is one central Act. Asking for a state would be noise."""
    result = agent.understand("The seller refused a refund for a defective product")

    assert result.intent == "consumer"
    assert result.needs_clarification is False
    assert result.jurisdiction == CENTRAL


def test_explicitly_selected_state_beats_one_mentioned_in_the_text(agent) -> None:
    """A dropdown choice is stronger evidence than a passing mention."""
    result = agent.understand(
        "My friend in Kerala had this problem, what about me?",
        state="Punjab",
    )
    assert result.jurisdiction == "Punjab"


def test_general_question_defaults_to_central_without_clarifying(agent) -> None:
    result = agent.understand("What are my basic rights as a citizen?")

    assert result.intent == "general"
    assert result.needs_clarification is False
    assert result.jurisdiction == CENTRAL
