from backend.retrieval.chunks import get_mock_chunks
from backend.retrieval.filters import filter_by_metadata


def test_central_jurisdiction_filter():
    chunks = get_mock_chunks()

    results = filter_by_metadata(
        chunks,
        {"jurisdiction": "Central"}
    )

    assert results

    for chunk in results:
        assert chunk["jurisdiction"] == "Central"


def test_state_jurisdiction_includes_central():
    chunks = get_mock_chunks()

    results = filter_by_metadata(
        chunks,
        {"jurisdiction": "Madhya Pradesh"}
    )

    for chunk in results:
        assert chunk["jurisdiction"] in {
            "Madhya Pradesh",
            "Central"
        }


def test_date_filter():
    chunks = get_mock_chunks()

    results = filter_by_metadata(
        chunks,
        as_of_date="2020-01-01"
    )

    for chunk in results:
        assert chunk["effective_date"] <= "2020-01-01"