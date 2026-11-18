import os
import re

from dotenv import load_dotenv
from groq import Groq

from backend.agents.verification import (
    extract_section_numbers,
    normalise_section,
)


load_dotenv()


# How many tokens the model may spend on an answer.
#
# This was previously unset, which is not the same as unlimited: the client
# then sends the model's own default, 2048 for qwen/qwen3.8-27b. Groq's free
# tier allows 1000 output tokens per minute, and it checks the REQUESTED
# figure before running anything, so every single call was refused outright:
#
#     429 Request too large ... output tokens per minute (OTPM):
#     Limit 1000, Requested 2048 ... reduce max_tokens
#
# Not a rate limit that backing off would clear -- a request for more than
# the per-minute budget can never succeed, however long you wait. It took
# out the synthesis half of the evaluation and backend/tests/test_api.py
# with it, and read as flakiness because 429 usually means "try later".
#
# 800 leaves headroom under the limit and is far more than an answer needs:
# the citations are assembled in code from the retrieved chunks, so the model
# writes only the prose, and the prompt asks for a short plain-language
# reply. Raise it with CIVICCONNECT_MAX_ANSWER_TOKENS on a paid tier.
MAX_ANSWER_TOKENS = int(os.getenv("CIVICCONNECT_MAX_ANSWER_TOKENS", "800"))


def _act_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower()).removeprefix("the")


def cited_chunks(answer: str, retrieved_chunks: list) -> list:
    """Narrow the citations to the provisions the answer actually relies on.

    Every retrieved chunk used to be returned as a citation. That made the
    citation list a copy of the retrieval list, with two consequences.

    For the evaluation, "was every cited section among those retrieved" was
    true by construction, so the groundedness figure was 100% whatever the
    model did -- a tautology reported as a result. And "did the answer cite
    the right section" measured recall again under a different name.

    For the reader it was worse. The answer rests on one or two provisions
    and the interface listed up to ten "Sources", so the citation that
    actually backs the claim sat among nine that did not. The point of
    showing a citation is that someone can check the sentence against it;
    ten of them check nothing.

    The prompt already requires the answer to name the Act and Section it
    relies on, so the answer itself says which chunks were used. This reads
    that back, using the same parser the verification agent uses rather than
    a second copy of it -- the two drifting apart is exactly how the
    tokenizer bug happened.

    Where several Acts share a section number, the ones whose Act is also
    named in the answer win. Where the answer names no section at all --
    welfare scheme answers have no sections, and a refusal cites nothing --
    every retrieved chunk is returned, because showing the sources that were
    searched is better than showing none.
    """
    if not retrieved_chunks:
        return []

    numbers = set(extract_section_numbers(answer or ""))
    if not numbers:
        return list(retrieved_chunks)

    matched = [
        chunk for chunk in retrieved_chunks
        if normalise_section(chunk.get("section")) in numbers
    ]
    if not matched:
        return list(retrieved_chunks)

    answer_key = _act_key(answer)
    named = [c for c in matched if _act_key(c.get("act", "")) in answer_key]
    return named or matched


class SynthesisAgent:
    """
    Generates grounded answers from retrieved CivicConnect chunks.
    """

    def __init__(
        self,
        model=None
    ):
        api_key = os.getenv("GROQ_API_KEY")

        # Check this ourselves rather than letting the Groq client fail deep
        # inside its own stack, so the message says what to do about it.
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add a "
                "key from https://console.groq.com"
            )

        self.client = Groq(api_key=api_key)

        # Configurable so the model can be swapped without a code change, and
        # so the report can state which one produced the evaluation numbers.
        # Groq retires model IDs on a schedule, and a retired ID turns every
        # /query into a 500. llama-3.3-70b-versatile, the previous default here,
        # was shut down on 2026-08-16. If synthesis starts failing with a 404
        # saying `model_not_found`, this ID has been retired too — see the
        # GROQ_MODEL block in .env.example for how to list what a key can serve.
        #
        # qwen3.8-27b is the default because the answer formatting above was
        # written and checked against it. openai/gpt-oss-120b is the other
        # verified option and needs no code change, just GROQ_MODEL in .env.
        # Whichever produces the Phase E numbers has to be named in the report:
        # the figures are not reproducible without it.
        self.model = model or os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

    def synthesize(self, query, retrieved_chunks):
        """
        Generate an answer using only the retrieved chunks.
        """

        if not retrieved_chunks:
            return {
                "answer": "The available sources do not contain enough information to answer this question.",
                "citations": []
            }

        context = "\n\n".join(
            [
                (
                    f"Source: {chunk['act']}, "
                    f"Section: {chunk['section']}\n"
                    f"{chunk['text']}"
                )
                for chunk in retrieved_chunks
            ]
        )

        prompt = f"""
You are CivicConnect. You explain Indian law and government schemes to ordinary
citizens — not to lawyers.

Picture who is asking. Someone who finished school, does not work in law, and
has a real problem right now. They want to know what applies to them and what
to do next. They did not come here for a legal briefing.

ACCURACY — this comes first, always:
- Use ONLY the provided context. Never add law you know from elsewhere.
- Never invent an Act, section, penalty, amount, deadline or date.
- If the context does not answer the question, say so plainly: "The sources I
  have do not cover this." Do not fill the gap from memory.
- Name the Act and Section you are relying on. This is what lets someone check
  you, so it is not optional — but it belongs inside a normal sentence, not as
  a heading.

HOW TO WRITE IT:

1. Lead with the answer. One short sentence, first line, no preamble. If
   someone asks how long an authority has to reply, the first line is "You
   should get a reply within 30 days." Not an "Overview" heading, not a
   restatement of the question.

2. Then explain, in everyday words:
   - Short sentences. One idea each.
   - Say "must" not "is legally mandated". Say "ask for" not "submit a
     request for". Say "reply" not "furnish a response".
   - Write to the person as "you", about what they can do.
   - If a legal term is unavoidable, explain it the first time in brackets:
     "the PIO (the officer in charge of answering information requests)".
   - No headings like "Legal Basis" or "Key Provisions". Say "This comes from
     Section 7 of the Right to Information Act, 2005."

3. Keep it short. Three to six sentences for a simple question. Use bullets
   only for a genuine list — documents to bring, steps to follow, amounts.
   When you do use bullets, put each on its own line and bold the label:
   "- **Aadhaar card**: proof of who you are".

4. Use a heading only when the answer really has several parts, such as a
   scheme with eligibility and an application process. Then make headings
   plain questions: "### Who can apply" and "### How to apply", never
   "### Eligibility Criteria".

5. If the sources only partly answer, give what you have and say what is
   missing in one plain sentence at the end: "These sources do not say what
   happens for urgent cases involving someone's life or liberty."

Write it the way you would explain it out loud to a friend who asked — accurate
and careful, but in words they would actually use.

User question:
{query}

Retrieved context:
{context}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=MAX_ANSWER_TOKENS
        )

        answer = response.choices[0].message.content

        citations = [
            {
                "chunk_id": chunk["chunk_id"],
                "act": chunk["act"],
                "section": chunk["section"],
                "jurisdiction": chunk["jurisdiction"],
                "source_url": chunk["source_url"],
                "reference_url": chunk.get("reference_url"),
                # Carry the retriever diagnostics through. The hybrid retriever
                # attaches these; without them the API cannot show how a source
                # was found, and the Phase E comparison has nothing to measure.
                "_retrieval_scores": chunk.get("_retrieval_scores"),
                "_rrf_score": chunk.get("_rrf_score"),
            }
            for chunk in cited_chunks(answer, retrieved_chunks)
        ]

        return {
            "answer": answer,
            "citations": citations
        }
