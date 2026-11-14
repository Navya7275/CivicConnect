"""The link a reader clicks, and the record of where the text came from.

These are two different things, and conflating them is what issue #22 was
about. `source_url` records where we fetched the text and is what `raw_sha256`
is the hash of. `reference_url` is a link that actually opens today.

They were the same field until the India Code handle pages started returning a
CDN error, which made every citation in the product a dead end. Overwriting
`source_url` with a working link would have left `raw_sha256` describing a page
we no longer point at, so the two meanings were split instead.

These tests guard that split: the link must reach the UI, it must fall back
when absent, and `source_url` must keep meaning what the provenance record
says it means.
"""

from __future__ import annotations

import pytest

from backend.api.schemas import Citation


def test_reference_url_is_optional() -> None:
    """Most citations will not have one, and that must stay valid."""
    citation = Citation(
        act="Consumer Protection Act, 2019",
        section="Section 35",
        jurisdiction="Central",
        source_url="https://example.gov.in/act",
    )
    assert citation.reference_url is None


def test_reference_url_does_not_replace_source_url() -> None:
    """The provenance record must survive alongside the reader-facing link.

    If a future change ever makes one overwrite the other, raw_sha256 stops
    describing the page source_url names, and the provenance claim in the
    report becomes false.
    """
    citation = Citation(
        act="Right to Information Act, 2005",
        section="Section 7",
        jurisdiction="Central",
        source_url="https://www.indiacode.nic.in/handle/123456789/2065",
        reference_url="https://cic.gov.in/sites/default/files/RTI-Act_English.pdf",
    )

    assert citation.source_url == "https://www.indiacode.nic.in/handle/123456789/2065"
    assert citation.reference_url == "https://cic.gov.in/sites/default/files/RTI-Act_English.pdf"
    assert citation.source_url != citation.reference_url


@pytest.mark.parametrize(
    ("reference_url", "expected"),
    [
        ("https://cic.gov.in/x.pdf", "https://cic.gov.in/x.pdf"),
        (None, "https://www.indiacode.nic.in/handle/123456789/2065"),
    ],
)
def test_the_link_the_ui_resolves(reference_url: str | None, expected: str) -> None:
    """Mirrors `reference_url || source_url` in CitationViewer.tsx.

    A citation must never render without a link at all: source_url is required,
    so the fallback always has something to use.
    """
    citation = Citation(
        act="Right to Information Act, 2005",
        section="Section 7",
        jurisdiction="Central",
        source_url="https://www.indiacode.nic.in/handle/123456789/2065",
        reference_url=reference_url,
    )

    assert (citation.reference_url or citation.source_url) == expected


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known gap, tracked in #31: the 116 Consumer Protection chunks have no "
        "working link yet. The India Code handle page returns a CDN error and "
        "ncdrc.nic.in/bare_acts/CPA2019.pdf returns 404. strict=True means this "
        "test FAILS once a working URL is set -- that is the signal to delete "
        "this marker, not to widen it."
    ),
)
def test_every_chunk_in_the_corpus_offers_a_working_link() -> None:
    """No citation should send a reader to a page known to be broken.

    The India Code handle pages return a CDN error, so a chunk whose only link
    is one of those is a dead end. Every chunk must carry a reference_url
    pointing somewhere else.

    Currently expected to fail: only the 31 RTI chunks have a confirmed link.
    Marked xfail rather than deleted or loosened, so the gap stays counted and
    visible instead of quietly disappearing from the suite.
    """
    import json
    from pathlib import Path

    corpus = Path(__file__).resolve().parents[2] / "data" / "ingestion" / "seed_chunks.json"
    chunks = json.loads(corpus.read_text(encoding="utf-8"))

    broken_hosts = ("indiacode.nic.in", "indiacode.gov.in")

    dead_ends = [
        c["chunk_id"]
        for c in chunks
        if not c.get("reference_url")
        and any(host in c.get("source_url", "") for host in broken_hosts)
    ]

    assert not dead_ends, (
        f"{len(dead_ends)} chunks link only to an India Code handle page, which "
        f"does not load. They need a reference_url. First few: {dead_ends[:3]}"
    )
