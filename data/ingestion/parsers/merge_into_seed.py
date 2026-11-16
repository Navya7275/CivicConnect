"""Merge generated statute chunks into seed_chunks.json.

Usage:
    python -m data.ingestion.parsers.merge_into_seed [--dry-run]

Appends the chunk files in SOURCES to data/ingestion/seed_chunks.json,
skipping any chunk_id already there, so running it twice changes nothing.

WHY THIS IS NOT ALREADY DONE
----------------------------
seed_chunks.json and the index artifacts under data/indexing/artifacts/ are
both tracked, and build_index writes a fingerprint of the corpus into the
index. Change the corpus without rebuilding, and the fingerprint stops
matching: BM25Retriever then refuses to load, which is correct, because
keyword search against a stale index returns wrong results silently rather
than failing.

So the two have to move in one commit. Building the index needs the
sentence-transformers model, which downloads from huggingface.co -- not
reachable from the cloud session these chunks were generated in. Leaving the
corpus merged there would have handed you a branch where pytest fails and a
fresh clone cannot start.

Run the sequence below on a machine with network access and commit the
result; that keeps the corpus and the index consistent in every commit.

    python -m data.ingestion.parsers.merge_into_seed
    python -m data.ingestion.load_seed
    python -m data.ingestion.validate
    python -m data.indexing.build_index
    python -m pytest -q

Once that lands, this script and data/ingestion/parsers/generated/ have done
their job and can be deleted -- seed_chunks.json becomes the single copy.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = HERE.parent / "seed_chunks.json"

SOURCES = [
    HERE / "generated" / "bns2023_chunks.json",
    HERE / "generated" / "mvact1988_chunks.json",
]

NEXT_STEPS = """
Next, in this order, then commit seed_chunks.json and the rebuilt artifacts
together:

    python -m data.ingestion.load_seed
    python -m data.ingestion.validate
    python -m data.indexing.build_index
    python -m pytest -q

build_index is the one that matters: it rewrites the corpus fingerprint the
BM25 index is checked against. Committing seed_chunks.json without it leaves
the branch unable to start.
"""


def main(argv):
    dry_run = "--dry-run" in argv

    seed = json.loads(SEED.read_text(encoding="utf-8"))
    existing = {c["chunk_id"] for c in seed}
    before = len(seed)

    added, skipped = 0, 0
    for source in SOURCES:
        if not source.exists():
            raise SystemExit(
                f"missing {source}\n"
                "Regenerate it with:\n"
                "    python -m data.ingestion.parsers.build_chunks "
                "<bns|mvact> <parsed.json> <out.json>")
        for chunk in json.loads(source.read_text(encoding="utf-8")):
            if chunk["chunk_id"] in existing:
                skipped += 1
                continue
            existing.add(chunk["chunk_id"])
            seed.append(chunk)
            added += 1

    print(f"existing : {before}")
    print(f"added    : {added}")
    print(f"skipped  : {skipped} (already present)")
    print(f"total    : {len(seed)}")

    if dry_run:
        print("\n--dry-run: seed_chunks.json not written")
        return

    SEED.write_text(json.dumps(seed, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(f"written  : {SEED}")
    print(NEXT_STEPS)


if __name__ == "__main__":
    main(sys.argv)
