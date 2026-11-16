"""Turn parsed statute sections into corpus chunks.

Usage:
    python -m data.ingestion.parsers.build_chunks <act-key> <parsed.json> <out.json>

act-key is "bns" or "mvact". The output matches the record shape in
data/ingestion/seed_chunks.json exactly, so it can be concatenated onto it.

CHUNK SIZE AND THE CORPUS IT JOINS
----------------------------------
The 57 chunks already in seed_chunks.json are 110 to 286 characters and are
condensed summaries rather than statute (see docs/DATA_SOURCES.md). These are
verbatim provisions, and a median BNS section is 616 characters against the
existing median of 189.

That heterogeneity is deliberate: a citation is worth nothing if the text it
points at is a paraphrase, so the new material is kept verbatim. But it does
mean the corpus is no longer uniform, and retrieval scores measured over the
57 are not comparable to scores measured after this lands. BM25 normalises
for document length, so the effect is bounded, but it is a confound and the
evaluation write-up has to say so.

Sections are split only when they exceed MAX_CHARS, and then at the
boundaries the statute itself provides -- sub-sections, Explanations,
Illustrations, Exceptions, provisos -- never mid-sentence. A fragment carries
a "Section 103(2):" style label so it is still identifiable on its own, which
is the convention the existing chunks use.

EFFECTIVE DATES
---------------
`effective_date` is not nullable, is required at load, and filters.py drops
any chunk without one, so every record needs a real date.

For the Motor Vehicles Act that date is 2026-08-15, which is what the source
states the consolidated text is current as of. It is not the Act's 1989
commencement: the text here carries the 2019 and 2023-26 amendments, and
dating it 1989 would claim that today's penalties were in force then. The
per-section "w.e.f." dates in the footnotes would be better still, but
footnotes are attached to a page rather than a section, so where a page spans
two sections they attach to the wrong one -- only 79 of 257 sections carry
one and s.185 is not among them. Per-section dating needs that fixed first.

The BNS dates are not in its source PDF, which is a compilation without the
gazette header. They are recorded here from the Act's publication rather than
from the document, and docs/DATA_SOURCES.md says so.
"""

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_CHARS = 1500      # above this a section is split
MIN_CHARS = 120       # below this a fragment is merged back

ACTS = {
    "bns": {
        "name": "Bharatiya Nyaya Sanhita, 2023",
        "slug": "bns2023",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/20062",
        "assent_date": "2023-12-25",
        "effective_date": "2024-07-01",
        # verify_provenance accepts only {html, pdf, api, manual}; which
        # PDF edition this came from is recorded in docs/DATA_SOURCES.md
        # and in the parser docstring, not squeezed into this field.
        "extraction_method": "pdf",
    },
    "mvact": {
        "name": "Motor Vehicles Act, 1988",
        "slug": "mvact1988",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/1798",
        "assent_date": "1988-10-14",
        "effective_date": "2026-08-15",
        "extraction_method": "pdf",
    },
}

REVIEWER = "Navya Singhal"

# Where a long section may be divided. Each is a boundary the drafter put
# there, so splitting on one never cuts a sentence in half.
SUBSECTION = re.compile(r"(?=(?<![\w(])\(\d{1,2}[A-Z]?\)\s)")
SUBDIVISION = re.compile(
    r"(?=(?:Explanation|Illustrations?|Exception|Provided (?:further |also )?that)\b)")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def strip_heading(piece: str, section: str, title: str) -> str:
    """Remove the section number, and the title where the body repeats it.

    The two Acts print their headings differently. BNS gives the number alone
    ("303. (1) Whoever, intending to take..."), while the Motor Vehicles Act
    repeats the title after it ("110. Power of Central Government to make
    rules.—(1) ..."). Since every chunk is labelled with its title already,
    leaving the second form alone produced "Section 110: Power of Central
    Government to make rules. Power of Central Government to make rules. ...".
    """
    body = re.sub(rf"^\[?\s*{re.escape(section)}\.\s*", "", piece).strip()
    # The title may carry amendment brackets or a trailing em-dash.
    pattern = rf"^\d*\s*\[?\s*{re.escape(title)}\.?\]?\s*[—\-:]?\s*"
    body = re.sub(pattern, "", body, count=1, flags=re.IGNORECASE).strip()
    return body


def _merge(parts):
    """Join neighbouring fragments up to MAX_CHARS.

    Splitting at every sub-section would give one-line chunks with no context,
    which retrieve badly and read worse.
    """
    merged = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if merged and len(merged[-1]) + len(part) + 1 <= MAX_CHARS:
            merged[-1] += " " + part
        else:
            merged.append(part)
    if len(merged) > 1 and len(merged[-1]) < MIN_CHARS:
        # Pop first: `merged[-2] += " " + merged.pop()` resolves the index
        # after the pop has already shortened the list.
        tail = merged.pop()
        merged[-1] += " " + tail
    return merged


def split_text(text: str):
    """Split an over-long section at statutory boundaries.

    Returns [(label_suffix, text)]. label_suffix is the sub-section number
    when the split fell on one, so a fragment of section 103 reads
    "Section 103(2)" rather than "part 2 of section 103".
    """
    if len(text) <= MAX_CHARS:
        return [(None, text)]

    pieces = _merge(SUBSECTION.split(text))

    # Sub-sections alone are not always enough. Defamation runs to ten
    # numbered Exceptions under a single sub-section (1), so the first pass
    # left one piece of 7,999 characters; those get divided again at the
    # Explanation / Illustration / Exception / proviso boundaries.
    refined = []
    for piece in pieces:
        if len(piece) > MAX_CHARS:
            refined.extend(_merge(SUBDIVISION.split(piece)))
        else:
            refined.append(piece)

    if len(refined) == 1:
        return [(None, refined[0])]

    # Every piece of a split section gets a suffix, including the ones that
    # do not open with a sub-section number. Leaving those bare gave the
    # Illustrations block of section 303 the id "bns2023-s303", which reads
    # as the whole section while actually sitting between -1 and -2.
    out = []
    for position, piece in enumerate(refined, 1):
        head = re.match(r"\((\d{1,2}[A-Z]?)\)", piece)
        out.append((head.group(1) if head else f"p{position}", piece))

    # A piece still over the limit has no further statutory boundary to use,
    # and cutting mid-sentence would produce a chunk that cannot be quoted.
    # Leave it long; the size report shows how many.
    return out


def build(act_key: str, parsed_path: Path):
    meta = ACTS[act_key]
    data = json.loads(parsed_path.read_text(encoding="utf-8"))
    sections = data["sections"] if isinstance(data, dict) else data
    state_amendments = data.get("state_amendments", []) if isinstance(data, dict) else []

    raw_digest = sha256(parsed_path.read_text(encoding="utf-8"))
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    chunks = []
    seen = {}
    for s in sections:
        for suffix, piece in split_text(s["text"]):
            # A positional suffix ("p2") disambiguates the chunk_id but is
            # not part of the law, so it never appears in the text a reader
            # or a retriever sees -- only a real sub-section number does.
            is_subsection = bool(suffix) and not re.fullmatch(r"p\d+", suffix)
            label = (f"Section {s['section']}({suffix})" if is_subsection
                     else f"Section {s['section']}")
            body = strip_heading(piece, s["section"], s["title"])
            if not body:
                # Nothing but the section number, which happens when the
                # first sub-section marker follows it immediately: "303. (1)
                # Whoever..." splits into "303." and "(1) Whoever...". The
                # first fragment carries no provision, so there is nothing to
                # cite and nothing to retrieve.
                continue
            text = f"{label}: {s['title']}. {body}"

            chunk_id = f"{meta['slug']}-s{s['section'].lower()}"
            if suffix:
                chunk_id += f"-{suffix.lower()}"
            # Two pieces of one section can open with the same sub-section
            # number, because a long sub-section is divided again at its
            # Explanations. Disambiguate with a letter rather than a count of
            # matching prefixes, which could itself collide.
            if chunk_id in seen:
                seen[chunk_id] += 1
                chunk_id = f"{chunk_id}{chr(ord('a') + seen[chunk_id] - 1)}"
            else:
                seen[chunk_id] = 1

            chunks.append({
                "chunk_id": chunk_id,
                "text": text,
                "act": meta["name"],
                "chapter": f"Chapter {s['chapter']}" if s.get("chapter") else "",
                "section": f"Section {s['section']}",
                "jurisdiction": "Central",
                "effective_date": meta["effective_date"],
                "assent_date": meta["assent_date"],
                "excerpt": text,
                "source_url": meta["source_url"],
                "text_sha256": sha256(text),
                "raw_sha256": raw_digest,
                "extraction_method": meta["extraction_method"],
                "reviewer_name": REVIEWER,
                "fetched_at": fetched_at,
                # No clickable link yet: the source PDFs are not in the repo,
                # so there is nothing a page anchor could point at. The page
                # number is kept here so links can be turned on later without
                # re-parsing anything.
                "reference_url": None,
                "source_page": s["page"],
            })

    for i, a in enumerate(state_amendments, 1):
        where = f" (section {a['after_section']})" if a.get("after_section") else ""
        text = f"{a['state']} amendment to the {meta['name']}{where}: {a['text']}"
        chunks.append({
            "chunk_id": f"{meta['slug']}-stateamend-{a['state'].lower()}-{i}",
            "text": text,
            "act": meta["name"],
            "chapter": "",
            "section": f"Section {a['after_section']} (state amendment)",
            # Not central law. The jurisdiction filter already widens a state
            # query to include Central, so tagging the state here is what
            # keeps one state's amendment out of another state's answer.
            "jurisdiction": a["state"],
            "effective_date": meta["effective_date"],
            "assent_date": meta["assent_date"],
            "excerpt": text,
            "source_url": meta["source_url"],
            "text_sha256": sha256(text),
            "raw_sha256": raw_digest,
            "extraction_method": meta["extraction_method"],
            "reviewer_name": REVIEWER,
            "fetched_at": fetched_at,
            "reference_url": None,
            "source_page": a["page"],
        })

    return chunks


def main(argv):
    if len(argv) != 4 or argv[1] not in ACTS:
        raise SystemExit(
            "usage: python -m data.ingestion.parsers.build_chunks "
            f"<{'|'.join(ACTS)}> <parsed.json> <out.json>")

    chunks = build(argv[1], Path(argv[2]))

    ids = [c["chunk_id"] for c in chunks]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise SystemExit(f"duplicate chunk_ids: {dupes[:10]}")

    Path(argv[3]).write_text(json.dumps(chunks, ensure_ascii=False, indent=1),
                             encoding="utf-8")

    lengths = sorted(len(c["text"]) for c in chunks)
    print(f"chunks       : {len(chunks)}")
    print(f"chars        : min {lengths[0]} / median {lengths[len(lengths)//2]} "
          f"/ max {lengths[-1]}")
    print(f"over {MAX_CHARS}    : {sum(1 for x in lengths if x > MAX_CHARS)}")
    print(f"written      : {argv[3]}")


if __name__ == "__main__":
    main(sys.argv)
