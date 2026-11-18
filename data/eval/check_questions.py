"""Check the question set before trusting any number it produces.

Two failures would quietly invalidate the whole evaluation, and neither is
visible by reading the questions:

1. An expected answer that is not in the corpus. The question can then never be
   scored correct, and the arm looks worse than it is. This is easy to cause by
   mistyping an Act name or naming a section that was removed.

2. Questions written in the corpus's own vocabulary. If a question reuses the
   words of the chunk that answers it, retrieval succeeds on lexical overlap
   and the score measures nothing. This matters here specifically: the question
   set was written by someone who had read the corpus, so the bias is expected
   rather than hypothetical, and the honest response is to measure it.

The second check is the reason the report can say the retrieval numbers are not
an artefact of shared wording. Run it, quote the figure.

    python -m data.eval.check_questions
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

QUESTIONS_PATH = Path(__file__).resolve().parent / "questions.json"

# Words too common to say anything about whether a question echoes a chunk.
STOPWORDS = set(
    "a an the is are was were be been being of to in on at for with and or not no "
    "do does did i my me we our you your it its this that these those can could "
    "should would will shall may if what when where who whom how why there here "
    "from by as but any some all have has had been about into out up down".split()
)


def content_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOPWORDS and len(w) > 2}


def norm_act(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower()).removeprefix("the")


# One implementation, shared with the verification agent. See the note in
# run_eval.py: this function existed in three places at once.
from backend.agents.verification import normalise_section as norm_section  # noqa: E402


def main() -> int:
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))

    from data.db.database import SessionLocal
    from data.db.models import Chunk

    db = SessionLocal()
    try:
        chunks = [
            {"act": c.act, "section": c.section, "text": c.text}
            for c in db.query(Chunk).all()
        ]
    finally:
        db.close()

    if not chunks:
        print("The chunks table is empty. Load the corpus first.")
        return 1

    answerable = [q for q in questions if q.get("answerable", True)]
    print(f"{len(questions)} questions: {len(answerable)} answerable, "
          f"{len(questions) - len(answerable)} deliberately not")
    print(f"{len(chunks)} chunks in the corpus")
    print()

    # --- 1. every expected answer must exist -----------------------------
    failures: list[str] = []
    targets: dict[str, list[dict]] = {}

    for q in answerable:
        hits = [
            c for c in chunks
            if norm_section(c["section"]) == norm_section(q["expected_section"])
            and (
                norm_act(q["expected_act"]) in norm_act(c["act"])
                or norm_act(c["act"]) in norm_act(q["expected_act"])
            )
        ]
        if hits:
            targets[q["id"]] = hits
        else:
            failures.append(
                f"  {q['id']}: nothing in the corpus matches "
                f"{q['expected_act']!r} {q['expected_section']!r}"
            )

    print("expected answers present in the corpus:")
    if failures:
        print("\n".join(failures))
        print(f"  {len(failures)} unscoreable question(s)")
    else:
        print("  all of them")
    print()

    # --- 2. how much does a question echo its own answer? ----------------
    scored = []
    for q in answerable:
        if q["id"] not in targets:
            continue
        qw = content_words(q["question"])
        if not qw:
            continue
        best = max(len(qw & content_words(c["text"])) / len(qw) for c in targets[q["id"]])
        scored.append((best, q["id"], q["question"]))

    scored.sort(reverse=True)
    values = [s[0] for s in scored]
    mean = sum(values) / len(values)
    median = sorted(values)[len(values) // 2]

    print("lexical overlap between each question and the chunk that answers it:")
    print(f"  mean    {mean:.1%}")
    print(f"  median  {median:.1%}")
    print(f"  max     {max(values):.1%}")
    print()
    print("  highest, i.e. most at risk of being winnable on shared wording:")
    for v, qid, text in scored[:5]:
        print(f"    {v:5.0%}  {qid}  {text[:64]}")
    print()
    print("  A question scoring high here may be retrieved on word matching alone.")
    print("  Rewrite it in different words rather than deleting it -- the topic is")
    print("  usually worth keeping, the phrasing is not.")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
