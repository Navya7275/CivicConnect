"""Parse the Bharatiya Nyaya Sanhita, 2023 into section-level records.

Usage:
    python -m data.ingestion.parsers.parse_bns <txt-dir> <out.json>

<txt-dir> holds the pdftotext output of the source PDF, split into the two
parts named in PARTS below. Produce them with:

    pdftotext -layout BNS2023-1-99.pdf   BNS2023-1-99.txt
    pdftotext -layout BNS2023-100-237.pdf BNS2023-100-237.txt

Form feeds are what carry the page numbers, so -layout matters and the text
must not be passed through anything that strips them. Page numbers become the
`#page=N` anchors on citations, which is the whole point of keeping them.

WHERE EACH FIELD COMES FROM
---------------------------
Titles and chapters come from the Arrangement of Sections at the front, not
from the marginal notes printed beside the body. The marginal notes say the
same thing, but they wrap across lines with nothing to distinguish a
continuation from the opening words of the provision, and taking them from
there truncated 128 of the 358 titles.

The body supplies the provision text and the page number.

FOUR THINGS THE SOURCE DOES THAT COST CONTENT IF UNHANDLED
----------------------------------------------------------
Each of these loses text silently -- the parse still succeeds, just with less
in it -- so the validation at the bottom is not decoration.

1. Section headings are written both "115. (1)" and "115.(1)". Requiring the
   space dropped 15 sections.
2. TOC entries 1-347 start at column 0; 348-358 carry a leading space.
   Testing the first character before stripping dropped all eleven.
3. Chapter titles wrap ("OF OFFENCES RELATING TO COIN, CURRENCY-NOTES, BANK- /
   NOTES, AND GOVERNMENT STAMPS"), and the line after a chapter heading may
   instead be a sub-heading ("Of abetment"). Chapter titles are in capitals
   and sub-headings are not, which is what separates them.
4. A sub-heading is normally centred, but s.357's is indented like a wrapped
   title. A TOC title always ends in a full stop, so a complete title means
   the next line begins something else.

PROVENANCE
----------
The source PDF is a compiled reference edition, not the official gazette: it
carries a "For Reference only" note and its metadata was stripped by the tool
used to split it. Section numbering and text were spot-checked against known
BNS provisions and matched, but that is verification by sampling, not an
official source. Anything ingested from it should say so in its provenance
fields. See docs/DATA_SOURCES.md.
"""

import json
import re
import sys
from pathlib import Path

PARTS = [("BNS2023-1-99.txt", 1), ("BNS2023-100-237.txt", 100)]

EXPECTED_SECTIONS = 358  # BNS 2023 as enacted

# Page furniture from the source PDF's navigation, plus bare page numbers.
NOISE = re.compile(
    r"^\s*(HomePage|Index|Note: For Reference only\.?|Chapters and Sections"
    r"|CORRESPONDING SECTION TABLE.*|SECTION|\d{1,3})\s*$"
)
TOC_ENTRY = re.compile(r"^(\d{1,3}[A-Z]?)\.\s+(.*)$")
SEC_RE = re.compile(r"^\s{0,12}(\d{1,3}[A-Z]?)\.(?:\s+(?=\S)|(?=\())")
CHAP_RE = re.compile(r"^\s*CHAPTER\s+([IVXL]+)\s*$")

SUBHEAD_INDENT = 20  # centred sub-heading vs ~6 for a wrapped title


def load_lines(src: Path):
    """Return [(page_number, line)] across both parts, in document order."""
    flat = []
    for fname, first_page in PARTS:
        path = src / fname
        if not path.exists():
            raise SystemExit(f"missing input: {path}")
        raw = path.read_text(encoding="utf-8")
        for offset, page_text in enumerate(raw.split("\f")):
            for line in page_text.split("\n"):
                flat.append((first_page + offset, line))
    return flat


def parse_toc(flat):
    """Arrangement of Sections -> {section: title}, {section: (chap, title, sub)}."""
    end = next(i for i, (_, ln) in enumerate(flat)
               if "CORRESPONDING SECTION TABLE" in ln)

    titles, chapters = {}, {}
    chap = chap_title = sub_heading = cur = None
    in_sub = awaiting_chapter_title = collecting_chapter_title = False

    for _, ln in flat[:end]:
        if NOISE.match(ln):
            continue

        chapter_match = CHAP_RE.match(ln)
        if chapter_match:
            chap = chapter_match.group(1)
            awaiting_chapter_title, collecting_chapter_title = True, False
            sub_heading, in_sub, cur = None, False, None
            continue

        text = ln.strip()

        if awaiting_chapter_title:
            if not text:
                continue
            if not TOC_ENTRY.match(text) and text == text.upper():
                chap_title = (f"{chap_title} {text}"
                              if collecting_chapter_title else text)
                collecting_chapter_title = True
                continue
            awaiting_chapter_title = collecting_chapter_title = False
            # fall through: a sub-heading or the chapter's first entry

        indent = len(ln) - len(ln.lstrip())
        if (text and not TOC_ENTRY.match(text) and text != text.upper()
                and indent >= SUBHEAD_INDENT):
            if text.startswith("Of "):
                sub_heading, in_sub = text, True
            elif in_sub:
                sub_heading = f"{sub_heading} {text}"
            cur = None
            continue
        in_sub = False

        entry = TOC_ENTRY.match(text)
        if entry:
            cur = entry.group(1)
            titles[cur] = entry.group(2).strip()
            chapters[cur] = (chap, chap_title, sub_heading)
        elif cur and text and not titles[cur].rstrip().endswith("."):
            titles[cur] = f"{titles[cur]} {text}"
        elif text.startswith("Of "):
            sub_heading, in_sub, cur = text, True, None

    for key in titles:
        titles[key] = re.sub(r"\s+", " ", titles[key]).strip().rstrip(".")
    return titles, chapters


def parse_body(flat, titles, chapters):
    """Body text -> [section record]. A heading only counts if the TOC knows it."""
    start = next(i for i, (_, ln) in enumerate(flat)
                 if re.match(r"\s*1\.\s*\(1\)\s*This Act may be called", ln))

    sections, cur = [], None
    for page, ln in flat[start:]:
        if NOISE.match(ln) or CHAP_RE.match(ln):
            continue
        match = SEC_RE.match(ln)
        if match and match.group(1) in titles:
            if cur:
                sections.append(cur)
            number = match.group(1)
            chapter, chapter_title, sub_heading = chapters.get(
                number, (None, None, None))
            cur = {
                "section": number,
                "title": titles[number],
                "chapter": chapter,
                "chapter_title": chapter_title,
                "sub_heading": sub_heading,
                "page": page,
                "_lines": [ln.strip()],
            }
        elif cur is not None and ln.strip():
            cur["_lines"].append(ln.strip())
    if cur:
        sections.append(cur)

    for section in sections:
        section["text"] = re.sub(r"\s+", " ",
                                 " ".join(section.pop("_lines"))).strip()
    return sections


def sort_key(number: str):
    match = re.match(r"(\d+)([A-Z]?)", number)
    return int(match.group(1)), match.group(2)


def validate(sections):
    """Fail loudly on the damage this source is known to cause.

    Every failure mode above loses sections or text without raising anything,
    so a parse that "worked" is not evidence of much. These checks are what
    makes a successful run mean something.
    """
    problems = []
    numbers = [s["section"] for s in sections]

    if len(sections) != EXPECTED_SECTIONS:
        problems.append(f"got {len(sections)} sections, expected {EXPECTED_SECTIONS}")

    duplicates = sorted({n for n in numbers if numbers.count(n) > 1})
    if duplicates:
        problems.append(f"duplicate sections: {duplicates}")

    present = {sort_key(n)[0] for n in numbers}
    missing = [i for i in range(1, EXPECTED_SECTIONS + 1) if i not in present]
    if missing:
        problems.append(f"missing sections: {missing}")

    out_of_order = [(numbers[i - 1], numbers[i]) for i in range(1, len(numbers))
                    if sort_key(numbers[i]) <= sort_key(numbers[i - 1])]
    if out_of_order:
        problems.append(f"out of order: {out_of_order[:5]}")

    untitled = [s["section"] for s in sections if not s["title"]]
    if untitled:
        problems.append(f"missing titles: {untitled}")

    unchaptered = [s["section"] for s in sections if not s["chapter"]]
    if unchaptered:
        problems.append(f"missing chapters: {unchaptered}")

    # Page furniture that survived into the text means NOISE missed a variant.
    joined = " ".join(s["text"] for s in sections)
    for leak in ("HomePage", "Reference only"):
        if leak in joined:
            problems.append(f"{joined.count(leak)}x '{leak}' leaked into text")

    return problems


def main(argv):
    if len(argv) != 3:
        raise SystemExit(__doc__.strip().split("\n\n")[1])

    src, out = Path(argv[1]), Path(argv[2])
    flat = load_lines(src)
    titles, chapters = parse_toc(flat)
    sections = parse_body(flat, titles, chapters)

    problems = validate(sections)
    if problems:
        raise SystemExit("parse failed validation:\n  - " + "\n  - ".join(problems))

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sections, ensure_ascii=False, indent=1),
                   encoding="utf-8")

    lengths = sorted(len(s["text"]) for s in sections)
    print(f"sections    : {len(sections)} (validated)")
    print(f"chapters    : {len({s['chapter'] for s in sections})}")
    print(f"sub-headings: {len({s['sub_heading'] for s in sections if s['sub_heading']})}")
    print(f"text chars  : min {lengths[0]} / median {lengths[len(lengths) // 2]} "
          f"/ max {lengths[-1]} / total {sum(lengths):,}")
    print(f"written     : {out}")


if __name__ == "__main__":
    main(sys.argv)
