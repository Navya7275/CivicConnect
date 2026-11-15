from pathlib import Path
import json
import pickle


ARTIFACTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "indexing"
    / "artifacts"
)

BM25_INDEX_PATH = ARTIFACTS_DIR / "bm25.pkl"
CHUNK_IDS_PATH = ARTIFACTS_DIR / "chunk_ids.json"


class BM25Retriever:
    """
    BM25-based sparse retriever using the prebuilt BM25 index.
    """

    def __init__(self, chunks):
        self.chunks = chunks

        if not BM25_INDEX_PATH.exists():
            raise FileNotFoundError(
                f"BM25 index not found: {BM25_INDEX_PATH}"
            )

        if not CHUNK_IDS_PATH.exists():
            raise FileNotFoundError(
                f"Chunk ID mapping not found: {CHUNK_IDS_PATH}"
            )

        # Map chunk_id -> chunk dictionary.
        self.chunk_lookup = {
            chunk["chunk_id"]: chunk
            for chunk in chunks
        }

        # Load the prebuilt BM25 index.
        with open(BM25_INDEX_PATH, "rb") as file:
            self.bm25 = pickle.load(file)

        # Positions in the BM25 score array refer to the order the index was
        # built in, which is not necessarily the order (or the length) of the
        # `chunks` list we were handed. So resolve through the same mapping
        # dense.py uses: index position -> chunk_id -> chunk.
        #
        # Indexing `self.chunks` by score position directly looks equivalent
        # and is not: it raises IndexError when given a subset of the corpus,
        # and silently returns the wrong chunk when the index is stale.
        with open(CHUNK_IDS_PATH, "r", encoding="utf-8") as file:
            mapping = json.load(file)

        # The BM25 index stores documents already tokenized, so it is only
        # valid for the tokenizer that built it. Querying a v1 index with the
        # v2 tokenizer does not raise anything on its own -- it just stops
        # matching, because one side has "request." and the other has
        # "request". Retrieval quietly gets worse and every test still passes.
        # Refuse to load instead, and say exactly what to run.
        import hashlib
        from data.indexing.build_index import TOKENIZER_VERSION

        if "corpus_sha256" in mapping:
            seed_chunks = Path(__file__).resolve().parents[2] / "data" / "ingestion" / "seed_chunks.json"
            seed_schemes = Path(__file__).resolve().parents[2] / "data" / "ingestion" / "seed_schemes.json"
            h = hashlib.sha256()
            for p in sorted([seed_chunks, seed_schemes]):
                if p.exists():
                    h.update(p.read_bytes())
            current_hash = h.hexdigest()
            if current_hash != mapping["corpus_sha256"]:
                raise RuntimeError(
                    "Index was built from a different corpus than the one on disk.\n"
                    "Run: python -m data.indexing.build_index"
                )

        index_tokenizer = mapping.get("tokenizer_version")
        if index_tokenizer != TOKENIZER_VERSION:
            raise RuntimeError(
                f"BM25 index was built with tokenizer version "
                f"{index_tokenizer if index_tokenizer is not None else '1 (unversioned)'}, "
                f"but this code uses version {TOKENIZER_VERSION}. The stored "
                f"tokens no longer match the ones queries produce, so keyword "
                f"search would silently return the wrong results.\n"
                f"Rebuild the index:  python -m data.indexing.build_index"
            )

        self.index_to_chunk_id = {
            int(index): chunk_id
            for index, chunk_id
            in mapping["index_to_chunk_id"].items()
        }

    def search(self, query, limit=5):
        """
        Search the prebuilt BM25 index.

        Returns:
            list[dict]: Each result contains the chunk and
            its BM25 score.
        """

        # Use the same tokenizer the index was built with. BM25 matches tokens
        # literally, so the query side and the document side have to agree
        # exactly -- "request." and "request?" and "request" are three
        # different terms as far as it is concerned.
        #
        # This used to be a second, inlined copy of the tokenizer logic
        # (`query.split()`), independent of build_index.tokenize_text. The two
        # agreed only by coincidence, with nothing keeping them in step, so
        # changing one silently broke matching without failing anything.
        from data.indexing.build_index import tokenize_text

        query_tokens = tokenize_text(query)

        scores = self.bm25.get_scores(query_tokens)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True
        )

        results = []

        for index in ranked_indices:
            if len(results) >= limit:
                break

            chunk_id = self.index_to_chunk_id.get(int(index))

            if chunk_id is None:
                continue

            chunk = self.chunk_lookup.get(chunk_id)

            # The caller may have passed a subset of the corpus, so a chunk
            # the index knows about is not always one we can return.
            if chunk is None:
                continue

            result = dict(chunk)
            result["_score"] = float(scores[index])
            result["_retriever"] = "bm25"

            results.append(result)

        return results
