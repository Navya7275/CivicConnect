# backend/retrieval/chunks.py

"""
Shared chunk structure for CivicConnect retrieval.

Each chunk represents a searchable piece of Indian legal
or welfare information.
"""


def get_mock_chunks():
    """
    Temporary mock data for developing the retrieval system.

    Later this will be replaced by chunks loaded from the
    actual PostgreSQL/database + indexing pipeline.
    """

    chunks = [
        {
            "chunk_id": "chunk_001",
            "text": (
                "As per Section 138 of the Negotiable Instruments Act, "
                "dishonour of a cheque for insufficient funds is an offence "
                "subject to the conditions prescribed by the Act."
            ),
            "act": "Negotiable Instruments Act",
            "chapter": "XVII",
            "section": "138",
            "jurisdiction": "Central",
            "effective_date": "1882-03-01",
            "source_url": "https://indiacode.nic.in",
        },
        {
            "chunk_id": "chunk_002",
            "text": (
                "The Consumer Protection Act provides protection to consumers "
                "against defective goods and deficient services."
            ),
            "act": "Consumer Protection Act",
            "chapter": "I",
            "section": "2",
            "jurisdiction": "Central",
            "effective_date": "2019-07-20",
            "source_url": "https://indiacode.nic.in",
        },
        {
            "chunk_id": "chunk_003",
            "text": (
                "Consumer disputes may be addressed through the consumer "
                "dispute redressal mechanisms established under the Act."
            ),
            "act": "Consumer Protection Act",
            "chapter": "IV",
            "section": "34",
            "jurisdiction": "Central",
            "effective_date": "2019-07-20",
            "source_url": "https://indiacode.nic.in",
        },
    ]

    return chunks