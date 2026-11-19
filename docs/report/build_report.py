"""Build the CivicConnect major-project report as a .docx in the ITM thesis format."""
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

FIG = Path(__file__).resolve().parent / "figures"
OUT = Path(__file__).resolve().parent / "CivicConnect_Project_Report.docx"

ASSETS = Path(__file__).resolve().parent / "assets"

# Authors in roll-number order, and the supervising faculty.
STUDENTS = [
    "Ayushi Shrivastava (BETN1AI23005)",
    "Harsh Gupta (BETN1AI23007)",
    "Harshit Garg (BETN1AI23008)",
    "Navya Singhal (BETN1AI23009)",
]
STUDENTS_INLINE = ", ".join(STUDENTS[:-1]) + " and " + STUDENTS[-1]
GUIDE = "Dr. Manali Shukla"
GUIDE_TITLE = "Associate Professor, Department of CSA, SOCIS"
INSTITUTE = "ITM University, Turari"

FONT = "Times New Roman"
BODY = 10
H1, H2, H3 = 17, 15, 13
LINE = 1.2          # line spacing used throughout the body
GREY = RGBColor(0x59, 0x59, 0x59)
HDR_FILL = "DCE3F0"

J = WD_ALIGN_PARAGRAPH.JUSTIFY
C = WD_ALIGN_PARAGRAPH.CENTER
L = WD_ALIGN_PARAGRAPH.LEFT
R = WD_ALIGN_PARAGRAPH.RIGHT

doc = Document()


# ------------------------------------------------------------------ helpers
def _font(run, size=BODY, bold=False, italic=False, color=None):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color is not None:
        run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), FONT)
    return run


_pending_break = False


def page_break():
    """Start the next paragraph on a fresh page.

    Deliberately not doc.add_page_break(), which appends a paragraph whose only
    content is the break. When the preceding page happens to be exactly full,
    that empty paragraph flows onto the next page and its break then pushes the
    real content one page further, leaving a blank page behind — which is what
    happened between the contents and the list of abbreviations. Setting
    page_break_before on the next real paragraph cannot do that.
    """
    global _pending_break
    _pending_break = True


def p(text="", size=BODY, bold=False, italic=False, align=J, space_after=6,
      space_before=0, line=LINE, color=None, indent=None):
    global _pending_break
    par = doc.add_paragraph()
    if _pending_break:
        par.paragraph_format.page_break_before = True
        _pending_break = False
    par.alignment = align
    pf = par.paragraph_format
    pf.line_spacing = line
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(space_before)
    if indent is not None:
        pf.left_indent = Inches(indent)
    if text:
        _font(par.add_run(text), size, bold, italic, color)
    return par


def rich(parts, align=J, size=BODY, line=LINE, space_after=6, indent=None):
    """parts = [(text, bold, italic), ...]"""
    par = doc.add_paragraph()
    par.alignment = align
    par.paragraph_format.line_spacing = line
    par.paragraph_format.space_after = Pt(space_after)
    if indent is not None:
        par.paragraph_format.left_indent = Inches(indent)
    for text, b, i in parts:
        _font(par.add_run(text), size, b, i)
    return par


def h1(text):
    page_break()
    p(text, size=H1, bold=True, align=L, space_after=12, line=1.2)


def h2(text):
    # keep_with_next stops a heading from being left stranded at the foot of a
    # page with its section starting overleaf.
    p(text, size=H2, bold=True, align=L, space_after=6, space_before=10,
      line=LINE).paragraph_format.keep_with_next = True


def h3(text):
    p(text, size=H3, bold=True, align=L, space_after=4, space_before=8,
      line=LINE).paragraph_format.keep_with_next = True


def bullet(text, size=BODY, level=0):
    par = doc.add_paragraph(style="List Bullet")
    par.alignment = J
    par.paragraph_format.line_spacing = LINE
    par.paragraph_format.space_after = Pt(3)
    par.paragraph_format.left_indent = Inches(0.3 + 0.25 * level)
    _font(par.add_run(text), size)
    return par


def numbered(text, size=BODY):
    par = doc.add_paragraph(style="List Number")
    par.alignment = J
    par.paragraph_format.line_spacing = LINE
    par.paragraph_format.space_after = Pt(3)
    par.paragraph_format.left_indent = Inches(0.3)
    _font(par.add_run(text), size)
    return par


def caption(text):
    p(text, size=9, italic=True, align=C, space_after=12, line=1.0, color=GREY)


def figure(name, cap, width=6.3, keep_intro=True):
    if keep_intro and doc.paragraphs:
        # Hold the sentence that introduces the figure on the same page as the
        # figure, so a heading plus two lines is not left stranded at the foot
        # of a page with the figure overleaf.
        doc.paragraphs[-1].paragraph_format.keep_with_next = True
    doc.add_picture(str(FIG / name), width=Inches(width))
    pf = doc.paragraphs[-1].paragraph_format
    doc.paragraphs[-1].alignment = C
    pf.space_before = Pt(6)
    pf.space_after = Pt(4)
    pf.keep_with_next = True      # the caption travels with its figure
    pf.keep_together = True
    caption(cap)


def shade(cell, hexfill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexfill)
    tcPr.append(shd)


def table(rows, cap, widths=None, size=9, header=True):
    # The caption goes ABOVE the table, unlike a figure's. Word has no
    # "keep with previous", so a caption placed under a table can be pushed
    # onto the next page on its own — which is what happened to Table 12,
    # whose caption ended up alone at the top of a page with its table
    # overleaf. A caption above, marked keep_with_next, cannot be separated.
    cap_par = p(cap, size=9, italic=True, align=C, space_after=3, line=1.0,
                space_before=8, color=GREY)
    cap_par.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=0, cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for ci, val in enumerate(row):
            cells[ci].text = ""
            par = cells[ci].paragraphs[0]
            par.alignment = L
            par.paragraph_format.line_spacing = 1.0
            par.paragraph_format.space_after = Pt(2)
            par.paragraph_format.space_before = Pt(2)
            _font(par.add_run(str(val)), size, bold=(header and ri == 0))
            if header and ri == 0:
                shade(cells[ci], HDR_FILL)
        if header and ri == 0:
            # Repeat the header row when a long table breaks across a page.
            trPr = t.rows[0]._tr.get_or_add_trPr()
            el = OxmlElement("w:tblHeader")
            el.set(qn("w:val"), "true")
            trPr.append(el)
    if widths:
        for ci, w in enumerate(widths):
            for row in t.rows:
                row.cells[ci].width = Inches(w)
    for row in t.rows:
        # Never let a single row be split across a page boundary.
        trPr = row._tr.get_or_add_trPr()
        el = OxmlElement("w:cantSplit")
        el.set(qn("w:val"), "true")
        trPr.append(el)
    # A table is followed directly by body text, so give it a little air.
    p("", space_after=2, line=1.0)
    return t


def add_page_number(par):
    run = par.add_run()
    _font(run, 8)
    for tag, attr, text in (("w:fldChar", "w:fldCharType", "begin"),
                            ("w:instrText", None, "PAGE"),
                            ("w:fldChar", "w:fldCharType", "end")):
        el = OxmlElement(tag)
        if attr:
            el.set(qn(attr), text)
        else:
            el.set(qn("xml:space"), "preserve")
            el.text = text
        run._r.append(el)


def page_fmt(section, fmt, start=None):
    pg = OxmlElement("w:pgNumType")
    pg.set(qn("w:fmt"), fmt)
    if start is not None:
        pg.set(qn("w:start"), str(start))
    section._sectPr.append(pg)


def footer_number(section):
    section.footer.is_linked_to_previous = False
    par = section.footer.paragraphs[0]
    par.alignment = C
    add_page_number(par)


def no_footer(section):
    section.footer.is_linked_to_previous = False
    section.footer.paragraphs[0].text = ""


# ------------------------------------------------- base style and page setup
style = doc.styles["Normal"]
style.font.name = FONT
style.font.size = Pt(BODY)
style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
# Never leave a single line of a paragraph alone at the top or bottom of a page.
style.paragraph_format.widow_control = True

A4_W, A4_H = Inches(8.27), Inches(11.69)


def add_page_border(section, sz=8, space=27):
    """Draw a box border on every page of this section.

    `sz` is in eighths of a point, so 8 is 1 pt. `space` is the gap in points
    between the page edge and the border, which is what offsetFrom "page"
    means.

    The border and the margins have to be chosen together. A true "Narrow"
    margin of 1.27 cm leaves only 36 pt between text and paper edge, so any
    border drawn inside it sits almost on the edge of the sheet; the 0.75 in
    margin used here leaves 54 pt, so the border can stand 27 pt off the edge
    with another 27 pt of air before the text starts.

    pgBorders must sit after pgMar and before pgNumType in a sectPr, which it
    does here because the margins are written by the lines above and the page
    numbering is appended later by page_fmt().
    """
    borders = OxmlElement("w:pgBorders")
    borders.set(qn("w:offsetFrom"), "page")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:space"), str(space))
        el.set(qn("w:color"), "000000")
        borders.append(el)
    section._sectPr.append(borders)


def page_setup(s, border=True):
    s.page_width, s.page_height = A4_W, A4_H
    # Narrow, but not Word's 1.27 cm "Narrow": that leaves no room for a page
    # border and stretches a 10 pt line to about 105 characters.
    for attr in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
        setattr(s, attr, Inches(0.75))
    s.footer_distance = Inches(0.45)
    if border:
        add_page_border(s)


s0 = doc.sections[0]
page_setup(s0)

# =========================================================== 1. TITLE PAGE
no_footer(s0)
p("", space_after=24)
p("CivicConnect: A Multi-Agent Hybrid-Retrieval Assistant for Indian "
  "Statutory Law and Welfare Schemes", size=16, bold=True, align=C, space_after=18, line=1.3)
p("A", size=12, align=C, space_after=8, line=1.2)
p("Major Project", size=13, align=C, space_after=8, line=1.2)
p("Submitted in partial fulfilment for the award of the degree of",
  size=11, italic=True, align=C, space_after=8, line=1.2)
p("BACHELOR OF TECHNOLOGY", size=12, align=C, space_after=6, line=1.2)
p("IN", size=11, align=C, space_after=6, line=1.2)
p("Computer Science and Engineering (Artificial Intelligence and Machine Learning)",
  size=12, align=C, space_after=14, line=1.2)
doc.add_picture(str(ASSETS / "itm_logo.png"), width=Inches(2.3))
doc.paragraphs[-1].alignment = C
doc.paragraphs[-1].paragraph_format.space_before = Pt(6)
doc.paragraphs[-1].paragraph_format.space_after = Pt(14)
p("by", size=11, italic=True, align=C, space_after=8, line=1.2)
for name in STUDENTS:
    p(name, size=12, align=C, space_after=4, line=1.2)
p("", space_after=10)
p("Under the Supervision of", size=11, align=C, space_after=8, line=1.2)
p(GUIDE, size=12, bold=True, align=C, space_after=4, line=1.2)
p(GUIDE_TITLE, size=11, align=C, space_after=3, line=1.2)
p(INSTITUTE, size=11, align=C, space_after=14, line=1.2)
p("ITM UNIVERSITY, GWALIOR – 474026 MP, INDIA", size=11, align=C, space_after=3, line=1.2)
p("(November 2026)", size=11, align=C, space_after=0, line=1.2)

# ====================================================== 2. FRONT MATTER
s1 = doc.add_section(WD_SECTION.NEW_PAGE)
page_setup(s1)
page_fmt(s1, "lowerRoman", start=2)
footer_number(s1)

p("CERTIFICATE", size=14, bold=True, align=C, space_after=18)
p("This is to certify that the work titled “CivicConnect: A Multi-Agent "
  "Hybrid-Retrieval Assistant for Indian Statutory Law and Welfare Schemes” "
  f"submitted by {STUDENTS_INLINE} in partial fulfilment of the award of the "
  "degree of B.Tech. (CSE), ITM University, Gwalior has been carried out under "
  "my/our supervision.", space_after=10)
p("To the best of my knowledge and belief, the dissertation", space_after=10)
for line in ("(i) Is an original piece of work of the candidates.",
             "(ii) It has duly been completed.",
             "(iii) It is up to the standard both in respect of contents and language.",
             "(iv) Free from plagiarism.",
             "(v) Work has not been submitted partially or wholly to any other University "
             "or Institute for the award of this or any other degree or diploma."):
    p(line, space_after=6)
p("", space_after=24)
tbl = doc.add_table(rows=4, cols=2)
for ri, (a, b) in enumerate([("Signature of Supervisor", "Signature of Co-guide"),
                             (GUIDE, ""),
                             (GUIDE_TITLE, "Designation"),
                             ("Date", "Date")]):
    for ci, val in enumerate((a, b)):
        cell = tbl.rows[ri].cells[ci]
        cell.text = ""
        par = cell.paragraphs[0]
        par.alignment = L if ci == 0 else R
        _font(par.add_run(val), BODY)

page_break()
p("DECLARATION", size=14, bold=True, align=C, space_after=18)
p("We hereby declare that the work entitled “CivicConnect: A Multi-Agent "
  "Hybrid-Retrieval Assistant for Indian Statutory Law and Welfare Schemes” "
  "submitted to the Department of CSA, SOCIS, ITM University, Gwalior (M.P.) "
  f"is our work done under the supervision of {GUIDE}, {GUIDE_TITLE}. The "
  "dissertation doesn’t contain any part which has been submitted for award of "
  "any degree either in this University or in any other University.",
  space_after=12)
p("We further declare that the work is free from any plagiarism.", space_after=36, indent=0.4)
for label in ("(Signature of the candidates)", "(Name of the candidates)",
              "(Roll Number of the candidates)"):
    p(label, align=R, space_after=30)
p("Verified by guide", align=R, space_after=0)

page_break()
p("ACKNOWLEDGEMENT", size=14, bold=True, align=C, space_after=18)
p("The success and outcome of this project required a great deal of guidance and "
  "assistance, and we are privileged to have received it throughout. All that we "
  "have been able to do is owed to that supervision, and we would not forget to "
  "thank those who gave it.", space_after=10)
p(f"We respect and thank {GUIDE}, {GUIDE_TITLE}, {INSTITUTE}, for the "
  "opportunity to undertake this work and for the support and direction that "
  "allowed us to complete it properly. She took a keen interest in the project, "
  "questioned our assumptions at the points where they most needed questioning, "
  "and provided the information necessary to build a system rather than a "
  "demonstration.", space_after=10)
p("We thank the Head of the Department, the faculty of the Department of Computer "
  "Science and Applications, and the Dean, SOCIS, ITM "
  "University, Gwalior, for their encouragement and for the timely support that "
  "carried this work to completion.", space_after=10)
p("We acknowledge the public institutions whose work this project depends upon. "
  "The India Code portal of the Ministry of Law and Justice and the MyScheme portal "
  "of the Government of India make statutory text and welfare-scheme information "
  "freely available; without that openness a grounded system of this kind could not "
  "be built by students at all.", space_after=10)
p("Finally, we thank our families, who trusted us and helped us through this work.",
  space_after=0)

page_break()
p("ABSTRACT", size=14, bold=True, align=C, space_after=16)
p("Indian statutory law is public, free and almost unreadable to the people it "
  "governs. A tenant facing eviction, a consumer refused a refund, or a rider fined "
  "at a checkpoint can obtain the governing Act in seconds and understand almost "
  "none of it. General-purpose language assistants answer such questions fluently "
  "and are, in this domain, actively dangerous: they invent section numbers, "
  "conflate state law with central law, and quote provisions that amendments "
  "repealed years ago. The failure is not that the answer is wrong, but that a "
  "wrong answer is indistinguishable from a right one.", space_after=10)
p("This report presents CivicConnect, a multi-agent, hybrid-retrieval assistant "
  "that answers questions about Indian law and welfare schemes in plain language "
  "and attaches the statutory provision it relied on. A corpus of 963 indexed "
  "chunks was built from four Acts — the Bharatiya Nyaya Sanhita 2023, the Motor "
  "Vehicles Act 1988, the Consumer Protection Act 2019 and the Right to Information "
  "Act 2005 — together with eighteen central and state welfare schemes, parsed "
  "directly from authoritative sources by self-validating parsers that refuse to "
  "emit output when a document fails its structural checks. Retrieval fuses a dense "
  "FAISS index over 384-dimensional sentence embeddings with a sparse BM25 index "
  "using Reciprocal Rank Fusion. A LangGraph state machine orchestrates four agents "
  "— query understanding, retrieval, synthesis and verification — with two "
  "conditional edges: the system stops and asks which state the user is in rather "
  "than guessing on state-divergent law, and it refuses to return an answer whose "
  "citations were not among the retrieved sources.", space_after=10)
p("Measured over 109 answerable questions written in everyday language, dense "
  "retrieval reaches 77 % recall@10 — that is, for 77 of every 100 questions the "
  "provision that answers it was among the ten passages retrieved — and tuned "
  "hybrid retrieval reaches the same 77 %. "
  "That equality is the report's principal finding and it is a negative one: after "
  "tuning, the hybrid arm returns dense retrieval's exact result set, neither gaining "
  "nor losing a single question, and the three questions BM25 uniquely recovers are "
  "worth 2.8 percentage points against a standard error of 4.0. The widely repeated "
  "claim that hybrid retrieval beats dense retrieval did not reproduce on this corpus, "
  "and the report explains why. Eleven silent parser defects, each of which lost "
  "statutory text without raising an error, are documented alongside the validation "
  "that caught them. The system is deployed: a static frontend on Cloudflare Pages "
  "against a FastAPI backend on Hugging Face Spaces, serving real grounded answers.",
  space_after=10)
rich([("Keywords: ", True, False),
      ("retrieval-augmented generation, hybrid retrieval, reciprocal rank fusion, "
       "legal information retrieval, Indian statutory law, multi-agent orchestration, "
       "grounded question answering, citation verification.", False, False)],
     space_after=0)

# -------------------------------------------------------------- CONTENTS
page_break()
p("CONTENTS", size=14, bold=True, align=C, space_after=14)


def toc(label, page, bold=False, ind=0.0):
    par = doc.add_paragraph()
    par.alignment = L
    # Tight enough that the whole contents fits one page. It previously spilled
    # two entries onto a second, nearly empty one.
    par.paragraph_format.line_spacing = 1.1
    par.paragraph_format.space_after = Pt(0)
    par.paragraph_format.left_indent = Inches(ind)
    tabs = par.paragraph_format.tab_stops
    tabs.add_tab_stop(Inches(6.0), WD_ALIGN_PARAGRAPH.RIGHT)
    _font(par.add_run(label), BODY, bold)
    _font(par.add_run("\t" + str(page)), BODY, bold)


for item, pg, b, ind in [
    ("CERTIFICATE", "ii", True, 0), ("DECLARATION", "iii", True, 0),
    ("ACKNOWLEDGEMENT", "iv", True, 0), ("ABSTRACT", "v", True, 0),
    ("CONTENTS", "vi", True, 0), ("LIST OF ABBREVIATIONS", "vii", True, 0),
    ("LIST OF FIGURES AND TABLES", "viii", True, 0),
    ("Chapter 1 \u2014 Introduction and Objectives", "1", True, 0),
    ("1.1 Background", "1", False, 0.25),
    ("1.2 Why General-Purpose Assistants Fail on Statute", "1", False, 0.25),
    ("1.3 Problem Statement", "2", False, 0.25),
    ("1.4 Objectives", "2", False, 0.25),
    ("1.5 Scope and Delimitations", "2", False, 0.25),
    ("Chapter 2 \u2014 Literature Survey", "3", True, 0),
    ("2.1 Retrieval-Augmented Generation", "3", False, 0.25),
    ("2.2 Sparse, Dense and Hybrid Retrieval", "3", False, 0.25),
    ("2.3 Rank Fusion", "3", False, 0.25),
    ("2.4 Legal-Domain Language Models and Indian Legal NLP", "3", False, 0.25),
    ("2.5 Hallucination and Attribution in Legal AI", "4", False, 0.25),
    ("2.6 Agentic Orchestration and Self-Verification", "4", False, 0.25),
    ("2.7 Summary of Prior Work", "4", False, 0.25),
    ("Chapter 3 \u2014 Research Gap and Proposed System", "5", True, 0),
    ("3.1 Identified Research Gaps", "5", False, 0.25),
    ("3.2 System Overview", "5", False, 0.25),
    ("3.3 Corpus Construction and Provenance", "6", False, 0.25),
    ("3.4 Hybrid Retrieval and Rank Fusion", "7", False, 0.25),
    ("3.5 Synthesis and the Grounding Contract", "7", False, 0.25),
    ("3.6 The Verification Agent", "8", False, 0.25),
    ("3.7 Deployment Architecture", "8", False, 0.25),
    ("3.8 Technology Stack", "9", False, 0.25),
    ("Chapter 4 \u2014 Results and Discussions", "10", True, 0),
    ("4.1 Evaluation Design", "10", False, 0.25),
    ("4.2 Corpus Construction Results", "11", False, 0.25),
    ("4.3 Retrieval Performance at Two Corpus Scales", "12", False, 0.25),
    ("4.4 Per-Act Breakdown", "13", False, 0.25),
    ("4.5 The Central Finding: Hybrid Retrieval Did Not Beat Dense", "13", False, 0.25),
    ("4.6 Tuning Interventions and Their Measured Effect", "14", False, 0.25),
    ("4.7 Failure Modes: A System That Looked Healthy", "15", False, 0.25),
    ("4.8 Deployment Results", "15", False, 0.25),
    ("4.9 Threats to Validity", "16", False, 0.25),
    ("Chapter 5 \u2014 Conclusions and Future Work", "17", True, 0),
    ("5.1 Conclusions", "17", False, 0.25),
    ("5.2 Learning Outcomes", "17", False, 0.25),
    ("5.3 Future Work", "17", False, 0.25),
    ("5.4 Recommendations", "19", False, 0.25),
    ("REFERENCES", "20", True, 0),
]:
    toc(item, pg, b, ind)

# ------------------------------------------------------- ABBREVIATIONS
page_break()
p("LIST OF ABBREVIATIONS", size=14, bold=True, align=L, space_after=14)
for ab, full in [
    ("API", "Application Programming Interface"),
    ("BM25", "Best Matching 25 (probabilistic sparse ranking function)"),
    ("BNS", "Bharatiya Nyaya Sanhita, 2023"),
    ("CDN", "Content Delivery Network"),
    ("CORS", "Cross-Origin Resource Sharing"),
    ("CPA", "Consumer Protection Act, 2019"),
    ("CSE", "Computer Science Engineering"),
    ("EMA", "Exponential Moving Average"),
    ("FAISS", "Facebook AI Similarity Search"),
    ("HF", "Hugging Face"),
    ("IDF", "Inverse Document Frequency"),
    ("IR", "Information Retrieval"),
    ("JSON", "JavaScript Object Notation"),
    ("LFS", "Large File Storage (Git extension)"),
    ("LLM", "Large Language Model"),
    ("MV Act", "Motor Vehicles Act, 1988"),
    ("ORM", "Object-Relational Mapping"),
    ("RAG", "Retrieval-Augmented Generation"),
    ("REST", "Representational State Transfer"),
    ("RRF", "Reciprocal Rank Fusion"),
    ("RTI", "Right to Information Act, 2005"),
    ("SDK", "Software Development Kit"),
    ("SQL", "Structured Query Language"),
    ("SSR", "Server-Side Rendering"),
    ("UI", "User Interface"),
    ("w.e.f.", "With Effect From"),
]:
    rich([(f"{ab}", True, False), (" — ", False, False), (full, False, False)],
         align=L, space_after=2, line=1.3)

# ------------------------------------------------ LIST OF FIGURES/TABLES
page_break()
p("LIST OF FIGURES AND TABLES", size=14, bold=True, align=L, space_after=14)
p("Figures", size=12, bold=True, align=L, space_after=6)
for f in [
    "Figure 1. The CivicConnect orchestration graph.",
    "Figure 2. Corpus composition and chunk length distribution.",
    "Figure 3. Hybrid retrieval and Reciprocal Rank Fusion.",
    "Figure 4. The verification contract.",
    "Figure 5. Deployment architecture.",
    "Figure 6. Retrieval recall at two corpus scales.",
    "Figure 7. Recall@10 by source Act.",
    "Figure 8. Measured effect of the two tuning interventions.",
]:
    p(f, align=L, space_after=2, line=1.3)
p("Tables", size=12, bold=True, align=L, space_after=6, space_before=10)
for t in [
    "Table 1. Comparison with representative existing approaches.",
    "Table 2. Corpus sources and provenance.",
    "Table 3. Parser validation results.",
    "Table 4. Technology stack by layer.",
    "Table 5. How to read the numbers in this report.",
    "Table 6. Composition of the evaluation question set.",
    "Table 7. Silent defects caught by parser validation.",
    "Table 8. Retrieval recall@10 at two corpus scales.",
    "Table 9. Recall@10 by source Act on the full corpus.",
    "Table 10. Fusion parameter tuning.",
    "Table 11. Deployment failures encountered and their resolution.",
    "Table 12. Project execution plan.",
]:
    p(t, align=L, space_after=2, line=1.3)

# ============================================================ CHAPTERS
s2 = doc.add_section(WD_SECTION.NEW_PAGE)
page_setup(s2)
page_fmt(s2, "decimal", start=1)
footer_number(s2)

# ----------------------------------------------------------- CHAPTER 1
p("Chapter 1", size=H1, bold=True, align=L, space_after=4, line=1.2)
p("Introduction and Objectives", size=H1, bold=True, align=L, space_after=14, line=1.2)

h2("1.1 Background")
p("India legislates prolifically and publishes diligently. The India Code portal "
  "carries the consolidated text of central legislation, updated for amendments and "
  "free to anyone with a browser. By the standard of open government this is a "
  "considerable achievement. By the standard of a citizen trying to find out whether "
  "their landlord may lawfully evict them, it achieves very little.", space_after=8)
p("The obstacle is not access but comprehension. Statutory drafting is precise "
  "because it must survive adversarial reading in court, and that precision is "
  "purchased with nested sub-sections, internal cross-references, provisos that "
  "reverse the clause preceding them, and definitions that live in a different "
  "section from the operative text. Section 185 of the Motor Vehicles Act, 1988 "
  "states the penalty for driving under the influence; it does so in language that "
  "assumes the reader already knows what Chapter XIII does, what “first offence” "
  "means for the purposes of the Act, and that a state amendment may have replaced "
  "the figure entirely. A person who has just been stopped at a checkpoint does not "
  "have that context and cannot acquire it in the time available.", space_after=8)
p("The same gap runs through welfare administration. Central and state governments "
  "operate hundreds of schemes with genuine entitlements attached, and the binding "
  "constraint on uptake is frequently not eligibility but awareness: people do not "
  "claim what they do not know exists, and cannot establish whether they qualify "
  "without reading guidelines written for administrators rather than applicants.",
  space_after=8)
p("Large language models appear to solve this. They explain statute fluently, at "
  "length, in whatever register is asked of them, and they are free. This project "
  "began from the observation that in this particular domain that fluency is not a "
  "solution but a hazard.", space_after=8)

h2("1.2 Why General-Purpose Assistants Fail on Statute")
p("A general assistant asked about Indian law fails in four characteristic ways, "
  "and the four share a property that makes them more serious than ordinary error.",
  space_after=8)
rich([("Fabricated provisions. ", True, False),
      ("The model produces a section number of the right shape, attached to a "
       "plausible summary, for a provision that does not exist or does not say that. "
       "Empirical work on this is unambiguous: Dahl et al. measured hallucination "
       "rates between 58 % and 82 % on legal queries put to leading general-purpose "
       "models [1], and Magesh et al. found that commercial legal research tools "
       "marketed as hallucination-free still produced unfaithful output on a "
       "substantial fraction of queries [2]. A fabricated citation is worse than a "
       "refusal because it is actionable: it looks exactly like the thing a person "
       "would act upon.", False, False)], space_after=8)
rich([("Jurisdictional conflation. ", True, False),
      ("Indian law is federal. Motor vehicle penalties, rent control, stamp duty and "
       "land revenue diverge by state, sometimes sharply. A model trained on an "
       "undifferentiated mixture of Indian legal text has no reliable mechanism for "
       "keeping a Madhya Pradesh amendment out of an answer to a Karnataka question, "
       "and no mechanism at all for telling the user that the distinction matters.",
       False, False)], space_after=8)
rich([("Temporal drift. ", True, False),
      ("The Bharatiya Nyaya Sanhita replaced the Indian Penal Code with effect from "
       "1 July 2024, renumbering offences wholesale. The Motor Vehicles (Amendment) "
       "Act 2019 multiplied several penalties. A model whose training data "
       "predominantly predates these changes will answer confidently in the old "
       "numbering, and the answer will be wrong in a way that is invisible to anyone "
       "who does not already know the correct answer.", False, False)], space_after=8)
rich([("Absence of provenance. ", True, False),
      ("The decisive defect. Even where the substance is correct, an unsourced answer "
       "cannot be checked. The user cannot distinguish the 80 % that is right from the "
       "20 % that is not, and so gains no more usable certainty than they started with.",
       False, False)], space_after=8)
p("The common property is that all four failures are silent. The output is equally "
  "confident whether it is correct or invented. This observation shaped every "
  "design decision that follows, and recurred so persistently during development — "
  "in the system's own failures, not merely the model's — that Section 4.7 is "
  "devoted to it.", space_after=8)

h2("1.3 Problem Statement")
p("Design and deploy a question-answering system for Indian statutory law and "
  "welfare schemes that answers in language a non-lawyer can act on, that grounds "
  "every answer in verbatim provisions retrieved from authoritative sources, that "
  "attaches the specific section relied upon so that the user can check it, that "
  "distinguishes central from state law and asks rather than guesses when the "
  "distinction is unresolved, and that refuses to present an unverified answer as a "
  "verified one.", space_after=8)

h2("1.4 Objectives")
for o in [
    "Build a corpus of Indian statutory provisions parsed directly from "
    "authoritative sources, preserving verbatim text, section identity, chapter "
    "structure, effective dates and page-level provenance for every chunk.",
    "Ensure the ingestion pipeline is self-validating, so that a parser which "
    "silently loses statutory text fails loudly instead of producing a smaller "
    "corpus that looks complete.",
    "Implement hybrid retrieval combining dense semantic search with sparse lexical "
    "search through rank fusion, and measure whether the combination actually "
    "outperforms either arm alone rather than assuming it.",
    "Orchestrate query understanding, retrieval, synthesis and verification as a "
    "multi-agent state machine with explicit conditional control flow.",
    "Enforce a grounding contract in which an answer may cite only sections that "
    "retrieval actually returned, and mark as unverified any answer that fails it.",
    "Stop and request clarification on state-divergent questions where the user's "
    "jurisdiction is unknown, rather than silently assuming central law.",
    "Evaluate retrieval on a question set written in everyday language, deliberately "
    "avoiding the vocabulary of the corpus, and report per-Act results rather than a "
    "single aggregate.",
    "Deploy the complete system on free-tier infrastructure so that it is publicly "
    "reachable rather than a local demonstration.",
]:
    numbered(o)

h2("1.5 Scope and Delimitations")
p("The scope is deliberately bounded, and stating the boundaries precisely is part "
  "of the contribution. CivicConnect covers four central Acts and eighteen welfare "
  "schemes. It does not cover case law, and therefore cannot reason about judicial "
  "interpretation — a limitation of consequence, since the meaning of a provision is "
  "frequently settled by courts rather than by its text. It does not cover state "
  "legislation except for six state amendments to the Motor Vehicles Act, which "
  "exist in the corpus mainly to exercise the jurisdiction-filtering mechanism. It "
  "operates in English. It is an information system and not legal advice, and the "
  "interface says so on every page.", space_after=8)

# ----------------------------------------------------------- CHAPTER 2
h1("Chapter 2")
p("Literature Survey", size=H1, bold=True, align=L, space_after=14, line=1.2)

h2("2.1 Retrieval-Augmented Generation")
p("Retrieval-augmented generation, introduced by Lewis et al. [3], conditions a "
  "generative model on passages fetched from a non-parametric store at inference "
  "time. The architecture is attractive for statutory question answering for a "
  "reason beyond accuracy: the retrieved passages are available to be shown. A "
  "parametric model can be correct but cannot be checked; a retrieval-augmented one "
  "can hand the user the provision it used. Gao et al. survey the field's subsequent "
  "development [4], distinguishing naive, advanced and modular architectures, the "
  "last of which — routing, iteration and verification around the retrieval core — "
  "describes the design adopted here.", space_after=8)

h2("2.2 Sparse, Dense and Hybrid Retrieval")
p("Sparse lexical retrieval, of which BM25 [5] remains the canonical form, scores "
  "documents by weighted term overlap with length normalisation. It is exact, "
  "inspectable, needs no training, and fails whenever the user and the document "
  "choose different words for the same thing — pervasive in this domain, where a "
  "statute says “reply” and a citizen says “respond”, and where the Right to "
  "Information Act never once contains the token “RTI”.", space_after=8)
p("Dense retrieval replaces term overlap with similarity in a learned embedding "
  "space. Karpukhin et al. demonstrated that dual-encoder dense passage retrieval "
  "substantially outperforms BM25 on open-domain question answering [6]; "
  "Sentence-BERT [7] supplies the siamese training arrangement that makes "
  "sentence-level embeddings comparable by cosine distance, and MiniLM [8] "
  "distils that capability into a model small enough to run on a free-tier CPU. "
  "Vector search at corpus scale is handled by FAISS [9].", space_after=8)
p("The standard conclusion is that the two are complementary and should be combined, "
  "because each recovers documents the other misses. BEIR [10] tempers this: "
  "relative performance varies sharply by domain, and dense retrievers trained on "
  "one distribution may underperform BM25 on another. Later work — ColBERT's late "
  "interaction [11] and SPLADE's learned sparse expansion [12] — attempts to "
  "obtain both properties within a single model. Chapter 4 reports that on this "
  "corpus the complementarity, though real in principle, was not measurable in "
  "practice.", space_after=8)

h2("2.3 Rank Fusion")
p("Where two rankers are combined, their scores are rarely on comparable scales: a "
  "BM25 score is unbounded and corpus-dependent, a cosine similarity is bounded in "
  "[-1, 1]. Reciprocal Rank Fusion [13] sidesteps normalisation entirely by "
  "discarding scores and combining ranks, assigning each document a score of "
  "1/(k + rank) summed across rankers. Cormack et al. report k = 60 as robust across "
  "their experiments, and that constant has been adopted widely as a default. Its "
  "role is less innocuous than its ubiquity suggests: k determines how steeply "
  "reciprocal rank decays, and therefore how far agreement between rankers outweighs "
  "confidence within one of them. Section 4.6 shows that leaving it at the "
  "recommended value cost nine points of recall on this corpus.", space_after=8)

h2("2.4 Legal-Domain Language Models and Indian Legal NLP")
p("Domain adaptation of transformer encoders to legal text is well established. "
  "LEGAL-BERT [14] showed that pre-training on legal corpora improves downstream "
  "legal tasks over general-domain BERT [15]. For Indian law specifically, Paul "
  "et al. produced InLegalBERT by pre-training on Indian court judgments and "
  "demonstrated gains on Indian legal tasks [16]. Dataset work includes ILDC for "
  "court judgment prediction and explanation [17], a corpus for automatic "
  "structuring of Indian legal documents [18], and LeSICiN for legal statute "
  "identification from Indian documents [19] — the task closest to the retrieval "
  "problem addressed here, though framed as classification over a fixed statute "
  "label set rather than as open retrieval with citation. JEC-QA [20] and "
  "LegalBench [21] provide evaluation frameworks for legal reasoning, both "
  "oriented towards professional examination questions rather than the lay queries "
  "this project targets.", space_after=8)

h2("2.5 Hallucination and Attribution in Legal AI")
p("The empirical literature on legal hallucination is recent and directly "
  "motivating. Dahl et al. profiled hallucination in general-purpose models on "
  "legal queries and found rates between 58 % and 82 %, with a pronounced tendency "
  "towards confident fabrication of citations [1]. Magesh et al. extended this to "
  "commercial retrieval-augmented legal research products and found that "
  "retrieval augmentation reduces but does not eliminate unfaithful output [2]. "
  "The conclusion drawn in this project is that retrieval alone is an insufficient "
  "guarantee, and that an explicit post-generation check of whether cited "
  "authorities appeared in the retrieved set is a necessary additional stage.",
  space_after=8)

h2("2.6 Agentic Orchestration and Self-Verification")
p("Decomposing a task across cooperating model calls with explicit control flow is "
  "now a standard pattern. ReAct [22] interleaves reasoning with tool use; "
  "Reflexion [23] adds verbal self-critique and retry. LangGraph expresses such "
  "designs as a state machine with typed state and conditional edges, which suits "
  "this problem because the required control flow is genuinely non-linear: one "
  "branch terminates early to ask the user a question, and another returns a failed "
  "answer to be rewritten. Evaluation of retrieval-augmented pipelines is addressed "
  "by RAGAS [24], which proposes reference-free faithfulness and context-relevance "
  "measures.", space_after=8)

h2("2.7 Summary of Prior Work")
table([
    ["System / approach", "Grounds answers", "Cites section", "Verifies citation",
     "Jurisdiction aware", "Indian statute"],
    ["General-purpose LLM", "No", "Sometimes, often wrong", "No", "No", "Partially"],
    ["BM25 statute search", "Yes", "Yes", "n/a (no generation)", "No", "Yes"],
    ["Dense RAG baseline", "Yes", "Sometimes", "No", "No", "Depends on corpus"],
    ["LeSICiN [19]", "Yes", "Yes (classification)", "n/a", "No", "Yes"],
    ["Commercial legal research tools [2]", "Yes", "Yes", "Partially", "Varies", "No"],
    ["CivicConnect (this work)", "Yes", "Yes", "Yes, enforced", "Yes, asks when unknown", "Yes"],
], "Table 1. Comparison with representative existing approaches.",
   widths=[1.5, 0.85, 1.1, 1.0, 1.0, 0.95], size=8)

# ----------------------------------------------------------- CHAPTER 3
h1("Chapter 3")
p("Research Gap and Proposed System", size=H1, bold=True, align=L, space_after=14, line=1.2)

h2("3.1 Identified Research Gaps")
for g in [
    "G1 — Indian legal NLP research concentrates on judgments and on professional "
    "tasks such as judgment prediction and statute classification. Lay-facing "
    "question answering over consolidated bare Acts is comparatively unaddressed.",
    "G2 — Retrieval-augmented systems return passages but rarely enforce that the "
    "generated answer cites only those passages. Retrieval is treated as sufficient "
    "for grounding; the empirical work in [2] shows that it is not.",
    "G3 — Federal structure is seldom modelled. Systems answer as though a single "
    "national rule exists, and have no mechanism for declaring that the answer "
    "depends on a jurisdiction the user has not supplied.",
    "G4 — Statutory text is versioned, but corpora are usually undated. Without "
    "effective dates a system cannot distinguish a repealed provision from a "
    "current one.",
    "G5 — The superiority of hybrid over dense retrieval is widely asserted and "
    "rarely re-measured per corpus, despite BEIR [10] showing that relative "
    "performance is domain-dependent.",
    "G6 — Corpus construction from statutory PDFs is treated as a preprocessing "
    "detail. In practice it is where most silent data loss occurs, and it is almost "
    "never validated or reported.",
]:
    bullet(g)
p("CivicConnect addresses all six. G5 and G6 in particular are addressed by "
  "measurement and disclosure rather than by a new technique, and the results are "
  "reported in Chapter 4 whether or not they flatter the design.", space_after=8)

h2("3.2 System Overview")
p("The system is a state machine over a typed state object, compiled with LangGraph. "
  "Five nodes and two conditional edges are shown in Figure 1. A straight-line "
  "pipeline would have sufficed for the common case; the two branches exist because "
  "the two situations they handle are precisely the situations in which a confident "
  "wrong answer would be most damaging.", space_after=8)
figure("fig1_architecture.png",
       "Figure 1. The CivicConnect orchestration graph. The clarification exit "
       "terminates without an answer when the question is state-dependent and no "
       "state is known; the verification loop returns an answer for rewriting when "
       "it cites authority that retrieval did not supply. After the retry budget is "
       "exhausted the answer is returned marked unverified rather than passed off "
       "as checked.")
rich([("Query understanding ", True, False),
      ("extracts the jurisdiction, any temporal qualifier and the intent of the "
       "question, and decides whether the question can be answered without knowing "
       "the user's state.", False, False)], space_after=6)
rich([("Retrieval ", True, False),
      ("runs the dense and sparse arms, fuses their rankings, applies jurisdiction "
       "and date filters, and returns the top ten chunks.", False, False)], space_after=6)
rich([("Synthesis ", True, False),
      ("prompts the language model with those chunks and the instruction to answer "
       "only from them, in plain language, naming the sections relied upon.",
       False, False)], space_after=6)
rich([("Verification ", True, False),
      ("extracts every section number the answer names and checks set containment "
       "against the sections actually retrieved.", False, False)], space_after=8)

h2("3.3 Corpus Construction and Provenance")
p("The corpus is the part of the system that determines its ceiling, and it was the "
  "most laborious part to build correctly. Four Acts were chosen to span distinct "
  "areas of everyday legal exposure: criminal liability, road traffic, consumer "
  "rights and access to government information.", space_after=8)
table([
    ["Source", "Chunks", "Sections parsed", "Provenance"],
    ["Bharatiya Nyaya Sanhita, 2023", "460", "358 of 358", "India Code consolidated PDF"],
    ["Motor Vehicles Act, 1988", "428", "257 of 257, plus 6 state amendments",
     "India Code consolidated PDF, current to 2026-08-15"],
    ["Consumer Protection Act, 2019", "47", "curated provisions", "India Code"],
    ["Right to Information Act, 2005", "10", "curated provisions", "India Code"],
    ["Welfare schemes (central and state)", "18", "n/a", "MyScheme portal, hand-curated"],
    ["Total indexed", "963", "", ""],
], "Table 2. Corpus sources and provenance. Every chunk carries its Act, chapter, "
   "section, jurisdiction, effective date, assent date, source URL, extraction "
   "method, source page and a SHA-256 digest of both the chunk text and the parsed "
   "source.", widths=[2.0, 0.7, 1.7, 1.9], size=8.5)
figure("fig3_corpus.png",
       "Figure 2. Left: composition of the indexed corpus. Right: distribution of "
       "chunk lengths. Sections longer than 1 500 characters are divided only at "
       "boundaries the drafter provided — sub-sections, Explanations, Illustrations, "
       "Exceptions and provisos — so that no chunk ends mid-sentence and every "
       "fragment remains quotable.")
p("Two design rules governed chunking. First, text is kept verbatim: a citation is "
  "worthless if the text it points at is a paraphrase. Second, a section is split "
  "only at statutory boundaries, and each fragment is labelled with its sub-section "
  "so that it remains identifiable in isolation. The median chunk is 785 characters "
  "and the longest is 5 525 — a small number of sections, chiefly those carrying ten "
  "numbered Exceptions under a single sub-section, admit no further lawful division "
  "and are left intact rather than cut mid-sentence.", space_after=8)
p("Parsing consolidated statutory PDFs proved considerably harder than anticipated, "
  "and the parsers were therefore written to validate their own output and to refuse "
  "to write a file when any check fails. The checks assert the expected section "
  "count, the absence of duplicates and gaps, monotonic section ordering, the "
  "presence of a title and chapter for every section, and the absence of page "
  "furniture in the body text.", space_after=8)
table([
    ["Check", "BNS 2023", "MV Act 1988"],
    ["Expected sections recovered", "358 of 358", "257 of 257"],
    ["Duplicate section numbers", "0", "0"],
    ["Gaps in numbering", "0", "0"],
    ["Sections missing a title", "0", "0"],
    ["Sections missing a chapter", "0", "0"],
    ["Page furniture leaked into text", "0", "0 (875 fragments stripped)"],
    ["State amendments recovered", "n/a", "6"],
], "Table 3. Parser validation results. A parse that fails any row produces no "
   "output file at all.", widths=[2.6, 1.6, 2.1], size=8.5)

h2("3.4 Hybrid Retrieval and Rank Fusion")
p("Retrieval runs two independent arms over the same corpus and fuses their "
  "rankings, as shown in Figure 3. The dense arm embeds the query with "
  "all-MiniLM-L6-v2 into 384 dimensions and searches a FAISS inner-product index "
  "over L2-normalised vectors, which is cosine similarity. The sparse arm tokenises "
  "into lowercased alphanumeric runs and scores with Okapi BM25.", space_after=8)
figure("fig2_hybrid.png",
       "Figure 3. Hybrid retrieval. Both arms run over the same 963 chunks; "
       "Reciprocal Rank Fusion combines their rankings without requiring their "
       "scores to be commensurable, and jurisdiction and date filters are applied "
       "after fusion.")
p("Two details of the sparse arm are worth recording because both were corrected "
  "during development and both mattered. Tokenisation originally split on "
  "whitespace alone, leaving punctuation attached, so that the query token "
  "“request?” failed to match the document token “request.” — and the Right to "
  "Information Act section that answers a question about reply deadlines ranked "
  "54th instead of 1st. Separately, function words are now removed from the query "
  "but never from documents, because in statutory text small words carry operative "
  "meaning: “not”, “shall”, “may” and “within” change what a provision does, and are "
  "deliberately excluded from the stop list.", space_after=8)

h2("3.5 Synthesis and the Grounding Contract")
p("Synthesis is a single call to a hosted large language model, currently Groq's "
  "qwen3.8-27b, prompted with the retrieved chunks and instructed to answer only "
  "from them, in language a non-specialist can act on, naming the sections relied "
  "upon. The output token budget is capped at 800, a constraint imposed by the free "
  "tier's limit of 1 000 output tokens per minute; exceeding it causes the provider "
  "to refuse the request outright rather than truncate, a failure mode that "
  "initially presented as intermittent unreliability.", space_after=8)

h2("3.6 The Verification Agent")
p("The grounding contract is enforced rather than requested. After synthesis, every "
  "section number appearing in the answer is extracted and tested for membership in "
  "the set of sections retrieval returned.", space_after=8)
figure("fig8_verification.png",
       "Figure 4. The verification contract. An answer citing authority that "
       "retrieval did not supply is returned for rewriting at most twice, after "
       "which it is surfaced with its verification flag false.", width=5.9)
p("This is a deliberately narrow check. It establishes that the answer cites only "
  "what it was shown; it does not establish that the answer characterises those "
  "provisions correctly. The distinction is stated plainly because conflating the "
  "two would overclaim precisely the property the project exists to provide.",
  space_after=8)

h2("3.7 Deployment Architecture")
p("The system is deployed on free-tier infrastructure, which imposed every "
  "significant constraint on the architecture.", space_after=8)
figure("fig7_deployment.png",
       "Figure 5. Deployment architecture. A statically built Astro frontend is "
       "served from Cloudflare's edge network; the FastAPI backend and a Gradio "
       "diagnostic interface share port 7860 on a Hugging Face Space; synthesis "
       "calls out to Groq.")
p("The frontend is an Astro 7 application with React islands, built to static "
  "HTML and served by Cloudflare Pages. The API base URL is inlined at build time, "
  "so the deployed bundle is bound to a specific backend rather than resolving one "
  "at runtime. The backend runs as a Hugging Face Space on ZeroGPU hardware, the "
  "only free tier available for the Gradio SDK, with FastAPI serving the REST "
  "endpoints and a mounted Gradio interface available at /gradio for diagnostics.",
  space_after=8)
p("The most consequential deployment decision was not to ship the search indexes. "
  "Hugging Face rejects binary files in a Space repository irrespective of size, and "
  "when the same files were pushed through Git LFS the push succeeded but the files "
  "did not materialise in the running container. Since the indexes are derived data, "
  "the resolution was to derive them: on every cold start the Space seeds its SQLite "
  "database from the corpus JSON, embeds the 963 chunks and builds both indexes "
  "before the API begins serving. This costs one to three minutes on a cold start "
  "and carries a compensating benefit — the indexes cannot fall out of step with the "
  "corpus, because they are built from the corpus that was just loaded.", space_after=8)

h2("3.8 Technology Stack")
table([
    ["Layer", "Technology", "Rationale"],
    ["Ingestion", "pdftotext -layout, custom Python parsers",
     "Layout mode preserves form feeds, which carry page numbers used for citation anchors"],
    ["Storage", "SQLAlchemy 2.0 over SQLite",
     "Single-file database suits a free-tier container; all access confined to one module"],
    ["Embeddings", "sentence-transformers all-MiniLM-L6-v2 (384-d)",
     "Runs on CPU within free-tier memory; 22 M parameters"],
    ["Dense index", "FAISS IndexFlatIP over normalised vectors",
     "Exact search; at 963 chunks an approximate index would add error for no benefit"],
    ["Sparse index", "rank_bm25 (Okapi BM25)", "No training required, fully inspectable"],
    ["Fusion", "Reciprocal Rank Fusion, k = 5, dense weight 3.0",
     "Avoids score normalisation between incommensurable rankers"],
    ["Orchestration", "LangGraph StateGraph", "Typed state with explicit conditional edges"],
    ["Generation", "Groq API, qwen3.8-27b", "Free tier with usable latency"],
    ["API", "FastAPI with Pydantic schemas", "Typed request and response contracts, generated OpenAPI docs"],
    ["Frontend", "Astro 7, React 19, Tailwind CSS 4", "Static output, minimal client JavaScript"],
    ["Hosting", "Cloudflare Pages and Hugging Face Spaces", "Free tier, no card required"],
], "Table 4. Technology stack by layer.", widths=[1.1, 1.9, 3.2], size=8.5)

# ----------------------------------------------------------- CHAPTER 4
h1("Chapter 4")
p("Results and Discussions", size=H1, bold=True, align=L, space_after=14, line=1.2)

h2("4.1 Evaluation Design")
p("Retrieval is evaluated as recall@10: for each question, whether the chunk "
  "containing the provision that answers it appeared in the ten chunks returned. "
  "Recall is reported separately from citation accuracy on purpose. High recall with "
  "poor citation accuracy means synthesis is misusing material it was given; low "
  "recall means retrieval never gave it the chance. These are different defects "
  "requiring different remedies, and a combined score conceals which one is present.",
  space_after=8)
p("Because several numbers recur throughout this chapter, Table 5 states in "
  "plain words what each one counts and how it was obtained, so that no figure "
  "in this report has to be taken on trust or quoted without understanding.",
  space_after=8)
table([
    ["Number or term", "What it means in plain words", "Where it comes from"],
    ["recall@10",
     "Retrieval hands ten chunks to the answer writer. Recall@10 asks one "
     "question: was the chunk containing the correct provision among those ten "
     "at all? 77 % means it was, for 77 of every 100 questions asked.",
     "The retrieved chunk identifiers are compared with the section recorded as "
     "correct for that question in questions.json."],
    ["963 chunks",
     "The number of separately searchable pieces the corpus is cut into. One "
     "chunk is normally one section of an Act; a section too long to keep whole "
     "becomes two or three chunks, split at a sub-section boundary.",
     "945 statutory chunks from four Acts, plus 18 welfare schemes."],
    ["109 answerable questions",
     "The test set. Each question has one section written down in advance as "
     "its correct answer, which is what makes automatic scoring possible.",
     "Written by the team in everyday language, not in the wording of the Acts."],
    ["6 unanswerable questions",
     "Questions the corpus genuinely cannot answer, included on purpose to test "
     "whether the system admits it instead of inventing a provision.",
     "Marked answerable: false in the question set."],
    ["± 4.0 percentage points",
     "The standard error: how far a percentage can drift by chance alone when "
     "it is measured on only 109 questions. Two results closer together than "
     "roughly twice this are not meaningfully different from each other.",
     "√(p(1−p)/n) with p = 0.77 and n = 109."],
    ["13.8 % lexical overlap",
     "How many of the words in a question also appear in the chunk that answers "
     "it. A LOW number is the good one here: it means retrieval had to work out "
     "what the question meant rather than match its words.",
     "Measured per question against its target chunk, then averaged."],
    ["2.8 percentage points",
     "The share of questions that the sparse arm alone rescued — 3 questions out "
     "of 109. Smaller than the ± 4.0 above, which is why the report treats it as "
     "indistinguishable from chance rather than as a gain.",
     "Questions found by BM25 and missed by dense retrieval."],
    ["k = 5",
     "A dial inside the fusion formula. A smaller k makes the two search methods "
     "agreeing with each other count for more, relative to either one being very "
     "confident on its own.",
     "Chosen by sweeping k and measuring recall; the library default is 60."],
    ["384 dimensions",
     "The length of the list of numbers used to stand for the meaning of a chunk. "
     "Two chunks with similar meaning end up with similar lists.",
     "Fixed by the all-MiniLM-L6-v2 embedding model."],
], "Table 5. How to read the numbers in this report. Every quantity quoted in "
   "Chapter 4 is defined here, with the calculation behind it, so that a figure "
   "can be explained rather than merely repeated.",
   widths=[1.1, 3.0, 2.2], size=8)
table([
    ["Property", "Value"],
    ["Total questions", "115"],
    ["Answerable from the corpus", "109"],
    ["Deliberately unanswerable", "6"],
    ["Consumer Protection Act, 2019", "36"],
    ["Bharatiya Nyaya Sanhita, 2023", "22"],
    ["Motor Vehicles Act, 1988", "18"],
    ["Right to Information Act, 2005", "14"],
    ["Welfare schemes", "19"],
    ["Mean lexical overlap with the target chunk", "13.8 %"],
], "Table 6. Composition of the evaluation question set.", widths=[3.6, 1.6], size=8.5)
p("The lexical overlap figure deserves emphasis because an earlier version of the "
  "question set was invalid. Those questions had been written while reading the "
  "corpus, and carried 25 % mean lexical overlap with the chunks they targeted; one "
  "reached 83 %. A question that reuses the wording of the provision answering it "
  "measures nothing but string matching, and inflates the sparse arm in particular. "
  "Nineteen such questions were rewritten in the register a citizen would actually "
  "use, bringing mean overlap to 13.8 %. Every figure in this chapter is measured on "
  "the rewritten set.", space_after=8)
p("A second methodological correction is recorded for the same reason. An earlier "
  "evaluation scored citation groundedness by checking cited sections against the "
  "retrieved chunks — but the citations were drawn from those chunks by "
  "construction, so the metric was tautological and reported near-perfect scores "
  "while measuring nothing. A companion metric for citation correctness merely "
  "restated recall. Both were removed.", space_after=8)

h2("4.2 Corpus Construction Results")
p("Eleven defects were found during parser development, each of which silently "
  "discarded statutory text while allowing the parse to report success. They are "
  "tabulated because the category — a pipeline that loses data without failing — is "
  "the single most important practical lesson of the project.", space_after=8)
table([
    ["Defect", "Silent consequence", "Detection"],
    ["Section headings written “115.(1)” without a space",
     "15 BNS sections lost", "Expected-count assertion"],
    ["Table-of-contents entries 348–358 carry a leading space",
     "11 BNS sections lost", "Gap detection in numbering"],
    ["India Code watermark interleaved into body text",
     "Corrupted text, e.g. “od with fine” inside s.185", "Leaked-token scan"],
    ["Superscript amendment marker absorbed the first digit",
     "MV s.10 parsed as section 0", "Ordering assertion"],
    ["Section 217A absorbed trailing schedules",
     "6 471 extraneous characters in one chunk", "Length outlier review"],
    ["Marginal notes used as titles",
     "128 of 358 BNS titles truncated", "Manual comparison against the Arrangement of Sections"],
    ["Chapter titles wrapping across two lines",
     "Chapter attribution lost", "Missing-chapter assertion"],
    ["Sub-heading indentation ambiguity at s.357",
     "Mis-attributed sub-heading", "Title-completeness heuristic"],
    ["Whitespace tokenisation retaining punctuation",
     "RTI s.7 ranked 54th instead of 1st on its own question", "Retrieval spot-check"],
    ["Corpus fingerprint computed over raw bytes",
     "Index refused to load on every machine but the one that built it",
     "Cross-platform CI failure"],
    ["Pre-2019 edition of the MV Act supplied as source",
     "Penalties would have been understated by an order of magnitude",
     "Edition-marker check"],
], "Table 7. Silent defects caught by parser validation. Every one of these "
   "permitted the parse to complete successfully.", widths=[2.1, 2.1, 2.0], size=8)

h2("4.3 Retrieval Performance at Two Corpus Scales")
p("The pilot corpus of 75 chunks was evaluated against 69 questions; the full corpus "
  "of 963 chunks against 109. The two are not directly comparable — both the corpus "
  "and the question set changed — but the direction is unambiguous and instructive.",
  space_after=8)
figure("fig4_recall_scale.png",
       "Figure 6. Retrieval recall@10 before and after the corpus grew by a "
       "factor of 12.8. Each bar is the percentage of questions whose answering "
       "provision was among the ten chunks retrieved. The pale bar is the small "
       "pilot corpus, the solid bar the full one. Every arm falls as the corpus "
       "grows, because there is more to confuse it with; the sparse arm falls "
       "furthest.", width=5.4)
table([
    ["Retrieval arm", "Pilot corpus (75 chunks, 69 questions)",
     "Full corpus (963 chunks, 109 questions)", "Change"],
    ["Dense (FAISS, MiniLM)", "97 %", "77 %", "−20 points"],
    ["Hybrid (RRF, tuned)", "91 %", "77 %", "−14 points"],
    ["Sparse (BM25)", "71 %", "42 %", "−29 points"],
], "Table 8. Retrieval recall@10 at two corpus scales. Read a row as: out of "
   "every 100 questions, this is how many had the right provision somewhere in "
   "the ten chunks retrieval returned. The two columns are different corpora "
   "and different question sets, so compare the direction of travel rather than "
   "subtracting one from the other.",
   widths=[1.5, 1.8, 1.8, 0.9], size=8.5)
p("Three observations follow. First, pilot-scale figures are not predictive: a "
  "system reporting 97 % on 75 chunks reported 77 % on 963, and any claim resting "
  "on the smaller number would have been misleading. Second, BM25 degrades fastest, "
  "which is expected — its inverse document frequency term stays positive however "
  "common a word becomes, so a longer document list gives function words more "
  "opportunity to accumulate score against genuine content terms. Third, the hybrid "
  "arm began below dense and only reached parity after the tuning described in "
  "Section 4.6.", space_after=8)

h2("4.4 Per-Act Breakdown")
figure("fig5_per_act.png",
       "Figure 7. Recall@10 by source Act on the full corpus. Read each group of "
       "three bars as one Act: blue is dense retrieval, orange is BM25, green is "
       "the two fused. The green bar equals the blue bar in every group, which is "
       "the finding of Section 4.5 — fusing the two adds nothing that dense "
       "retrieval had not already found.", width=5.9)
table([
    ["Source", "Questions", "Dense", "BM25", "Hybrid"],
    ["Welfare schemes", "19", "100 %", "84 %", "100 %"],
    ["Consumer Protection Act, 2019", "36", "78 %", "50 %", "78 %"],
    ["Motor Vehicles Act, 1988", "18", "78 %", "28 %", "78 %"],
    ["Right to Information Act, 2005", "14", "64 %", "29 %", "64 %"],
    ["Bharatiya Nyaya Sanhita, 2023", "22", "64 %", "14 %", "64 %"],
    ["All answerable questions", "109", "77 %", "42 %", "77 %"],
], "Table 9. Recall@10 by source Act on the full corpus. The questions column "
   "gives the sample each percentage rests on, which matters: 64 % of the 22 "
   "BNS questions is 14 questions found and 8 missed. The point of the table is "
   "the Dense and Hybrid columns, which hold the same value in every row.",
   widths=[2.2, 0.9, 0.8, 0.8, 0.8], size=8.5)
p("The spread across Acts is wider than the aggregate suggests and is explained by "
  "corpus density rather than by retrieval quality. Welfare schemes are few, "
  "distinctive and described in the vocabulary applicants use, so they are nearly "
  "always found. The Bharatiya Nyaya Sanhita is the opposite case: 460 chunks of "
  "criminal provisions sharing a formulaic register — “whoever … shall be punished "
  "with imprisonment … which may extend to …” — so that many sections are mutual "
  "near-neighbours in embedding space, and discriminating among them requires the "
  "specific offence term to dominate a great deal of shared boilerplate. BM25's 14 % "
  "on that Act reflects the same phenomenon from the lexical side.", space_after=8)

h2("4.5 The Central Finding: Hybrid Retrieval Did Not Beat Dense")
p("The project set out to demonstrate that hybrid retrieval outperforms dense "
  "retrieval. It does not, on this corpus, and the result is reported as measured.",
  space_after=8)
p("After tuning, hybrid retrieval returns dense retrieval's result set exactly: the "
  "same 84 of 109 questions are answered, none gained and none lost, and the "
  "per-Act columns in Table 9 are identical row by row. The sparse arm contributes "
  "nothing that the dense arm had not already supplied. Across the whole question "
  "set, BM25 uniquely recovers three questions that dense retrieval misses — worth "
  "2.8 percentage points, against a standard error of approximately 4.0 points on a "
  "sample of 109. The contribution is not distinguishable from zero.", space_after=8)
p("Why the complementarity failed to materialise is itself informative. The two "
  "arms are complementary only where they make different mistakes. Here they "
  "largely do not: the questions dense retrieval misses are predominantly questions "
  "whose target chunk shares its vocabulary with dozens of sibling provisions, and "
  "those are precisely the chunks BM25 also cannot separate, because the "
  "discriminating term is rare while the shared boilerplate is abundant. Where the "
  "two arms fail, they fail for the same underlying reason, and fusing two rankers "
  "that are wrong together cannot recover the answer.", space_after=8)
p("Two conclusions follow, and the second matters more than the first. The narrow "
  "conclusion is that for this corpus the sparse arm could be removed with no "
  "measurable loss of recall, and the report states so. The broader conclusion "
  "concerns method: the superiority of hybrid retrieval is widely asserted as "
  "general knowledge, and it was assumed at the outset of this project. It was "
  "measured only because the evaluation was built to compare arms rather than to "
  "confirm a design already chosen. BEIR [10] documents exactly this domain "
  "dependence, and this corpus is another instance of it.", space_after=8)
p("The sparse arm is nonetheless retained in the deployed system, for a reason "
  "outside the measurement. Users ask questions of the form “what does section 185 "
  "say”, in which an exact identifier is the entire query. Dense embeddings handle "
  "numeric identifiers poorly; BM25 handles them exactly. The evaluation set "
  "contains few such questions, so this strength is invisible in Table 9 while being "
  "real in use. Section 5.3 proposes replacing the general sparse arm with a "
  "dedicated exact-match channel for section identifiers, which would serve that "
  "need at a fraction of the cost.", space_after=8)

h2("4.6 Tuning Interventions and Their Measured Effect")
figure("fig6_tuning.png",
       "Figure 8. The two tuning interventions that moved retrieval most, each "
       "measured on its own with everything else held fixed. In both panels the "
       "grey bar is before the change and the coloured bar after, so the height "
       "difference is what that one change was worth.", width=5.9)
p("Removing function words from the query — never from documents — raised sparse "
  "recall from 30 % to 55 % over the 69-question set then in use, fixing seventeen "
  "questions and breaking none. The mechanism is the inverse document frequency "
  "formulation: rank_bm25 computes log(1 + (N − df + 0.5)/(df + 0.5)), which remains "
  "positive however common a term is. At 75 chunks there was nothing for function "
  "words to accumulate against; at 963 they outweighed content terms entirely. On "
  "the question “How long does a public authority have to respond to an RTI "
  "request?”, the Right to Information Act section 7 chunk ranked 2nd at 75 chunks "
  "and 35th at 963, because two of the three words carrying the query contributed "
  "nothing — the Act says “reply” rather than “respond”, and spells its own name out "
  "rather than writing “RTI”.", space_after=8)
p("Retuning the fusion constant raised hybrid recall from 68 % to 77 %. The "
  "arithmetic is worth setting out, because the default is adopted almost "
  "universally without examination. At k = 60 with a 50-candidate pool, a chunk "
  "ranked 50th by both arms scores 2/110 = 0.0182 while a chunk ranked 1st by one "
  "arm alone scores 1/61 = 0.0164. Agreement wins, but only just, so fusion behaved "
  "almost like a union of two ranked lists and inherited the weaknesses of both. "
  "Lowering k to 5 makes the reciprocal decay steeply, so agreement between arms "
  "becomes decisive; weighting the dense arm at 3.0 against the sparse arm's 1.0 "
  "reflects their measured relative reliability on this corpus.", space_after=8)
table([
    ["Parameter", "Default", "Tuned", "Hybrid recall@10"],
    ["RRF constant k", "60", "5", "68 % → 77 %"],
    ["Dense weight", "1.0", "3.0", "(same intervention)"],
    ["Sparse weight", "1.0", "1.0", "unchanged"],
    ["Query function-word filter", "off", "on", "BM25 30 % → 55 %"],
], "Table 10. Fusion parameter tuning. The Default column is what the library "
   "ships with, the Tuned column is what this system now uses, and the last "
   "column is the recall measured before and after that single change.",
   widths=[1.8, 1.0, 1.0, 1.7], size=8.5)

h2("4.7 Failure Modes: A System That Looked Healthy")
p("One pattern recurred often enough during development to be reported as a finding "
  "rather than an anecdote: a broken state that presents as a working one. Four "
  "independent instances arose, in different components, written by different "
  "members of the team.", space_after=8)
for item in [
    "The frontend shipped with a built-in simulator returning canned answers "
    "indistinguishable in layout from real ones. A missing configuration file "
    "silently enabled it, so the application appeared to work perfectly while "
    "answering from a fixture.",
    "The /health endpoint returned HTTP 200 while the service was serving stub "
    "answers, because it reported that the process was alive rather than that the "
    "providers had loaded. An orchestrator watching the status code would never "
    "have noticed.",
    "The stub answer itself read as a plausible response. It was rewritten to open "
    "with an explicit statement that it is not a real answer.",
    "The stub answer was returned with its verification flag set true, so the "
    "interface displayed a green “Verified by law” badge directly above text that "
    "was not an answer at all.",
]:
    bullet(item)
p("The common structure is that each component reported on its own liveness rather "
  "than on its usefulness, and every layer above it took that report at face value. "
  "The remedy adopted throughout is that a degraded component must say so in terms "
  "the layer above can act on: /health now reports a serving_real_answers field "
  "distinct from its status code, and the verification flag is computed from the "
  "answer's content rather than assumed.", space_after=8)

h2("4.8 Deployment Results")
p("The deployed system serves real grounded answers. Its health endpoint reports "
  "retrieval, synthesis and query logging all operating against real components. "
  "Reaching that state required four distinct failures to be diagnosed, three of "
  "which were invisible in the application logs until the final line.", space_after=8)
table([
    ["Failure", "Symptom", "Cause", "Resolution"],
    ["ZeroGPU startup check",
     "“No @spaces.GPU function detected during startup”",
     "The free Gradio tier runs on ZeroGPU, which requires at least one "
     "GPU-decorated function even for a CPU-only workload",
     "Declare one such function, used by nothing in the answer path"],
    ["Port contention",
     "“[Errno 98] address already in use” on port 7860",
     "A Space sets GRADIO_SSR_MODE and GRADIO_SERVER_PORT; gradio's Node "
     "server-side-rendering proxy begins its port search at that port and took 7860 "
     "from the application itself",
     "Disable server-side rendering when mounting Gradio onto FastAPI"],
    ["Missing index artifacts",
     "“BM25 index not found” while a JSON file in the adjacent directory loaded "
     "normally",
     "The indexes were pushed via Git LFS and did not materialise in the container; "
     "pushed as ordinary files they are rejected as binaries",
     "Derive the indexes at boot from the seeded corpus"],
    ["Unset provider credential",
     "Health endpoint reported synthesis unavailable",
     "GROQ_API_KEY absent from the Space environment",
     "Stored as a Space secret"],
], "Table 11. Deployment failures encountered and their resolution.",
   widths=[1.15, 1.6, 2.1, 1.45], size=8)
p("The port contention is the most instructive of the four. Two deployment cycles "
  "were spent searching for an external process holding port 7860; the process "
  "holding it was the application's own Gradio mount, two lines above the code that "
  "failed. It was identified by reading gradio's source rather than by further "
  "inspection of the symptom, and confirmed by reproducing the failure locally with "
  "the Space's environment variables set.", space_after=8)
table([
    ["Period (2026)", "Phase", "Deliverables"],
    ["August", "Problem study and architecture",
     "Literature survey, problem formulation, LangGraph design, stub pipeline"],
    ["September", "Data layer and retrieval",
     "SQLAlchemy schema, seed corpus, FAISS and BM25 indexes, hybrid search"],
    ["October", "Corpus expansion",
     "BNS and MV Act parsers with validation, corpus grown from 57 to 945 chunks"],
    ["Early November", "Evaluation and tuning",
     "Question set rewritten, tautological metrics removed, fusion retuned"],
    ["Mid November", "Integration and deployment",
     "Frontend integration, Hugging Face Space, Cloudflare Pages, CORS"],
    ["Late November", "Documentation", "This report"],
], "Table 12. Project execution plan.", widths=[1.2, 1.7, 3.3], size=8.5)

h2("4.9 Threats to Validity")
for t in [
    "The question set was written by the project team, who knew the corpus. Lexical "
    "overlap was measured and reduced to 13.8 % to control for this, but "
    "author-written questions remain a weaker instrument than questions collected "
    "from real users.",
    "109 answerable questions give a standard error of roughly 4 percentage points "
    "on a proportion near 0.77. Differences smaller than about 8 points should not "
    "be treated as real, which is precisely why the hybrid-versus-dense comparison "
    "is reported as indistinguishable rather than as a narrow win for either.",
    "Recall@10 measures whether the answering chunk was retrieved, not whether the "
    "generated answer used it correctly. Answer quality is not quantified in this "
    "report.",
    "Refusal behaviour on the six deliberately unanswerable questions is implemented "
    "but not yet measured.",
    "The corpus covers four Acts. Results on criminal and traffic law may not "
    "transfer to areas with different drafting conventions, such as taxation.",
]:
    bullet(t)

# ----------------------------------------------------------- CHAPTER 5
h1("Chapter 5")
p("Conclusions and Future Work", size=H1, bold=True, align=L, space_after=14, line=1.2)

h2("5.1 Conclusions")
p("CivicConnect demonstrates that a grounded, citation-bearing assistant for Indian "
  "statutory law can be built and publicly deployed by a student team on free "
  "infrastructure. A corpus of 963 chunks was constructed from four Acts and "
  "eighteen welfare schemes by self-validating parsers that refuse to emit output "
  "when a document fails its structural checks — a discipline that caught eleven "
  "defects, every one of which would otherwise have silently discarded statutory "
  "text. A LangGraph state machine orchestrates query understanding, retrieval, "
  "synthesis and verification, with two conditional edges that exist specifically to "
  "prevent confident wrong answers: the system asks which state the user is in "
  "rather than guessing, and refuses to present an answer citing authority that "
  "retrieval did not supply.", space_after=8)
p("Dense retrieval reaches 77 % recall@10 over 109 everyday-language questions — "
  "for 77 questions in every 100, the provision that answers the question was "
  "among the ten passages retrieval returned. "
  "Tuned hybrid retrieval reaches the same figure, returning dense retrieval's exact "
  "result set. The project's founding assumption — that hybrid retrieval would beat "
  "dense retrieval — did not hold, and the report says so, with the arithmetic "
  "explaining why and the standard error establishing that the sparse arm's apparent "
  "contribution is indistinguishable from noise. That negative result is the most "
  "transferable thing the project produced, because the assumption it refutes is "
  "widely held and rarely re-tested per corpus.", space_after=8)
p("The limitation most relevant to any real deployment is stated plainly. 77 % "
  "recall means that roughly one question in four never reaches the provision that "
  "answers it, and on the Bharatiya Nyaya Sanhita the figure is closer to one in "
  "three. The system is honest about this — it attaches its sources, so a user can "
  "see what it relied on — but it is an assistant for finding and understanding "
  "provisions, not an authority to be relied upon without checking, and the "
  "interface says so.", space_after=8)

h2("5.2 Learning Outcomes")
for lo in [
    "Recognising that a pipeline can lose data without failing, and that the only "
    "defence is a parser that validates its own output and refuses to write a file "
    "when a check fails.",
    "Learning that an evaluation can measure nothing while reporting excellent "
    "numbers — a groundedness metric that compared citations against the chunks they "
    "were drawn from, and questions written in the corpus's own vocabulary.",
    "Understanding that library defaults encode the assumptions of the setting they "
    "were tuned in: the RRF constant k = 60 is reasonable for its original "
    "experiments and cost nine points of recall here.",
    "Reporting a negative result rather than tuning until the preferred conclusion "
    "appeared, and computing the standard error that establishes the contribution is "
    "indistinguishable from zero.",
    "Diagnosing failures from first principles — the port contention was found by "
    "reading a library's source and reproducing the environment, after two cycles "
    "spent searching for an external cause that did not exist.",
    "Distinguishing a service that is alive from a service that is useful, after "
    "four independent instances of a component reporting health while serving "
    "fixtures.",
    "Building a complete system rather than a model: ingestion, storage, retrieval, "
    "orchestration, API, interface, deployment and evaluation.",
]:
    bullet(lo)

h2("5.3 Future Work")
p("The directions below follow from the measurements in Chapter 4 rather than from "
  "a general wish list, and each is paired with the metric that would establish "
  "whether it worked.", space_after=8)

h3("5.3.1 Raise the dense ceiling, because it is the system's ceiling")
p("Section 4.5 established that the sparse arm contributes nothing measurable, which "
  "means the dense arm alone determines performance. The embedding model is "
  "general-purpose all-MiniLM-L6-v2, trained on web text, asked to separate "
  "criminal provisions that differ by one offence term in a page of shared "
  "boilerplate. Two interventions follow. Substituting a legal-domain encoder such "
  "as InLegalBERT [16] would test whether domain pre-training transfers from "
  "judgments to bare Acts. More promisingly, the corpus itself supplies training "
  "data: each chunk's section heading paraphrases its content, so (heading, body) "
  "pairs can be mined as positives and sibling sections within the same chapter as "
  "hard negatives, giving a contrastive fine-tuning set of several thousand pairs at "
  "no annotation cost. Success criterion: BNS recall@10 above its present 64 %.",
  space_after=8)

h3("5.3.2 A dedicated exact-match channel for section identifiers")
p("Rather than retaining a general sparse arm that contributes nothing measurable, "
  "replace it with a narrow index over section identifiers and Act short names, "
  "consulted only when the query contains something of the shape of a citation. This "
  "serves the “what does section 185 say” query exactly, at a fraction of BM25's "
  "cost and complexity. Success criterion: near-perfect recall on a new evaluation "
  "slice consisting entirely of identifier queries, which the present question set "
  "lacks.", space_after=8)

h3("5.3.3 Cross-reference expansion over a statutory citation graph")
p("Statutes are densely self-referential: a provision routinely states that a term "
  "has the meaning assigned in another section, or that a penalty applies subject to "
  "another chapter. Retrieval currently treats each chunk as independent, so a "
  "question whose answer requires an operative section and its definition can only "
  "succeed if both happen to rank in the top ten. Extracting internal "
  "cross-references at ingestion — they are formulaic enough to capture reliably — "
  "would yield a directed graph over chunks, and retrieval could expand one hop "
  "along it before fusion. Success criterion: recall on a labelled subset of "
  "questions requiring two or more sections.", space_after=8)

h3("5.3.4 Cross-encoder re-ranking")
p("The present pipeline retrieves ten chunks and passes them to synthesis. "
  "Retrieving fifty and re-ranking with a cross-encoder that attends jointly over "
  "query and passage would address exactly the near-neighbour confusion that "
  "produces the BNS result, at a latency cost acceptable for a question-answering "
  "interface. Success criterion: recall@10 after re-ranking against recall@50 "
  "before it, which bounds the achievable gain.", space_after=8)

h3("5.3.5 Point-in-time retrieval over amendment history")
p("Every chunk carries an effective date, but the date is currently uniform across "
  "an Act because per-section commencement dates sit in footnotes attached to pages "
  "rather than to sections. Resolving footnote-to-section attribution — only 79 of "
  "the Motor Vehicles Act's 257 sections presently carry one — would permit "
  "point-in-time queries such as “what was the penalty for this in 2018”, currently "
  "unanswerable. This matters more than it sounds: an offence committed before an "
  "amendment is tried under the law as it stood.", space_after=8)

h3("5.3.6 Calibrated abstention")
p("The system presently answers or asks for clarification. It should also be able to "
  "decline. Six deliberately unanswerable questions exist in the evaluation set and "
  "refusal behaviour is implemented but unmeasured. A threshold on fused retrieval "
  "score, calibrated on those questions, would let the system say that the corpus "
  "does not cover the question — which, for a system whose value rests on "
  "trustworthiness, is a more valuable capability than a marginal recall "
  "improvement.", space_after=8)

h3("5.3.7 Corpus expansion along the paths users actually take")
p("The four Acts were chosen for breadth of everyday exposure, and the gaps are now "
  "evident. In priority order: the Bharatiya Nagarik Suraksha Sanhita 2023 and the "
  "Bharatiya Sakshya Adhiniyam 2023, which together with the BNS replaced the "
  "criminal code and are required for any procedural question; state Rent Control "
  "Acts, the most frequently asked area this corpus cannot touch; the Transfer of "
  "Property Act 1882; the Hindu Marriage Act 1955 and the Special Marriage Act 1954; "
  "and the four consolidated Labour Codes. Each addition should be accompanied by "
  "its own evaluation slice, because Section 4.3 showed that aggregate recall moves "
  "substantially with corpus size and a figure quoted without its corpus is "
  "meaningless.", space_after=8)

h3("5.3.8 A retrieval-failure feedback loop from the query log")
p("Every query is already logged with its retrieved chunk identifiers and "
  "verification verdict. That log is an unexploited asset: queries whose fused "
  "scores were uniformly low identify the questions the corpus cannot answer, "
  "ranked by how often real users ask them. This converts corpus expansion from "
  "guesswork into a prioritised, evidence-driven queue, and requires no new "
  "infrastructure — only analysis of data already being collected.", space_after=8)

h3("5.3.9 Multilingual access")
p("The corpus is English and the users are frequently not. Because retrieval is "
  "embedding-based, a multilingual sentence encoder would permit Hindi queries "
  "against the English corpus without translating the corpus, and synthesis can be "
  "instructed to answer in the language of the question while citing the English "
  "provision verbatim. For a system whose purpose is to make law accessible to "
  "people it currently excludes, this is arguably the highest-value extension in "
  "this list.", space_after=8)

h3("5.3.10 Operational hardening")
p("The free tier rebuilds the indexes on every cold start, costing one to three "
  "minutes before the first answer. Publishing the artifacts to a Hugging Face "
  "dataset repository and downloading them at boot — with the existing corpus "
  "fingerprint deciding whether the download is still valid — would reduce this to "
  "seconds while preserving the guarantee that an index never outlives its corpus.",
  space_after=8)

h2("5.4 Recommendations")
for rec in [
    "Re-measure rather than inherit. The one assumption this project did test — that "
    "hybrid retrieval beats dense — did not hold. Any component adopted because it "
    "is standard practice should be compared against its own ablation on the corpus "
    "at hand.",
    "Validate ingestion before optimising retrieval. Eleven silent parser defects "
    "cost more recall than every tuning intervention recovered, and none of them "
    "raised an error.",
    "Report the corpus with every number. Recall of 97 % and 77 % came from the same "
    "system; only the corpus differed. A retrieval figure quoted without its corpus "
    "size and question set is not a result.",
    "Make degradation loud. Four separate components reported health while serving "
    "fixtures. A health check should report whether the service is useful, not "
    "merely whether the process is alive.",
    "Treat the escalation path as a feature. For a system in a domain where a "
    "confident wrong answer causes real harm, the ability to say “I do not know” or "
    "“that depends on your state” is worth more than several points of recall.",
]:
    bullet(rec)

# --------------------------------------------------------------- REFERENCES
h1("REFERENCES")
refs = [
    "M. Dahl, V. Magesh, M. Suzgun, and D. E. Ho, “Large legal fictions: Profiling "
    "legal hallucinations in large language models,” Journal of Legal Analysis, 2024.",
    "V. Magesh, F. Surani, M. Dahl, M. Suzgun, C. D. Manning, and D. E. Ho, "
    "“Hallucination-free? Assessing the reliability of leading AI legal research "
    "tools,” Journal of Empirical Legal Studies, 2025.",
    "P. Lewis et al., “Retrieval-augmented generation for knowledge-intensive NLP "
    "tasks,” in Advances in Neural Information Processing Systems, 2020.",
    "Y. Gao et al., “Retrieval-augmented generation for large language models: A "
    "survey,” arXiv preprint, 2024.",
    "S. Robertson and H. Zaragoza, “The probabilistic relevance framework: BM25 and "
    "beyond,” Foundations and Trends in Information Retrieval, vol. 3, no. 4, "
    "pp. 333–389, 2009.",
    "V. Karpukhin et al., “Dense passage retrieval for open-domain question "
    "answering,” in Proc. EMNLP, 2020.",
    "N. Reimers and I. Gurevych, “Sentence-BERT: Sentence embeddings using siamese "
    "BERT-networks,” in Proc. EMNLP-IJCNLP, 2019.",
    "W. Wang, F. Wei, L. Dong, H. Bao, N. Yang, and M. Zhou, “MiniLM: Deep "
    "self-attention distillation for task-agnostic compression of pre-trained "
    "transformers,” in Advances in Neural Information Processing Systems, 2020.",
    "J. Johnson, M. Douze, and H. Jégou, “Billion-scale similarity search with GPUs,” "
    "IEEE Transactions on Big Data, vol. 7, no. 3, pp. 535–547, 2021.",
    "N. Thakur, N. Reimers, A. Rücklé, A. Srivastava, and I. Gurevych, “BEIR: A "
    "heterogeneous benchmark for zero-shot evaluation of information retrieval "
    "models,” in NeurIPS Datasets and Benchmarks Track, 2021.",
    "O. Khattab and M. Zaharia, “ColBERT: Efficient and effective passage search via "
    "contextualized late interaction over BERT,” in Proc. ACM SIGIR, 2020.",
    "T. Formal, B. Piwowarski, and S. Clinchant, “SPLADE: Sparse lexical and "
    "expansion model for first stage ranking,” in Proc. ACM SIGIR, 2021.",
    "G. V. Cormack, C. L. A. Clarke, and S. Buettcher, “Reciprocal rank fusion "
    "outperforms Condorcet and individual rank learning methods,” in Proc. ACM "
    "SIGIR, 2009, pp. 758–759.",
    "I. Chalkidis, M. Fergadiotis, P. Malakasiotis, N. Aletras, and I. Androutsopoulos, "
    "“LEGAL-BERT: The muppets straight out of law school,” in Findings of EMNLP, 2020.",
    "J. Devlin, M.-W. Chang, K. Lee, and K. Toutanova, “BERT: Pre-training of deep "
    "bidirectional transformers for language understanding,” in Proc. NAACL-HLT, 2019.",
    "S. Paul, A. Mandal, P. Goyal, and S. Ghosh, “Pre-trained language models for the "
    "legal domain: A case study on Indian law,” in Proc. International Conference on "
    "Artificial Intelligence and Law (ICAIL), 2023.",
    "V. Malik et al., “ILDC for CJPE: Indian legal documents corpus for court "
    "judgment prediction and explanation,” in Proc. ACL, 2021.",
    "P. Kalamkar et al., “Corpus for automatic structuring of legal documents,” in "
    "Proc. Language Resources and Evaluation Conference (LREC), 2022.",
    "S. Paul, P. Goyal, and S. Ghosh, “LeSICiN: A heterogeneous graph-based approach "
    "for automatic legal statute identification from Indian legal documents,” in "
    "Proc. AAAI Conference on Artificial Intelligence, 2022.",
    "H. Zhong, C. Xiao, C. Tu, T. Zhang, Z. Liu, and M. Sun, “JEC-QA: A legal-domain "
    "question answering dataset,” in Proc. AAAI Conference on Artificial "
    "Intelligence, 2020.",
    "N. Guha et al., “LegalBench: A collaboratively built benchmark for measuring "
    "legal reasoning in large language models,” in NeurIPS Datasets and Benchmarks "
    "Track, 2023.",
    "S. Yao et al., “ReAct: Synergizing reasoning and acting in language models,” in "
    "Proc. International Conference on Learning Representations (ICLR), 2023.",
    "N. Shinn, F. Cassano, E. Berman, A. Gopinath, K. Narasimhan, and S. Yao, "
    "“Reflexion: Language agents with verbal reinforcement learning,” in Advances in "
    "Neural Information Processing Systems, 2023.",
    "S. Es, J. James, L. Espinosa-Anke, and S. Schockaert, “RAGAS: Automated "
    "evaluation of retrieval augmented generation,” in Proc. EACL (System "
    "Demonstrations), 2024.",
    "Ministry of Law and Justice, Government of India, “India Code: Digital "
    "repository of all central and state acts.” [Online]. Available: "
    "https://www.indiacode.nic.in",
    "Government of India, “MyScheme: National platform for government schemes.” "
    "[Online]. Available: https://www.myscheme.gov.in",
]
for i, r in enumerate(refs, 1):
    par = doc.add_paragraph()
    par.alignment = J
    pf = par.paragraph_format
    pf.line_spacing = 1.3
    pf.space_after = Pt(5)
    pf.left_indent = Inches(0.35)
    pf.first_line_indent = Inches(-0.35)
    _font(par.add_run(f"[{i}] "), BODY)
    _font(par.add_run(r), BODY)

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print("written:", OUT, f"({OUT.stat().st_size // 1024} KB)")
