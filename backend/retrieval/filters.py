def filter_by_metadata(chunks, filters):
    """
    Filter chunks using top-level chunk metadata.

    Example:
        filters = {
            "jurisdiction": "Central"
        }
    """

    if not filters:
        return chunks

    filtered_chunks = []

    for chunk in chunks:
        matches = True

        for key, expected_value in filters.items():
            if chunk.get(key) != expected_value:
                matches = False
                break

        if matches:
            filtered_chunks.append(chunk)

    return filtered_chunks