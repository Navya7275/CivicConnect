"""Phase E — measure whether hybrid retrieval and verification actually help.

The project claims three things: that hybrid retrieval beats dense alone, that
answers are grounded in real statutory sources, and that the verification agent
catches answers which are not. None of those is currently a number. This script
turns them into one.

It runs every question in `questions.json` through three arms and scores them:

    dense                 FAISS only -- semantic similarity on its own
    hybrid                FAISS + BM25 fused with RRF
    hybrid+verification   the same, with the verification agent judging the answer

What gets measured, and why these and not others:

  recall@k            Did retrieval return the chunk that answers the question
                      at all? Pure retrieval, no LLM involved, so it is cheap
                      and deterministic.

  citation correctness  Did the answer cite the section that actually answers
                      the question?

  citation groundedness Was every section the answer cited actually among the
                      retrieved chunks? This is the hallucination measure.

  refusal correctness For questions the corpus genuinely cannot answer, did the
                      system say so instead of inventing something?

Recall and citation accuracy are reported separately on purpose. If recall is
high and citation accuracy is low, synthesis is misusing chunks it was given.
If recall is low, retrieval never gave it a chance. Those have completely
different fixes, and a single combined score hides which one you have.

Running it:

    python -m data.eval.run_eval                 # all three arms
    python -m data.eval.run_eval --no-synthesis  # retrieval only, no API key needed
    python -m data.eval.run_eval --limit 8 --out results.json

`--no-synthesis` exists because retrieval metrics need no network at all. It is
the fast loop while tuning retrieval, and it still produces recall@k, which is
the number that would have caught the tokenizer bug in #30.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

EVAL_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVAL_DIR.parents[1]
QUESTIONS_PATH = EVAL_DIR / "questions.json"

# Phrases the synthesis prompt tells the model to use when the context does not
# answer the question. Matching is deliberately loose: we are asking "did it
# decline", not "did it decline in exactly these words".
REFUSAL_MARKERS = (
    "do not cover",
    "does not cover",
    "do not contain",
    "does not contain",
    "not provide enough information",
    "do not provide enough",
    "sources i have do not",
    "cannot answer",
)


def normalise_section(value: str | None) -> str | None:
    """'Section 7' / 'sec. 7' / '7' all become '7'."""
    if not value:
        return None
    m = re.search(r"(\d+[A-Z]?)", str(value), re.IGNORECASE)
    return m.group(1).upper() if m else None


def same_provision(a_act: str, a_sec: str, b_act: str, b_sec: str) -> bool:
    """Do two (act, section) pairs refer to the same provision?

    Act names are compared loosely -- "Right to Information Act, 2005" and
    "The Right to Information Act, 2005" are the same Act, and an evaluation
    that counted them as different would measure punctuation.
    """
    if normalise_section(a_sec) != normalise_section(b_sec):
        return False
    norm = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower()).removeprefix("the")
    return norm(a_act) in norm(b_act) or norm(b_act) in norm(a_act)


@dataclass
class QuestionResult:
    """What happened for one question in one arm."""

    qid: str
    answerable: bool
    # Which Act the answer lives in, so the report can break recall down by
    # body of law. The aggregate hides the only thing worth knowing: keyword
    # search scores very differently on the plain-language summaries than on
    # verbatim statute, and one number averages the two together.
    expected_act: str = ""
    retrieved: list[tuple[str, str]] = field(default_factory=list)
    recall_hit: bool = False
    cited: list[tuple[str, str]] = field(default_factory=list)
    citation_correct: bool = False
    citation_grounded: bool = True
    refused: bool = False
    verified: bool | None = None
    hallucinated_sections: list[str] = field(default_factory=list)
    error: str | None = None
    synthesis_error: str | None = None
    seconds: float = 0.0


def load_questions() -> list[dict[str, Any]]:
    if not QUESTIONS_PATH.exists():
        sys.exit(f"No question set at {QUESTIONS_PATH}")
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    if not questions:
        sys.exit("Question set is empty.")
    return questions


def load_corpus() -> list[dict[str, Any]]:
    from backend.retrieval.data_loader import load_chunks_from_database

    chunks = load_chunks_from_database()
    if not chunks:
        sys.exit(
            "The chunks table is empty. Run:\n"
            "  python -m data.ingestion.load_seed\n"
            "  python -m data.ingestion.load_welfare"
        )
    return chunks


def build_arms(chunks: list[dict[str, Any]], want: list[str]) -> dict[str, Any]:
    """Construct the retrievers, skipping any that cannot be built.

    A missing arm is reported rather than fatal: retrieval-only runs are useful
    on a machine that cannot reach the embedding model, and reporting two arms
    honestly beats refusing to run.
    """
    arms: dict[str, Any] = {}

    if "dense" in want:
        try:
            from backend.retrieval.dense import DenseRetriever

            arms["dense"] = DenseRetriever(chunks)
        except Exception as exc:  # noqa: BLE001
            print(f"  [skip] dense: {exc.__class__.__name__}: {exc}")

    if "bm25" in want:
        try:
            from backend.retrieval.bm25 import BM25Retriever

            arms["bm25"] = BM25Retriever(chunks)
        except Exception as exc:  # noqa: BLE001
            print(f"  [skip] bm25: {exc.__class__.__name__}: {exc}")

    if "hybrid" in want or "hybrid+verification" in want:
        try:
            from backend.retrieval.hybrid_search import HybridRetriever

            hybrid = HybridRetriever(chunks)
            if "hybrid" in want:
                arms["hybrid"] = hybrid
            if "hybrid+verification" in want:
                arms["hybrid+verification"] = hybrid
        except Exception as exc:  # noqa: BLE001
            print(f"  [skip] hybrid: {exc.__class__.__name__}: {exc}")

    return arms


def as_chunk(item: Any) -> dict[str, Any]:
    """Retrievers return either a chunk dict or {'chunk': ..., 'score': ...}."""
    if isinstance(item, dict) and "chunk" in item and isinstance(item["chunk"], dict):
        return item["chunk"]
    return item


def run_one(
    question: dict[str, Any],
    arm_name: str,
    retriever: Any,
    synthesizer: Any | None,
    verifier: Any | None,
    limit: int,
) -> QuestionResult:
    """Score one question in one arm.

    Retrieval and synthesis fail independently, and are recorded that way.

    An earlier version wrapped both in a single handler, so a rate limit from
    Groq discarded the retrieval result that had already been computed. A run
    that hit limits on 64 of 77 questions then reported recall over the 13
    that survived, as a bare percentage, with nothing to indicate the
    denominator -- bm25 showed 100% over ten questions. Recall@k needs no LLM;
    it must never be lost to one.
    """
    res = QuestionResult(
        qid=question["id"],
        answerable=question.get("answerable", True),
        expected_act=question.get("expected_act", ""),
    )
    started = time.perf_counter()

    # --- retrieval: no network, no LLM, always attempted ------------------
    try:
        raw = retriever.search(question["question"], limit=limit)
        chunks = [as_chunk(r) for r in raw]
        res.retrieved = [(c.get("act", ""), c.get("section", "")) for c in chunks]

        if res.answerable:
            res.recall_hit = any(
                same_provision(a, s, question["expected_act"], question["expected_section"])
                for a, s in res.retrieved
            )
    except Exception as exc:  # noqa: BLE001
        res.error = f"{exc.__class__.__name__}: {exc}"
        res.seconds = time.perf_counter() - started
        return res

    if synthesizer is None:
        res.seconds = time.perf_counter() - started
        return res

    # --- synthesis: needs the provider, and may fail on its own -----------
    try:
        out = None
        for attempt in range(5):
            try:
                out = synthesizer.synthesize(question["question"], chunks)
                break
            except Exception as exc:  # noqa: BLE001
                rate_limited = (
                    "rate" in exc.__class__.__name__.lower() or "429" in str(exc)
                )
                if not rate_limited or attempt == 4:
                    raise
                wait = 2 ** attempt * 5
                print(f"\n    rate limited, waiting {wait}s", flush=True)
                time.sleep(wait)

        if out is None:
            raise RuntimeError("synthesis returned nothing after retries")

        answer = out.get("answer") or ""
        citations = out.get("citations") or []

        res.refused = any(m in answer.lower() for m in REFUSAL_MARKERS)
        res.cited = [(c.get("act", ""), c.get("section", "")) for c in citations]

        if res.answerable:
            res.citation_correct = any(
                same_provision(a, s, question["expected_act"], question["expected_section"])
                for a, s in res.cited
            )

        retrieved_keys = {(normalise_section(s), (a or "").lower()) for a, s in res.retrieved}
        res.citation_grounded = all(
            (normalise_section(s), (a or "").lower()) in retrieved_keys for a, s in res.cited
        )

        if verifier is not None:
            v = verifier.verify(answer, citations, chunks)
            res.verified = v.verified
            res.hallucinated_sections = list(v.hallucinated_sections)

    except Exception as exc:  # noqa: BLE001
        res.synthesis_error = f"{exc.__class__.__name__}: {exc}"

    res.seconds = time.perf_counter() - started
    return res


def pct(n: int, d: int) -> str:
    return f"{100.0 * n / d:5.1f}%" if d else "    --"


def frac(n: int, d: int) -> str:
    """A percentage that always carries its denominator.

    A bare "100.0%" over ten questions reads identically to one over seventy,
    and that is how a rate-limited run came to look like a clean result. Every
    figure here says what it is over.
    """
    return f"{100.0 * n / d:.0f}% ({n}/{d})" if d else "--"


def recall_by_act(results: dict[str, list[QuestionResult]]) -> None:
    """Break recall down by the Act the answer lives in.

    The single figure averages two different problems together. The Consumer
    Protection and RTI chunks are condensed summaries written in ordinary
    language, so a question shares vocabulary with them; the Bharatiya Nyaya
    Sanhita and Motor Vehicles Act chunks are verbatim statute, where it does
    not. "Someone took my phone out of my bag on a bus" and "Whoever,
    intending to take dishonestly any movable property out of the possession
    of any person without that person's consent" have almost no words in
    common, which is survivable for dense retrieval and close to fatal for
    BM25.

    Reported separately, that difference is the result. Averaged, it is
    invisible.
    """
    arms = list(results)
    acts: dict[str, dict[str, list[bool]]] = {}
    for arm, rows in results.items():
        for r in rows:
            if not r.answerable or r.error or not r.expected_act:
                continue
            acts.setdefault(r.expected_act, {}).setdefault(arm, []).append(r.recall_hit)

    if len(acts) < 2:
        return

    # Welfare schemes are one chunk each and there are a lot of them; group
    # them together rather than printing twenty rows of n=1.
    STATUTES = ("Bharatiya Nyaya Sanhita", "Motor Vehicles Act",
                "Consumer Protection Act", "Right to Information")
    grouped: dict[str, dict[str, list[bool]]] = {}
    for act, per_arm in acts.items():
        label = next((s for s in STATUTES if s in act), "Welfare schemes")
        for arm, hits in per_arm.items():
            grouped.setdefault(label, {}).setdefault(arm, []).extend(hits)

    width = max(len(k) for k in grouped) + 2
    print()
    print("  recall@k by body of law")
    print()
    print("  " + "".ljust(width) + "".join(f"{a:>22}" for a in arms))
    print("  " + "-" * (width + 22 * len(arms)))
    for label in sorted(grouped, key=lambda k: -len(grouped[k].get(arms[0], []))):
        cells = ""
        for arm in arms:
            hits = grouped[label].get(arm, [])
            cells += f"{frac(sum(hits), len(hits)):>22}" if hits else f"{'-':>22}"
        print("  " + label.ljust(width) + cells)


def report(results: dict[str, list[QuestionResult]], synthesis_ran: bool) -> None:
    print()
    print("=" * 78)
    print("PHASE E RESULTS")
    print("=" * 78)
    print()
    print("RETRIEVAL  (no LLM involved, so these are always complete)")
    print()
    print(f"  {'arm':<22} {'recall@k':>16} {'failed':>8}")
    print(f"  {'-' * 48}")

    for arm, rows in results.items():
        ok = [r for r in rows if r.answerable and not r.error]
        print(f"  {arm:<22} {frac(sum(r.recall_hit for r in ok), len(ok)):>16} "
              f"{sum(1 for r in rows if r.error):>8}")

    recall_by_act(results)

    if not synthesis_ran:
        print()
        print("  Synthesis was not run, so citation and refusal metrics are absent.")
        print("  recall@k: did retrieval return the chunk that answers the question.")
        return

    print()
    print("ANSWERS  (needs the LLM; questions it could not reach are excluded)")
    print()
    print(f"  {'arm':<22} {'cited right':>16} {'grounded':>16} {'refused':>14} {'lost':>6}")
    print(f"  {'-' * 78}")

    starved = False
    for arm, rows in results.items():
        done = [r for r in rows if not r.error and not r.synthesis_error]
        ans = [r for r in done if r.answerable]
        una = [r for r in done if not r.answerable]
        lost = sum(1 for r in rows if r.synthesis_error)
        if len(done) < 0.8 * len(rows):
            starved = True
        print(f"  {arm:<22} {frac(sum(r.citation_correct for r in ans), len(ans)):>16} "
              f"{frac(sum(r.citation_grounded for r in done), len(done)):>16} "
              f"{frac(sum(r.refused for r in una), len(una)):>14} {lost:>6}")

    if starved:
        print()
        print("  WARNING: an arm answered fewer than 80% of its questions. Those")
        print("  percentages are over whatever got through, which is not a result.")
        print("  Re-run with a larger --sleep, or use --no-synthesis for retrieval")
        print("  metrics alone, which need no provider and are always complete.")

    if "hybrid+verification" in results:
        rows = [r for r in results["hybrid+verification"] if not r.error and not r.synthesis_error]
        flagged = [r for r in rows if r.verified is False]
        hallucinated = [r for r in rows if r.hallucinated_sections]
        print()
        print(f"  verification flagged {len(flagged)} of {len(rows)} answers as ungrounded")
        print(f"  prose named a section that was not retrieved in {len(hallucinated)}")
        for r in hallucinated[:5]:
            print(f"      {r.qid}: {', '.join(r.hallucinated_sections)}")

    errs: dict[str, int] = {}
    for rows in results.values():
        for r in rows:
            if r.synthesis_error:
                errs[r.synthesis_error.split(":")[0]] = errs.get(r.synthesis_error.split(":")[0], 0) + 1
    if errs:
        print()
        print("  synthesis failures by type:")
        for name, n in sorted(errs.items(), key=lambda kv: -kv[1]):
            print(f"      {n:4}  {name}")

    times = [r.seconds for rows in results.values() for r in rows]
    if times:
        print()
        print(f"  median {statistics.median(times):.1f}s per question, {len(times)} runs")

    print()
    print("  recall@k     did retrieval return the chunk that answers the question")
    print("  cited right  did the answer cite the section that answers it")
    print("  grounded     was every cited section actually among those retrieved")
    print("  refused      for unanswerable questions, did it correctly decline")


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase E evaluation")
    ap.add_argument("--limit", type=int, default=5, help="chunks retrieved per question (k)")
    ap.add_argument(
        "--arms",
        default="dense,bm25,hybrid,hybrid+verification",
        help="comma-separated subset of arms to run",
    )
    ap.add_argument(
        "--no-synthesis",
        action="store_true",
        help="retrieval metrics only; needs no API key and no network",
    )
    ap.add_argument("--out", help="write full per-question results to this JSON file")
    ap.add_argument(
        "--sample",
        type=int,
        help=(
            "run only this many answerable questions, keeping every unanswerable "
            "one. Use it for the synthesis arms on a rate-limited tier: the full "
            "set is 308 LLM calls, which a free key will not serve"
        ),
    )
    ap.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="seconds to pause between questions; use ~2 on a rate-limited free tier",
    )
    args = ap.parse_args()

    os.chdir(REPO_ROOT)
    want = [a.strip() for a in args.arms.split(",") if a.strip()]

    questions = load_questions()

    if args.sample:
        # Keep every unanswerable question and evenly space the answerable ones.
        #
        # Evenly spaced rather than random so the sample is the same on every
        # run and the numbers are comparable, and because questions.json is
        # ordered by act and then by section -- taking the first N would test
        # only the RTI Act.
        #
        # The unanswerable ones are always kept: there are only eight, they
        # cost one call each, and refusal correctness is the one synthesis
        # metric that is not partly a restatement of recall.
        answerable_qs = [q for q in questions if q.get("answerable", True)]
        unanswerable_qs = [q for q in questions if not q.get("answerable", True)]
        n = min(args.sample, len(answerable_qs))
        step = len(answerable_qs) / n
        picked = [answerable_qs[int(i * step)] for i in range(n)]
        questions = picked + unanswerable_qs
        print(f"sampling {n} of {len(answerable_qs)} answerable, plus all "
              f"{len(unanswerable_qs)} unanswerable")

    answerable = sum(1 for q in questions if q.get("answerable", True))
    print(f"{len(questions)} questions ({answerable} answerable, {len(questions) - answerable} not)")

    chunks = load_corpus()
    print(f"{len(chunks)} chunks in the corpus")

    arms = build_arms(chunks, want)
    if not arms:
        artifacts = REPO_ROOT / "data" / "indexing" / "artifacts"
        built = (artifacts / "faiss.index").exists()
        sys.exit(
            "No arm could be constructed.\n"
            + (
                "  The index exists, so the reason is above -- most likely the embedding\n"
                "  model could not be loaded. It downloads from huggingface.co on first\n"
                "  use and is cached afterwards, so this machine needs network access once."
                if built
                else "  The index is missing. Build it:\n    python -m data.indexing.build_index"
            )
        )

    synthesizer = verifier = None
    if not args.no_synthesis:
        try:
            from backend.agents.synthesis import SynthesisAgent

            synthesizer = SynthesisAgent()
        except Exception as exc:  # noqa: BLE001
            print(f"  [skip] synthesis: {exc.__class__.__name__}: {exc}")
            print("         running retrieval metrics only; set GROQ_API_KEY for the rest")
    if synthesizer is not None:
        from backend.agents.verification import VerificationAgent

        verifier = VerificationAgent()

    print(f"arms: {', '.join(arms)}")
    print()

    results: dict[str, list[QuestionResult]] = {}
    for arm_name, retriever in arms.items():
        use_verifier = verifier if arm_name == "hybrid+verification" else None
        rows = []
        for i, q in enumerate(questions, 1):
            rows.append(run_one(q, arm_name, retriever, synthesizer, use_verifier, args.limit))
            print(f"\r  {arm_name}: {i}/{len(questions)}", end="", flush=True)
            if args.sleep and synthesizer is not None and i < len(questions):
                time.sleep(args.sleep)
        print()
        results[arm_name] = rows

    report(results, synthesis_ran=synthesizer is not None)

    if args.out:
        payload = {
            "k": args.limit,
            "questions": len(questions),
            "corpus_chunks": len(chunks),
            "model": os.getenv("GROQ_MODEL", "(default)"),
            "synthesis_ran": synthesizer is not None,
            "arms": {
                arm: [vars(r) for r in rows] for arm, rows in results.items()
            },
        }
        Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nfull results written to {args.out}")
        print("Record the GROQ_MODEL and the index's corpus fingerprint alongside")
        print("these numbers -- they are not reproducible without both.")


if __name__ == "__main__":
    main()
