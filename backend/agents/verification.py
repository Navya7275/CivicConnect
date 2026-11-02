"""Verification agent — Phase C3.

Checks that an answer only cites law we actually retrieved.

Why this needs to look at the answer text and not just the citations list:

A synthesis agent returns two things — some prose, and a list of citations. It
is entirely possible for the list to be clean while the prose invents a section
number:

    answer    : "Under Section 47 you may appeal to the State Commission."
    citations : [ { act: "Consumer Protection Act, 2019", section: "Section 35" } ]

Phase C1's check only compared the citations list against the retrieved chunks,
so this passed. The user then reads "Section 47" — a section number nothing
verified, presented with the same confidence as the rest of the answer. That is
exactly the failure this project exists to prevent, so checking the list alone
is not enough.

This module therefore runs two independent checks, and both must pass:

1. **Citation grounding** — every entry in the citations list corresponds to a
   retrieved chunk.
2. **Prose grounding** — every section number written in the answer text
   corresponds to a retrieved chunk.

A failure of either sends the answer back to synthesis, and every rejection is
recorded so the Phase E evaluation can count hallucinations (see issue #13).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Section reference extraction
# --------------------------------------------------------------------------

#: Matches the start of a section reference and captures its first number.
#:
#: Handles the forms that actually appear in Indian legal writing:
#:   Section 35 · section 35 · Sections 35 · Sec. 35 · Sec 35 · S. 35 · §35
#: and any sub-clauses that follow: Section 2(9), Section 35(1)(a).
#:
#: Bare "s." is deliberately required to have the full stop, so ordinary
#: sentences ending in "s" cannot start a false match.
_SECTION_ANCHOR = re.compile(
    r"""
    (?:
        §\s*                              # §35
      | \bsections?\b\.?\s*               # Section / Sections / section.
      | \bsecs?\b\.?\s*                   # Sec / Secs / Sec.
      | \bs\.\s*                          # s. 35
    )
    (\d+[A-Z]?)                           # the section number: 35, 35A
    """,
    re.IGNORECASE | re.VERBOSE,
)

#: After an anchor, consume a comma/and-separated list: "Sections 35, 36 and 38".
#: Applied with `.match(text, position)`, which anchors at `position` already.
_SECTION_CONTINUATION = re.compile(
    r"""
    (?:\s*\([0-9a-zA-Z]+\))*              # skip sub-clauses on the previous number
    \s*(?:,|\band\b|&)\s*
    (\d+[A-Z]?)
    """,
    re.IGNORECASE | re.VERBOSE,
)


def extract_section_numbers(text: str) -> list[str]:
    """Pull every section number referenced in a piece of prose.

    Returns bare numbers (``"35"``, ``"2"``, ``"35A"``) in the order they first
    appear, deduplicated. Sub-clauses are collapsed onto their parent section:
    ``"Section 2(9)"`` yields ``"2"``, because our corpus stores section-level
    chunks and the sub-clause lives inside the chunk text.

    Numbers that are not section references are not matched, because an anchor
    word is required. "within thirty days", "2 years" and "₹50,00,000" are all
    correctly ignored.

    Args:
        text: The answer prose.

    Returns:
        Deduplicated section numbers, in order of first appearance.
    """
    if not text:
        return []

    found: list[str] = []

    def remember(number: str) -> None:
        normalised = number.upper()
        if normalised not in found:
            found.append(normalised)

    for anchor in _SECTION_ANCHOR.finditer(text):
        remember(anchor.group(1))

        # Walk any "35, 36 and 38" list that follows this anchor.
        position = anchor.end()
        while True:
            continuation = _SECTION_CONTINUATION.match(text, position)
            if continuation is None:
                break
            remember(continuation.group(1))
            position = continuation.end()

    return found


def normalise_section(value: str | None) -> str | None:
    """Reduce a stored section label to a bare comparable number.

    ``"Section 35"`` -> ``"35"``, ``"Section 2(9)"`` -> ``"2"``, ``"35A"`` -> ``"35A"``.
    Returns None when no number can be found, so non-section chunks (welfare
    scheme entries, for instance) are simply not matched against.
    """
    if not value:
        return None
    match = re.search(r"(\d+[A-Z]?)", value, re.IGNORECASE)
    return match.group(1).upper() if match else None


# --------------------------------------------------------------------------
# Result type
# --------------------------------------------------------------------------

@dataclass
class VerificationResult:
    """The outcome of verifying one answer."""

    verified: bool
    status: str
    """One of: 'verified', 'ungrounded', 'skipped'."""

    ungrounded_citations: list[dict[str, Any]] = field(default_factory=list)
    """Citation entries with no matching retrieved chunk."""

    hallucinated_sections: list[str] = field(default_factory=list)
    """Section numbers written in the prose with no matching retrieved chunk.

    This is the number that matters for the project's central claim, and the
    one the Phase E evaluation reports as hallucination rate.
    """

    checked_sections: list[str] = field(default_factory=list)
    """Every section number found in the prose, grounded or not."""

    @property
    def rejection_summary(self) -> str:
        """One line explaining why verification failed, for logs and the report."""
        parts = []
        if self.hallucinated_sections:
            parts.append(f"sections not in sources: {', '.join(self.hallucinated_sections)}")
        if self.ungrounded_citations:
            labels = [
                f"{c.get('act', '?')} {c.get('section', '?')}"
                for c in self.ungrounded_citations
            ]
            parts.append(f"ungrounded citations: {'; '.join(labels)}")
        return " | ".join(parts) if parts else "no problems found"


# --------------------------------------------------------------------------
# The agent
# --------------------------------------------------------------------------

class VerificationAgent:
    """Decides whether an answer is grounded in the chunks that were retrieved."""

    def verify(
        self,
        answer: str,
        citations: list[dict[str, Any]],
        retrieved_chunks: list[dict[str, Any]],
    ) -> VerificationResult:
        """Check an answer against its sources.

        Args:
            answer: The generated prose.
            citations: What the synthesis agent said it cited.
            retrieved_chunks: What retrieval actually returned.

        Returns:
            A `VerificationResult`. `verified` is True only when the citations
            list and the prose are both fully grounded.
        """
        # What the retrieved chunks let us support.
        known_ids = {c.get("chunk_id") for c in retrieved_chunks if c.get("chunk_id")}
        known_act_sections = {
            (c.get("act"), c.get("section")) for c in retrieved_chunks
        }
        known_numbers = {
            number
            for number in (normalise_section(c.get("section")) for c in retrieved_chunks)
            if number
        }

        # --- check 1: the citations list ---
        ungrounded_citations = [
            citation
            for citation in citations
            if citation.get("chunk_id") not in known_ids
            and (citation.get("act"), citation.get("section")) not in known_act_sections
        ]

        # --- check 2: section numbers written in the prose ---
        #
        # This is the check Phase C1 was missing. Note the deliberate limitation:
        # we match on section number alone, not on the act it was attributed to.
        # Pairing a section to its act from free prose is fragile, and being
        # over-strict here causes needless retries. So "Section 35 of the Motor
        # Vehicles Act" will pass while CPA Section 35 is in context. Catching
        # that needs act-aware matching, which is worth doing once we index
        # several acts that share section numbers.
        prose_sections = extract_section_numbers(answer)
        hallucinated = [
            number for number in prose_sections if number not in known_numbers
        ]

        # Nothing cited and nothing claimed in the prose: a legitimate
        # "we don't have enough information" answer. Not a failure, but not
        # something we can call verified either.
        if not citations and not prose_sections:
            return VerificationResult(
                verified=False,
                status="skipped",
                checked_sections=[],
            )

        if ungrounded_citations or hallucinated:
            result = VerificationResult(
                verified=False,
                status="ungrounded",
                ungrounded_citations=ungrounded_citations,
                hallucinated_sections=hallucinated,
                checked_sections=prose_sections,
            )
            # Logged at warning level and in a stable shape, so Phase E can
            # count these and a demo panel can show them.
            logger.warning("Verification rejected an answer — %s", result.rejection_summary)
            return result

        return VerificationResult(
            verified=True,
            status="verified",
            checked_sections=prose_sections,
        )
