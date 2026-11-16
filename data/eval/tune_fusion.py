"""Sweep RRF settings against the question set and print what each scores.

    python -m data.eval.tune_fusion

WHY
---
Hybrid retrieval currently scores below dense alone on every body of law in
the corpus:

    body of law                dense     bm25   hybrid
    Welfare schemes             100%      84%     100%
    Consumer Protection          78%      50%      75%
    Bharatiya Nyaya Sanhita      64%      14%      59%
    Right to Information         64%      29%      43%
    Motor Vehicles Act           78%      28%      50%

That is not a tuning accident, it is arithmetic. A chunk contributes
weight/(k + rank) from each list it appears in, and with k=60 and a
50-candidate pool:

    dense ranks it #1, bm25 never finds it : 1/61  = 0.016393
    both retrievers rank it last (#50)     : 2/110 = 0.018182

Every chunk the two agree on outranks every chunk only one found. Fusion
becomes "intersection first", so when bm25 is 14% accurate on criminal law it
pulls dense down with it.

HOW
---
Retrieval runs once per question and the ranked lists are cached; the sweep
then re-fuses those cached lists for every setting, which costs nothing. So
the run takes about as long as one evaluation pass, not one per setting.

Report the whole table, not just the winner. A setting that wins overall
while losing badly on one body of law is worth knowing about, and the shape
of the sweep says more than its maximum -- if recall climbs steadily as the
dense weight rises, the honest conclusion may be that the bm25 arm is not
earning its place at all.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.retrieval.bm25 import BM25Retriever          # noqa: E402
from backend.retrieval.data_loader import load_chunks_from_database  # noqa: E402
from backend.retrieval.dense import DenseRetriever        # noqa: E402
from backend.retrieval.fusion import reciprocal_rank_fusion  # noqa: E402
from data.eval.check_questions import norm_act, norm_section  # noqa: E402

QUESTIONS = Path(__file__).resolve().parent / "questions.json"

CANDIDATES = 50          # what HybridRetriever asks each arm for at limit=10
LIMIT = 10               # recall@10

K_VALUES = [5, 10, 20, 40, 60]
DENSE_WEIGHTS = [1.0, 1.5, 2.0, 3.0, 5.0]

STATUTES = ("Bharatiya Nyaya Sanhita", "Motor Vehicles Act",
            "Consumer Protection Act", "Right to Information")


def body_of_law(act: str) -> str:
    return next((s for s in STATUTES if s in act), "Welfare schemes")


def answers(question, chunk) -> bool:
    return (
        norm_section(chunk["section"]) == norm_section(question["expected_section"])
        and (norm_act(question["expected_act"]) in norm_act(chunk["act"])
             or norm_act(chunk["act"]) in norm_act(question["expected_act"]))
    )


def main() -> int:
    questions = [q for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))
                 if q.get("answerable", True)]
    chunks = load_chunks_from_database()
    print(f"{len(questions)} answerable questions, {len(chunks)} chunks")

    bm25 = BM25Retriever(chunks)
    dense = DenseRetriever(chunks)

    print("retrieving once per question (the slow part)...", flush=True)
    cached = []
    for q in questions:
        cached.append((
            q,
            bm25.search(q["question"], limit=CANDIDATES),
            dense.search(q["question"], limit=CANDIDATES),
        ))

    def recall(k, w_dense, by_act=False):
        hits, per_act = 0, {}
        for q, b, d in cached:
            fused = reciprocal_rank_fusion([b, d], k=k, limit=LIMIT,
                                           weights=[1.0, w_dense])
            hit = any(answers(q, c) for c in fused)
            hits += hit
            if by_act:
                per_act.setdefault(body_of_law(q["expected_act"]), []).append(hit)
        return (hits, len(cached), per_act)

    print()
    print("recall@10, rows are k, columns are the weight on the dense arm")
    print("(weight 1.0 on bm25 throughout; k=60 w=1.0 is what ships today)")
    print()
    print("  " + "k".ljust(6) + "".join(f"{f'x{w:g}':>12}" for w in DENSE_WEIGHTS))
    print("  " + "-" * (6 + 12 * len(DENSE_WEIGHTS)))

    best = (-1, None)
    for k in K_VALUES:
        cells = ""
        for w in DENSE_WEIGHTS:
            hits, total, _ = recall(k, w)
            pct = 100 * hits / total
            cells += f"{f'{pct:.0f}% ({hits})':>12}"
            if hits > best[0]:
                best = (hits, (k, w))
        print("  " + str(k).ljust(6) + cells)

    hits, total, _ = recall(60, 1.0)
    print(f"\n  shipping today      k=60  dense x1    : {100*hits/total:.0f}% ({hits}/{total})")

    bk, bw = best[1]
    bh, bt, per_act = recall(bk, bw, by_act=True)
    print(f"  best in this sweep  k={bk:<3} dense x{bw:<4g}: {100*bh/bt:.0f}% ({bh}/{bt})")
    print()
    print("  best setting, by body of law:")
    for label in sorted(per_act, key=lambda x: -len(per_act[x])):
        v = per_act[label]
        print(f"    {label:<26} {100*sum(v)/len(v):>3.0f}% ({sum(v)}/{len(v)})")
    print()
    print("  Compare each row against the dense-only column in run_eval. If no")
    print("  setting beats dense alone, that is the finding: report it rather")
    print("  than tuning until the hybrid looks better than it is.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
