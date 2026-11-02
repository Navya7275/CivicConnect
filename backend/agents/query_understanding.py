"""Query Understanding agent.

The first node in the pipeline. Before we search for anything, we work out:

1. **Intent** — which area of law or welfare the question is about.
2. **Jurisdiction** — whose law applies: Central, or a specific state.
3. **Whether we can answer at all** — some areas of law differ from state to
   state. If the user has not told us which state they are in, guessing would
   mean giving them another state's law, so we ask instead.

Point 3 is deliberate. A general-purpose chatbot will happily answer a rent
question with whichever state's rules it saw most during training. We would
rather ask one short question than confidently give someone the wrong law.

This implementation is rule-based, which means it is deterministic, fast, and
testable without a network connection or an API key. An LLM-backed version can
be added later behind the same `understand()` interface if the rules turn out
to be too rigid.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Jurisdictions
# --------------------------------------------------------------------------

CENTRAL = "Central"

#: Canonical state/UT name -> alternative spellings and abbreviations users type.
#: Canonical names follow the Government of India's official English spellings.
STATE_ALIASES: dict[str, tuple[str, ...]] = {
    "Andhra Pradesh": ("andhra pradesh", "andhra", "ap"),
    "Arunachal Pradesh": ("arunachal pradesh", "arunachal"),
    "Assam": ("assam",),
    "Bihar": ("bihar",),
    "Chhattisgarh": ("chhattisgarh", "chattisgarh"),
    "Goa": ("goa",),
    "Gujarat": ("gujarat",),
    "Haryana": ("haryana",),
    "Himachal Pradesh": ("himachal pradesh", "himachal", "hp"),
    "Jharkhand": ("jharkhand",),
    "Karnataka": ("karnataka",),
    "Kerala": ("kerala",),
    "Madhya Pradesh": ("madhya pradesh", "mp"),
    "Maharashtra": ("maharashtra",),
    "Manipur": ("manipur",),
    "Meghalaya": ("meghalaya",),
    "Mizoram": ("mizoram",),
    "Nagaland": ("nagaland",),
    "Odisha": ("odisha", "orissa"),
    "Punjab": ("punjab",),
    "Rajasthan": ("rajasthan",),
    "Sikkim": ("sikkim",),
    "Tamil Nadu": ("tamil nadu", "tamilnadu", "tn"),
    "Telangana": ("telangana",),
    "Tripura": ("tripura",),
    "Uttar Pradesh": ("uttar pradesh", "up"),
    "Uttarakhand": ("uttarakhand", "uttaranchal"),
    "West Bengal": ("west bengal",),
    # Union Territories
    "Andaman and Nicobar Islands": ("andaman and nicobar islands", "andaman and nicobar", "andaman"),
    "Chandigarh": ("chandigarh",),
    "Dadra and Nagar Haveli and Daman and Diu": ("dadra and nagar haveli and daman and diu", "dadra and nagar haveli", "daman and diu"),
    "Delhi": ("delhi", "new delhi", "nct of delhi"),
    "Jammu and Kashmir": ("jammu and kashmir", "jammu & kashmir", "j&k"),
    "Ladakh": ("ladakh",),
    "Lakshadweep": ("lakshadweep",),
    "Puducherry": ("puducherry", "pondicherry"),
}

#: Short aliases that collide with ordinary English or other abbreviations.
#: These are only accepted when nothing nearby suggests the other meaning.
#: "MP" is the obvious one — Madhya Pradesh, or Member of Parliament.
_AMBIGUOUS_ALIASES: dict[str, tuple[str, ...]] = {
    "mp": ("member", "parliament", "lok sabha", "rajya sabha", "constituency", "mla", "minister"),
    "ap": ("andhra",),  # bare "AP" is weak on its own; prefer the full name nearby
    "tn": (),
    "up": ("pick up", "set up", "give up", "sign up", "top up", "back up", "follow up"),
    "hp": ("laptop", "printer", "horsepower"),
}


# --------------------------------------------------------------------------
# Intents
# --------------------------------------------------------------------------

#: Intent -> keywords that suggest it. Order matters only for readability;
#: scoring below counts every match, so overlapping keywords are fine.
INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "consumer": (
        "consumer", "refund", "defective", "faulty", "warranty", "guarantee",
        "product liability", "unfair trade", "e-commerce", "online order",
        "shopkeeper", "seller", "complaint against", "deficiency in service",
        "replacement", "overcharged", "mrp", "food safety",
    ),
    "welfare": (
        "scheme", "yojana", "subsidy", "pension", "scholarship", "benefit",
        "eligible", "eligibility", "apply for", "ration", "bpl",
        "pm-kisan", "pmjdy", "jan dhan", "ayushman", "ladli", "widow",
        "old age", "disability certificate", "financial assistance",
    ),
    "housing": (
        "rent", "rental", "tenant", "landlord", "eviction", "lease",
        "security deposit", "tenancy", "rent agreement", "house owner",
        "vacate", "rent control",
    ),
    "labour": (
        "salary", "wages", "minimum wage", "overtime", "employer", "employee",
        "provident fund", "epf", "gratuity", "maternity leave", "bonus",
        "termination", "notice period", "workplace harassment", "posh",
        "contract labour", "working hours",
    ),
    "rti": (
        "rti", "right to information", "public information officer", "pio",
        "information request", "government record", "first appeal",
    ),
    "traffic": (
        "traffic", "challan", "driving licence", "driving license", "helmet",
        "motor vehicle", "accident claim", "third party insurance",
        "rash driving", "vehicle registration", "fine for",
    ),
    "police": (
        "fir", "police complaint", "arrest", "bail", "station house officer",
        "zero fir", "police refuse", "cognizable",
    ),
}

#: Intents where the answer genuinely depends on which state the user is in.
#:
#: Under the Seventh Schedule of the Constitution, land and tenancy are State
#: subjects, so every state has its own Rent Control Act. Minimum wages are
#: notified per state. Welfare schemes are a mix of central and state schemes,
#: and the state ones are usually the more generous. Policing is a State
#: subject in practice.
#:
#: Consumer protection, RTI and motor vehicles are governed by central Acts
#: that apply the same way everywhere, so we do not need to ask.
STATE_SPECIFIC_INTENTS: frozenset[str] = frozenset({
    "housing",
    "labour",
    "welfare",
    "police",
})

DEFAULT_INTENT = "general"

CLARIFICATION_TEMPLATE = (
    "This depends on which state you are in, because {reason}. "
    "Which state or union territory are you asking about?"
)

#: Why each state-specific intent needs a state, in plain language for the user.
_CLARIFICATION_REASONS: dict[str, str] = {
    "housing": "rent and tenancy laws are made by each state separately",
    "labour": "minimum wages and labour rules are notified state by state",
    "welfare": "many welfare schemes are run by individual state governments",
    "police": "police procedure and state rules differ between states",
}


# --------------------------------------------------------------------------
# Result type
# --------------------------------------------------------------------------

@dataclass
class QueryUnderstanding:
    """What the agent worked out about a question."""

    original_query: str
    rewritten_query: str
    intent: str
    jurisdiction: str
    detected_state: str | None
    needs_clarification: bool
    clarification_question: str | None = None
    intent_scores: dict[str, int] = field(default_factory=dict)

    @property
    def is_state_specific(self) -> bool:
        """True when this area of law differs between states."""
        return self.intent in STATE_SPECIFIC_INTENTS


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _contains_word(haystack: str, needle: str) -> bool:
    """True if `needle` appears in `haystack` as a whole word or phrase.

    Uses word boundaries so that "up" does not match inside "update", and
    "ap" does not match inside "apply".
    """
    return re.search(rf"\b{re.escape(needle)}\b", haystack) is not None


def detect_state(text: str) -> str | None:
    """Find an Indian state or union territory mentioned in `text`.

    Returns the canonical name, or None if nothing was found.

    Longer aliases are checked first so that "Andhra Pradesh" wins over the
    bare "AP", and so multi-word names are not missed.
    """
    lowered = text.lower()

    candidates: list[tuple[str, str]] = [
        (alias, canonical)
        for canonical, aliases in STATE_ALIASES.items()
        for alias in aliases
    ]
    candidates.sort(key=lambda pair: len(pair[0]), reverse=True)

    for alias, canonical in candidates:
        if not _contains_word(lowered, alias):
            continue

        # Short aliases can mean something else entirely. Skip them when a
        # nearby word suggests the other meaning.
        blockers = _AMBIGUOUS_ALIASES.get(alias)
        if blockers and any(blocker in lowered for blocker in blockers):
            continue

        return canonical

    return None


def classify_intent(text: str) -> tuple[str, dict[str, int]]:
    """Work out which area of law a question is about.

    Returns the winning intent and the full score table. The scores are
    returned so the API can expose them later for debugging, and so tests can
    assert on near-misses rather than only the winner.
    """
    lowered = text.lower()

    scores = {
        intent: sum(1 for keyword in keywords if _contains_word(lowered, keyword))
        for intent, keywords in INTENT_KEYWORDS.items()
    }

    best_intent = max(scores, key=lambda intent: scores[intent])
    if scores[best_intent] == 0:
        return DEFAULT_INTENT, scores

    return best_intent, scores


def rewrite_query(text: str, intent: str, state: str | None) -> str:
    """Tidy a question into something better suited to retrieval.

    This is deliberately conservative. We normalise whitespace, expand a few
    abbreviations that hurt keyword search, and append the jurisdiction so that
    BM25 has the state name to match on. We do not reword the user's question,
    because doing that can quietly change what they asked.
    """
    rewritten = re.sub(r"\s+", " ", text).strip()

    expansions = {
        r"\brti\b": "RTI right to information",
        r"\bfir\b": "FIR first information report",
        r"\bepf\b": "EPF employees provident fund",
        r"\bmrp\b": "MRP maximum retail price",
        r"\bposh\b": "POSH sexual harassment of women at workplace",
    }
    for pattern, replacement in expansions.items():
        rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)

    if state:
        rewritten = f"{rewritten} ({state})"

    return rewritten


# --------------------------------------------------------------------------
# The agent
# --------------------------------------------------------------------------

class QueryUnderstandingAgent:
    """Turns a raw question into intent, jurisdiction, and a search query."""

    def understand(self, query: str, state: str | None = None) -> QueryUnderstanding:
        """Analyse one question.

        Args:
            query: The user's question, in plain language.
            state: A state the user picked in the UI, if any. This takes
                priority over a state mentioned in the question text, because
                an explicit choice is stronger evidence than a passing mention.

        Returns:
            A `QueryUnderstanding` describing what we found.
        """
        intent, scores = classify_intent(query)

        # An explicit selection beats a mention in the text.
        supplied_state = detect_state(state) if state else None
        mentioned_state = detect_state(query)
        resolved_state = supplied_state or mentioned_state

        state_specific = intent in STATE_SPECIFIC_INTENTS
        needs_clarification = state_specific and resolved_state is None

        if needs_clarification:
            jurisdiction = "Unknown"
            reason = _CLARIFICATION_REASONS.get(intent, "the rules differ between states")
            clarification = CLARIFICATION_TEMPLATE.format(reason=reason)
        else:
            # With no state involved, we are looking at central law.
            jurisdiction = resolved_state or CENTRAL
            clarification = None

        return QueryUnderstanding(
            original_query=query,
            rewritten_query=rewrite_query(query, intent, resolved_state),
            intent=intent,
            jurisdiction=jurisdiction,
            detected_state=resolved_state,
            needs_clarification=needs_clarification,
            clarification_question=clarification,
            intent_scores=scores,
        )
