# Where to get authentic Indian legal and scheme data

A survey of sources for statutes, rules, regulations and welfare schemes, central
and state, with Madhya Pradesh covered first.

**Status of this document.** The URLs below were found by searching, not by
opening each one. Only the lines marked **verified** were actually loaded in a
browser. Everything else needs checking before anyone builds on it. This matters:
we have already shipped a URL from a search result that turned out to return 404
(issue #31). A search result is a lead, not a confirmation.

---

## The rule that decides everything else

Two different things get called "the source", and conflating them is what went
wrong in issues #22 and #31:

| field | meaning | may it be third-party? |
|---|---|---|
| `source_url` | where the text was fetched from; what `raw_sha256` hashes | **No.** Government only. |
| `reference_url` | a link a reader clicks to read the law | Yes, if `DATA_SOURCES.md` says so |

A third-party mirror is acceptable as a convenience link. It is never acceptable
as the provenance record, and no chunk text may ever come from one. The corpus is
the evidence base; a mirror is a courtesy.

---

## Central law

### India Code — `indiacode.gov.in` / `indiacode.nic.in`

The Legislative Department's repository of central Acts. This is where our 147
law chunks came from.

- No public API. The relaunch announced 13 August 2026 did not include one, so
  ingestion means scraping.
- **The whole host was unreachable on 14 November 2026** — handle pages and
  direct bitstream PDFs alike, returning Akamai errors. That looks like an
  outage rather than a permanent change, so re-check before concluding anything.
- Handle URLs serve whole Acts, not individual sections. This is why all 116
  Consumer Protection chunks share one `raw_sha256`, which is correct rather
  than a bug (issue #22).

### NyayKosh — `lawascode.negd.in`

National e-Governance Division. The only genuinely official API found.

- Free, no key. Each statute served four ways: plain-language text, PDF,
  **Akoma Ntoso XML** (the international standard for legislation), and
  versioned REST endpoints.
- **Covers four Acts**: DPDP 2023, Aadhaar 2016, IT Act 2000, Online Gaming
  Rules 2026. All digital-economy law — nothing on tenancy, consumer rights,
  RTI or welfare.
- So it does not help the current corpus, but it is the right long-term target.
  Worth citing in the report's future work: as the government's own law-as-code
  programme expands, ingestion could consume Akoma Ntoso directly instead of
  scraping HTML.

### Statute-specific official sites

Often more reliable than the aggregator, because the body that administers an
Act tends to host its own copy:

- **Central Information Commission** — `cic.gov.in/sites/default/files/RTI-Act_English.pdf`
  — **verified working**, and now the `reference_url` for all 31 RTI chunks.
  A Hindi text sits alongside it at `rti-actinhindi.pdf`, useful for issue #34.
- **NCDRC** — `ncdrc.nic.in`. The host is up; `bare_acts/CPA2019.pdf` returns
  404. That directory serves `.htm` (`RTIact.htm` exists), so the Consumer
  Protection Act may be there under a different name. **Still needed.**
- **eGazette** — `egazette.gov.in`. Where an Act or rule is first published.
  The authoritative text when a commencement date or amendment is disputed.

---

## Madhya Pradesh

MP is the right state to start with: three of our scheme rows are already MP, and
the corpus currently has **no state law at all**, which makes the state
clarification question unanswerable for law.

### MP Code — `code.mp.gov.in` ← start here

The state's official digital repository of Acts and Rules. By its own
description it holds state legislation, rules made under those Acts, rules made
independently by the state, and central provisions as amended for MP.

That last category matters more than it sounds. Several central Acts apply
differently in MP, and a system that cites the unamended central text for an MP
user is giving a subtly wrong answer. This is exactly the case the
Seventh Schedule logic exists to handle, and we currently have no data for it.

### Other MP sources

- **Law Department** — `law.mp.gov.in/en/acts`. Alphabetical and chronological
  lists of MP Acts, plus links out to India Code and MP Code. Useful as an
  index. Page metadata suggests it is several years old, so cross-check.
- **Department-level pages** — `home.mp.gov.in/en/acts-and-rules` (Home),
  `sda.mp.gov.in/mphome/en/acts-and-rules`. Department-specific rules. Both look
  dated, latest entries around 2010–2016.

### MP schemes

- **Samagra** — `samagra.gov.in`. The spine of MP welfare delivery. Every family
  has an 8-digit Samagra ID, and most state schemes are tied to it. Launched
  2010 under the Samagra Social Security Mission.
- **MP e-District** — `mpedistrict.gov.in`. Scheme applications. Ladli Bahna
  Yojana among the prominent ones.
- **SAMAST** — `samast.mponline.gov.in`. Single window for bank-linked schemes.
- **MP Online** — `mponline.gov.in`. Kiosk-delivered citizen services.
- **Social Justice Department** — pensions and disability schemes.

A caution specific to schemes: eligibility rules and benefit amounts change with
budget cycles. A scheme chunk is accurate as of its `fetched_at` date in a way a
statute chunk is not, and the UI should say so.

---

## Schemes, nationally

### myScheme — `myscheme.gov.in`

Operated by Digital India Corporation under MeitY. **4,700+ central and state
schemes** with structured eligibility. Our 18 pilot schemes came from here.

- **No official public API.** Anything calling itself a myScheme API is a
  third-party wrapper or a scrape.
- Community snapshots exist on Kaggle and Hugging Face (2,066 to 4,670 schemes
  depending on vintage). Useful for *finding* schemes; never as `source_url`,
  and never as chunk text. A stale snapshot of an eligibility rule is worse than
  no answer, because someone may act on it.
- For official bulk access, Digital India Corporation is the body to ask. No
  published process was found.

---

## Third-party aggregators

Acceptable as `reference_url`. Never as provenance, never as chunk text.

- **eCourtsIndia IndiaCode** — claims a free keyless JSON API over 2,246 Acts
  and 77,072 sections, with Markdown and Akoma Ntoso output, CC BY 4.0. If real,
  this is the most interesting option on this page, because it may offer
  **per-section URLs** — which would restore the deep linking issue #22 had to
  give up, and close #31. Everything known about it comes from its own
  marketing; verify before relying on it. A private company, not government.
- **Indian Kanoon** — paid, token-based, judgment-focused.
- **Bare Acts Live** — 1,162 MP Acts and rules, subscription.

---

## Deliberately not pursued: court judgments

The Supreme Court's eSCR portal, and High Court data generally, were considered
and set aside. Recorded here so the decision is visible rather than an omission.

Judgments are **case law, not statute**. Our corpus answers "what does the law
say". Judgments answer "how has this been interpreted", which requires reasoning
about precedent, ratio versus obiter, and whether a case still stands. Getting
that wrong means telling a real person something false about their rights, and
our own disclaimer says we do not advise on individual cases.

Practically, there is no official API and no bulk export from eSCR. The options
are paid third-party scrapers. That is a large acquisition effort for data that
would not improve a single answer to the questions this project targets.

If the project continues past the current scope, the honest sequence is: state
law first, then more central Acts, then rules and notifications, and only then
case law — with a lawyer involved.

---

## What is actually missing, in priority order

1. **MP state law.** The corpus is 147 chunks, all Central. `STATE_SPECIFIC_INTENTS`
   covers housing, labour, welfare and police, so the app asks which state the
   user is in — and then has no state law to answer with. Tenancy is a State
   subject, which is the whole reason the question is asked. Source: MP Code.
2. **A working Consumer Protection link.** 116 of 147 citations currently have
   nowhere to send a reader (issue #31).
3. **More MP schemes.** Three today. Samagra and MP e-District are the sources.
4. **Rules and notifications.** An Act often leaves the operative detail to
   rules made under it. We have no rules at all.

**Do not act on this list before Phase E (#13).** Every chunk added changes what
the evaluation measures, and an evaluation over a moving corpus is not a result.
Collect the numbers on the corpus we have, then grow it.

---

## Scraping, legally

No Indian law prohibits web scraping as such, and bare Acts are government works.
The real constraints are the IT Act on unauthorised access, the DPDP Act where
personal data is involved (not our case), and site terms of use.

The practical risks are technical: rate limits and anti-bot measures. Prefer an
API where one exists. The `robots.txt` check and rate limiting already in
`data/ingestion/scrape.py` are the right posture and should stay.
