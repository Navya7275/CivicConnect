def filter_by_metadata(
    chunks,
    filters=None,
    as_of_date=None
):
    """
    Filter chunks using metadata and effective date.

    Jurisdiction rule:
    - If requested jurisdiction is a state, include that
      state and Central law.
    - If requested jurisdiction is Central, include only
      Central law.

    Other metadata fields use exact matching.

    If as_of_date is provided, only chunks whose
    effective_date is on or before that date are included.
    """

    if not filters and not as_of_date:
        return chunks

    filtered_chunks = []

    for chunk in chunks:

        matches = True

        # Metadata filters
        if filters:

            for key, expected_value in filters.items():

                if key == "jurisdiction":

                    chunk_jurisdiction = chunk.get(
                        "jurisdiction"
                    )

                    if expected_value == "Central":

                        if chunk_jurisdiction != "Central":
                            matches = False
                            break

                    else:

                        if chunk_jurisdiction not in {
                            expected_value,
                            "Central"
                        }:
                            matches = False
                            break

                else:

                    if chunk.get(key) != expected_value:
                        matches = False
                        break

        if not matches:
            continue

        # Effective-date filtering
        if as_of_date:

            effective_date = chunk.get(
                "effective_date"
            )

            if (
                not effective_date
                or effective_date > as_of_date
            ):
                continue

        filtered_chunks.append(chunk)

    return filtered_chunks