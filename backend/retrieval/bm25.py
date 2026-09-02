from rank_bm25 import BM25Okapi


class BM25Retriever:
    """
    BM25-based sparse retriever for CivicConnect.
    """

    def __init__(self, chunks):
        self.chunks = chunks

        tokenized_documents = [
            chunk["text"].lower().split()
            for chunk in chunks
        ]

        self.bm25 = BM25Okapi(tokenized_documents)

    def search(self, query, limit=5):
        """
        Search the indexed chunks using BM25.
        """

        query_tokens = query.lower().split()

        scores = self.bm25.get_scores(query_tokens)

        ranked = list(zip(self.chunks, scores))

        ranked.sort(
            key=lambda item: item[1],
            reverse=True
        )

        return [
            chunk
            for chunk, score in ranked[:limit]
        ]