"""Deterministic chunking utility for statutory laws and welfare schemes.

Conforms strictly to the shared chunk contract.
"""

import hashlib
import re
from typing import Any, Dict, List


def clean_text(text: str) -> str:
    """Clean text by stripping excessive whitespace and header/footer artifacts."""
    if not text:
        return ""
    # Collapse multiple whitespace/newlines
    text = re.sub(r"\s+", " ", text)
    # Strip common PDF page artifacts
    text = re.sub(r"Page \d+ of \d+", "", text, flags=re.IGNORECASE)
    return text.strip()


def chunk_law_section(
    act: str,
    chapter: str,
    section: str,
    text: str,
    jurisdiction: str,
    effective_date: str,
    source_url: str,
    chunk_id_prefix: str = "",
    max_chunk_chars: int = 1500,
    assent_date: str = "",
    excerpt: str = "",
    raw_sha256: str = "",
    fetched_at: str = "",
    extraction_method: str = "html",
    reviewer_name: str = "",
) -> List[Dict[str, Any]]:
    """Chunk statutory legal section deterministically with cryptographic provenance.

    Preserves Act -> Chapter -> Section hierarchy. If section text is under max_chunk_chars,
    keeps it as a single chunk. If larger, splits deterministically into sub-chunks.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return []

    # Generate base chunk_id if not provided
    if not chunk_id_prefix:
        sec_num = re.sub(r"[^\w]", "", section.lower())
        act_prefix = "".join(w.lower() for w in act.split() if w.isalnum() or any(c.isalnum() for c in w))
        act_prefix = re.sub(r"[^\w]", "", act_prefix)
        chunk_id_prefix = f"{act_prefix}-{sec_num}"

    def make_chunk_dict(cid: str, txt: str) -> Dict[str, Any]:
        t_hash = hashlib.sha256(txt.encode("utf-8")).hexdigest()
        r_hash = raw_sha256.strip() if raw_sha256 else t_hash
        d = {
            "chunk_id": cid,
            "text": txt,
            "act": act.strip(),
            "chapter": chapter.strip(),
            "section": section.strip(),
            "jurisdiction": jurisdiction.strip(),
            "effective_date": effective_date.strip(),
            "source_url": source_url.strip(),
            "text_sha256": t_hash,
            "raw_sha256": r_hash,
            "extraction_method": extraction_method.strip() if extraction_method else "html",
        }
        if assent_date:
            d["assent_date"] = assent_date.strip()
        if excerpt:
            d["excerpt"] = excerpt.strip()
        if fetched_at:
            d["fetched_at"] = fetched_at.strip()
        if reviewer_name:
            d["reviewer_name"] = reviewer_name.strip()
        return d

    if len(cleaned) <= max_chunk_chars:
        return [make_chunk_dict(chunk_id_prefix, cleaned)]

    # Deterministic split for long section
    words = cleaned.split(" ")
    chunks = []
    curr_words: List[str] = []
    curr_len = 0
    part = 1

    for word in words:
        if curr_len + len(word) + 1 > max_chunk_chars and curr_words:
            chunks.append(make_chunk_dict(f"{chunk_id_prefix}-{part}", " ".join(curr_words)))
            part += 1
            curr_words = []
            curr_len = 0
        curr_words.append(word)
        curr_len += len(word) + 1

    if curr_words:
        cid = f"{chunk_id_prefix}-{part}" if part > 1 else chunk_id_prefix
        chunks.append(make_chunk_dict(cid, " ".join(curr_words)))

    return chunks


def chunk_welfare_scheme(
    scheme_name: str,
    description: str,
    eligibility: str,
    benefits: str,
    application_process: str,
    jurisdiction: str,
    effective_date: str,
    source_url: str,
    category: str = "",
    documents_required: str = "",
    scheme_id_slug: str = "",
    excerpt: str = "",
    raw_sha256: str = "",
    fetched_at: str = "",
    extraction_method: str = "api",
    reviewer_name: str = "",
) -> List[Dict[str, Any]]:
    """Chunk welfare scheme details cleanly into a structured chunk with provenance."""
    if not scheme_id_slug:
        scheme_id_slug = "scheme-" + re.sub(r"[^\w]+", "-", scheme_name.lower()).strip("-")

    parts = []
    if description:
        parts.append(f"Description: {clean_text(description)}")
    if eligibility:
        parts.append(f"Eligibility: {clean_text(eligibility)}")
    if benefits:
        parts.append(f"Benefits: {clean_text(benefits)}")
    if application_process:
        parts.append(f"Application Process: {clean_text(application_process)}")
    if documents_required:
        parts.append(f"Documents Required: {clean_text(documents_required)}")

    combined_text = "\n\n".join(parts)
    t_hash = hashlib.sha256(combined_text.encode("utf-8")).hexdigest()
    r_hash = raw_sha256.strip() if raw_sha256 else t_hash

    chunk_data = {
        "chunk_id": f"{scheme_id_slug}-1",
        "text": combined_text,
        "act": scheme_name.strip(),
        "chapter": category.strip() if category else "Welfare Scheme",
        "section": "",
        "jurisdiction": jurisdiction.strip(),
        "effective_date": effective_date.strip() if effective_date else "2020-01-01",
        "source_url": source_url.strip(),
        "text_sha256": t_hash,
        "raw_sha256": r_hash,
        "extraction_method": extraction_method.strip() if extraction_method else "api",
    }
    if excerpt:
        chunk_data["excerpt"] = excerpt.strip()
    if fetched_at:
        chunk_data["fetched_at"] = fetched_at.strip()
    if reviewer_name:
        chunk_data["reviewer_name"] = reviewer_name.strip()

    return [chunk_data]
