# Phase E — the evaluation

Turns three claims into numbers: that hybrid retrieval beats dense alone, that
answers are grounded in real sources, and that the verification agent catches
the ones that are not.

## Running it

The index must exist first. If `data/indexing/artifacts/` is empty:

```bash
python -m data.ingestion.load_seed
python -m data.ingestion.load_welfare
python -m data.indexing.build_index
```

Then:

```bash
python -m data.eval.run_eval                 # all three arms
python -m data.eval.run_eval --no-synthesis  # retrieval only, no API key needed
python -m data.eval.run_eval --limit 8 --out results.json
```

`--no-synthesis` is the fast loop while tuning retrieval. It needs no network
and no key, and still reports recall@k.

## What it measures

| metric | question it answers |
|---|---|
| **recall@k** | did retrieval return the chunk that answers the question at all |
| **citation correctness** | did the answer cite the section that answers it |
| **citation groundedness** | was every cited section actually among the retrieved chunks |
| **refusal correctness** | for questions the corpus cannot answer, did it decline |

Recall and citation accuracy are reported separately on purpose. High recall
with low citation accuracy means synthesis is misusing chunks it was given; low
recall means retrieval never gave it a chance. Different problems, different
fixes, and a single combined score hides which one you have.

## The question set

`questions.json`, one entry per question:

```json
{
  "id": "rti-07",
  "question": "I asked a government office for records two months ago and they haven't replied. Is that allowed?",
  "expected_act": "Right to Information Act, 2005",
  "expected_section": "Section 7",
  "answerable": true
}
```

`expected_section` is the ground truth. Without it there is nothing to score
against and the exercise collapses into reading answers and forming
impressions.

A deliberate slice carries `answerable: false` — questions the corpus genuinely
cannot answer. Those test whether the system says so instead of inventing, which
is the behaviour the whole project rests on.

### Two things that would invalidate the numbers

**Questions written in the corpus's own vocabulary.** If a question reuses the
exact words of the chunk that answers it, retrieval succeeds on lexical overlap
and the score measures nothing. This is not hypothetical: the tokenizer bug in
#30 only surfaced because a real question ended in a question mark. Questions
phrased the way people actually speak are the point.

**A moving corpus.** Every chunk added or removed changes what the numbers mean.
Record the corpus size, the `GROQ_MODEL` and the index build alongside any
result — figures without them are not reproducible, and Groq has already
retired one model mid-project.

## Status

The harness is written. The question set is not yet, and must be written against
the 57 real statutory chunks — not the 147 the corpus appeared to hold before
the 90 generated-filler chunks were removed in #41.
