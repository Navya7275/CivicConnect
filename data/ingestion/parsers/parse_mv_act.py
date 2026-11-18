"""Parse the Motor Vehicles Act, 1988 into section-level records.

Usage:
    python -m data.ingestion.parsers.parse_mv_act <txt-dir> <out.json>

<txt-dir> holds the pdftotext output of the India Code consolidated PDF,
split into the two parts named in PARTS below:

    pdftotext -layout A1988-59_1-1-88.pdf   mv-1-88.txt
    pdftotext -layout A1988-59_1-89-176.pdf mv-89-176.txt

Use -layout and do not pass the text through anything that strips form feeds:
they are what carries the page numbers, and page numbers are what let a
citation open the provision it quotes.

WHICH EDITION THIS EXPECTS
--------------------------
The India Code consolidated text marked "[As on the 15th August, 2026]",
which carries every amendment through the Jan Vishwas (Amendment of
Provisions) Act, 2026. This matters: India Code also serves a pre-2019
edition of the same Act under a near-identical filename, and the two are not
distinguishable by name or section count. The 2019 amendment rewrote most of
the penalty provisions, so the older text states fines that are wrong by a
factor of five -- s.185 drunk driving reads two thousand rupees there against
ten thousand here.

check_edition() refuses to parse the older text. It looks for terms the 2019
amendment introduced ("golden hour", "aggregator", the National Road Safety
Board), none of which appear in the earlier edition.

FOUR THINGS THAT CORRUPT THE PARSE IF UNHANDLED
-----------------------------------------------
1. A diagonal "India Code" watermark is extracted as stray tokens -- "In",
   "di", "aC", "od", "e" -- once per page, 875 of them in 176 pages. Left in,
   they land inside quoted statute: s.185 reads "od with fine" and "aC both".
2. Amendment footnotes open with a number and a full stop ("1. Subs. by Act
   32 of 2019, s. 17, for ..."), so a regex for section headings matches them.
   Driving the parse from the Arrangement of Sections, and requiring each
   heading to be the next section expected, is what rejects them.
3. Six STATE AMENDMENT blocks sit inside the body. They are real law but they
   are Rajasthan's or Karnataka's, not central, and merging them into the
   preceding central section would misstate both. They become their own
   records, carrying the state as jurisdiction.
4. Sections carry letter suffixes (2A, 110A, 164B, 215D, 217A), so section
   identifiers do not sort or compare as integers.

PROVENANCE
----------
India Code, the Legislative Department's own repository. The watermark the
cleaner removes is itself the evidence of origin.
"""

import json
import re
import sys
from pathlib import Path

PARTS = [("mv-1-88.txt", 1), ("mv-89-176.txt", 89)]

# Fragments of the diagonal "India Code" watermark, as pdftotext emits them.
# Nearly all land on a line of their own; a few share a line with statute text
# or with a line of asterisks marking an omission ("* * od * *").
WATERMARK = ("In", "di", "aC", "od", "e")
# "aC", "od" and "di" are not words, so they can be removed wherever they
# stand alone. "In" and "e" are only removed as a whole line, since both occur
# in the text ("In this Act", "e-cart") and a false strip would alter statute.
WATERMARK_ISOLATED = re.compile(r"(?<=\s{2})(?:aC|od|di)(?=\s{2}|\s*$)")
WATERMARK_TRAILING = re.compile(r"\s{2,}(?:In|di|aC|od|e)\s*$")

# Terms the Motor Vehicles (Amendment) Act, 2019 introduced. Absent from the
# pre-2019 edition, so their presence identifies the consolidated text.
EDITION_MARKERS = ("golden hour", "aggregator", "National Road Safety Board")

TOC_START = re.compile(r"^\s*ARRANGEMENT OF SECTIONS\s*$")
TOC_END = re.compile(r"^\s*THE SECOND SCHEDULE")
BODY_START = re.compile(r"^\s*BE it enacted by Parliament")
# The sections stop here. Past this point come the First Schedule (road
# signs) and the Statement of Objects and Reasons, which the last section
# absorbed -- 6,471 characters of s.217A that were not s.217A.
BODY_END = re.compile(r"^\s*\[*\s*\[?THE FIRST SCHEDULE")

# In the body a chapter heading inserted by an amendment is bracketed
# ("[CHAPTER XI"), and its all-caps title sits on the next line.
CHAP_RE = re.compile(r"^\s*\[*\s*CHAPTER\s+([IVXL]+)\s*\]*\s*$")
ALL_CAPS = re.compile(r"^[^a-z]*[A-Z][^a-z]*$")
TOC_ENTRY = re.compile(r"^(\d{1,3}[A-Z]?)\.\s+(.+)$")
# A body heading: "185. Driving by a drunken person...—Whoever, while driving".
# Amendment brackets land in two places and both hid headings:
#   "[2A. E-cart and e-rickshaw.—"                 whole section inserted
#   "93. 2[Agent or canvasser or aggregator...]—"  title alone substituted
# Anchoring on the digit, or requiring a capital straight after the number,
# made those sections invisible, and the section before each then ran on and
# absorbed the remainder of the Act.
#
# This pattern is loose enough to match an amendment footnote ("2. Subs. by
# Act 32 of 2019..."), which is why FOOTNOTE is tested first and why a
# heading counts only when it is the next section the TOC expects.
# The leading superscript is only ever allowed immediately before a bracket.
# Letting it stand alone made it steal the first digit of a plain heading:
# "10. Form and contents..." matched with "1" as the superscript and "0" as
# the section number, so section 10 was never found.
SEC_RE = re.compile(
    r"^\s{0,10}(?:\d{1,2}\s*\[|\[)?\s*(\d{1,3}[A-Z]?)\.\s*\d*\s*\[?\s*(?=[A-Z])")
STATE_BLOCK = re.compile(r"^\s*STATE AMENDMENTS?\s*$")
# A whole chapter repealed by the 2019 amendment is recorded in place:
# "[CHAPTER X--LIABILITY WITHOUT FAULT IN CERTAIN CASES] Omitted by ...".
# It is structure, not statute, and without this it was appended to s.139.
# Omitted *sections* are left alone: they parse as ordinary records whose
# text states that the provision was omitted, which is what a reader needs.
OMITTED_CHAPTER = re.compile(r"^\s*\[?CHAPTER\b.*Omitted by")
# An amendment footnote opens with a number and a full stop, exactly as a
# section heading does. What separates them is that a footnote always cites
# the amending instrument, so the citation is required rather than the opening
# word -- a list of opening words missed "Sub-clause (a) omitted by Act 54 of
# 1994, s. 2 (w.e.f. 14-11-1994)", which then landed inside s.2's text.
FOOTNOTE_OPENS = re.compile(r"^\s*\d{1,2}\.\s+\S")
FOOTNOTE_CITES = re.compile(r"w\.e\.f\.|ibid|by Act \d+ of \d{4}|by s\. \d+")


def is_footnote(line: str) -> bool:
    return bool(FOOTNOTE_OPENS.match(line) and FOOTNOTE_CITES.search(line))
PAGE_NUMBER = re.compile(r"^\s*\d{1,3}\s*$")
NOISE = re.compile(r"^\s*(SECTIONS|_+|-+)\s*$")


def strip_watermark(line: str) -> str | None:
    """Return the line without watermark text, or None if it was only that."""
    if line.strip() in WATERMARK:
        return None
    line = WATERMARK_TRAILING.sub("", line)
    return WATERMARK_ISOLATED.sub("", line)


def load_lines(src: Path):
    """Return [(page_number, line)] across both parts, watermark removed."""
    flat = []
    for fname, first_page in PARTS:
        path = src / fname
        if not path.exists():
            raise SystemExit(f"missing input: {path}")
        raw = path.read_text(encoding="utf-8")
        for offset, page_text in enumerate(raw.split("\f")):
            for line in page_text.split("\n"):
                cleaned = strip_watermark(line)
                if cleaned is not None:
                    flat.append((first_page + offset, cleaned))
    return flat


def check_edition(flat):
    """Refuse the pre-2019 edition, whose penalty figures are long superseded."""
    joined = " ".join(ln for _, ln in flat).lower()
    missing = [m for m in EDITION_MARKERS if m.lower() not in joined]
    if missing:
        raise SystemExit(
            "This looks like the pre-2019 Motor Vehicles Act: no mention of "
            + ", ".join(repr(m) for m in missing)
            + ".\nThat edition states penalties the 2019 amendment replaced "
            "(s.185 drunk driving reads two thousand rupees against ten "
            "thousand), so it must not be ingested.\nUse the India Code "
            "consolidated text marked '[As on the 15th August, 2026]'."
        )


def parse_toc(flat):
    """Arrangement of Sections -> ordered [(section, title, chapter, chap_title)]."""
    start = next(i for i, (_, ln) in enumerate(flat) if TOC_START.match(ln))
    end = next(i for i, (_, ln) in enumerate(flat)
               if i > start and TOC_END.match(ln))

    entries = []
    chap = chap_title = None
    awaiting_title = False
    cur = None

    for _, ln in flat[start:end]:
        text = ln.strip()
        if not text or NOISE.match(ln) or PAGE_NUMBER.match(ln):
            continue

        chapter_match = CHAP_RE.match(ln)
        if chapter_match:
            chap, awaiting_title, cur = chapter_match.group(1), True, None
            continue
        if awaiting_title:
            if text == text.upper():
                chap_title = text
                continue
            awaiting_title = False

        entry = TOC_ENTRY.match(text)
        if entry:
            cur = {"section": entry.group(1), "title": entry.group(2).strip(),
                   "chapter": chap, "chapter_title": chap_title}
            entries.append(cur)
        elif cur and not cur["title"].rstrip().endswith("."):
            cur["title"] += " " + text        # wrapped title

    for e in entries:
        e["title"] = re.sub(r"\s+", " ", e["title"]).strip().rstrip(".")
    return entries


def parse_body(flat, toc):
    """Body -> section records, plus state-amendment records kept separate.

    A heading is accepted only when it is the next section the Arrangement of
    Sections leads us to expect. Amendment footnotes open with a number and a
    full stop too, and that ordering requirement is the whole defence against
    reading one as the start of a new section.
    """
    start = next(i for i, (_, ln) in enumerate(flat) if BODY_START.match(ln))
    expected = [e["section"] for e in toc]
    by_number = {e["section"]: e for e in toc}

    sections, state_amendments = [], []
    cur = None
    cursor = 0            # how far through `expected` we are
    in_state_block = False
    state_name = None
    state_lines = []

    def close_section():
        nonlocal cur
        if cur:
            sections.append(cur)
            cur = None

    def close_state():
        nonlocal state_lines, state_name, in_state_block
        if state_lines and state_name:
            state_amendments.append({
                "state": state_name,
                "after_section": cur["section"] if cur else None,
                "page": state_page,
                "text": re.sub(r"\s+", " ", " ".join(state_lines)).strip(),
            })
        state_lines, state_name, in_state_block = [], None, False

    state_page = None
    footnote_page = None
    skipping_wrapped = False
    in_chapter_title = False
    for page, ln in flat[start + 1:]:
        text = ln.strip()
        if not text or PAGE_NUMBER.match(ln) or NOISE.match(ln):
            continue
        if skipping_wrapped:
            # Continuation of the omitted-chapter line below; it ends where
            # the sentence does.
            skipping_wrapped = not text.endswith(".")
            continue

        if BODY_END.match(ln):
            break

        if CHAP_RE.match(ln):
            in_chapter_title = True
            continue

        if in_chapter_title:
            # The chapter's title follows its number on the next line, in
            # capitals, and otherwise lands in the preceding section's text.
            if ALL_CAPS.match(text):
                continue
            in_chapter_title = False

        if OMITTED_CHAPTER.match(ln):
            skipping_wrapped = not text.endswith(".")
            continue

        if STATE_BLOCK.match(ln):
            close_state()
            in_state_block, state_page = True, page
            continue

        if page != footnote_page:
            footnote_page = None          # a new page starts in statute again

        if is_footnote(ln):
            # Amendment history, not statute. Recorded on the section so the
            # information is not lost, but kept out of the quotable text.
            footnote_page = page
            if cur is not None:
                cur.setdefault("amendment_notes", []).append(text)
            continue

        if page == footnote_page:
            # A footnote wraps, and its continuation carries nothing that
            # marks it as one -- "ibid. (w.e.f. 1-9-2019)." on its own looks
            # like prose and landed in the middle of s.9. Footnotes sit at the
            # foot of the page, so once one begins, the rest of that page is
            # footnote text.
            if cur is not None and cur.get("amendment_notes"):
                cur["amendment_notes"][-1] += " " + text
            continue

        match = SEC_RE.match(ln)
        if match and cursor < len(expected) and match.group(1) == expected[cursor]:
            close_state()
            close_section()
            number = match.group(1)
            meta = by_number[number]
            cur = {"section": number, "title": meta["title"],
                   "chapter": meta["chapter"],
                   "chapter_title": meta["chapter_title"],
                   "page": page, "_lines": [text]}
            cursor += 1
            continue

        if in_state_block:
            if state_name is None:
                state_name = text          # the line after the banner names it
            else:
                state_lines.append(text)
            continue

        if cur is not None:
            cur["_lines"].append(text)

    close_state()
    close_section()

    for s in sections:
        s["text"] = re.sub(r"\s+", " ", " ".join(s.pop("_lines"))).strip()
    return sections, state_amendments


def validate(sections, toc, state_amendments):
    problems = []
    found = [s["section"] for s in sections]
    wanted = [e["section"] for e in toc]

    missing = [n for n in wanted if n not in found]
    if missing:
        problems.append(f"{len(missing)} sections in the TOC but not the body: "
                        f"{missing[:20]}")

    duplicates = sorted({n for n in found if found.count(n) > 1})
    if duplicates:
        problems.append(f"duplicate sections: {duplicates}")

    if found != [n for n in wanted if n in found]:
        problems.append("body sections are not in Arrangement-of-Sections order")

    untitled = [s["section"] for s in sections if not s["title"]]
    if untitled:
        problems.append(f"missing titles: {untitled}")

    joined = " ".join(s["text"] for s in sections)
    leaks = len(re.findall(r"(?<![A-Za-z])(aC|di|od)(?![A-Za-z])", joined))
    if leaks:
        problems.append(f"{leaks} watermark fragments left in section text")

    # A repealed section's record is a citation of the Act that repealed it
    # ("140. [Liability to pay compensation...] Omitted by s. 50, ibid.
    # (w.e.f. 1-4-2022)."), so the citation is the content, not a leak.
    omitted = re.compile(r"^\d{1,3}[A-Z]?\.\s*\[.*?\]\s*Omitted by", re.S)
    for s in sections:
        if omitted.match(s["text"]):
            continue
        if re.search(r"Subs\. by Act|w\.e\.f\.|\bibid\b", s["text"]):
            problems.append(f"amendment footnote leaked into s.{s['section']}")
            break

    if not state_amendments:
        problems.append("no state amendments found (the source has six blocks)")

    return problems


def main(argv):
    if len(argv) != 3:
        raise SystemExit(__doc__.strip().split("\n\n")[1])

    src, out = Path(argv[1]), Path(argv[2])
    flat = load_lines(src)
    check_edition(flat)

    toc = parse_toc(flat)
    sections, state_amendments = parse_body(flat, toc)

    problems = validate(sections, toc, state_amendments)
    if problems:
        raise SystemExit("parse failed validation:\n  - " + "\n  - ".join(problems))

    payload = {"sections": sections, "state_amendments": state_amendments}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                   encoding="utf-8")

    lengths = sorted(len(s["text"]) for s in sections)
    noted = sum(1 for s in sections if s.get("amendment_notes"))
    print(f"TOC entries      : {len(toc)}")
    print(f"sections parsed  : {len(sections)} (validated)")
    print(f"chapters         : {len({s['chapter'] for s in sections})}")
    print(f"state amendments : {len(state_amendments)} "
          f"({', '.join(sorted({a['state'] for a in state_amendments}))})")
    print(f"with amendment notes: {noted}")
    print(f"text chars       : min {lengths[0]} / median {lengths[len(lengths)//2]} "
          f"/ max {lengths[-1]} / total {sum(lengths):,}")
    print(f"written          : {out}")


if __name__ == "__main__":
    main(sys.argv)
