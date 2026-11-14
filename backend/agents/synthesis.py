import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class SynthesisAgent:
    """
    Generates grounded answers from retrieved CivicConnect chunks.
    """

    def __init__(
        self,
        model=None
    ):
        api_key = os.getenv("GROQ_API_KEY")

        # Check this ourselves rather than letting the Groq client fail deep
        # inside its own stack, so the message says what to do about it.
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add a "
                "key from https://console.groq.com"
            )

        self.client = Groq(api_key=api_key)

        # Configurable so the model can be swapped without a code change, and
        # so the report can state which one produced the evaluation numbers.
        self.model = model or os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

    def synthesize(self, query, retrieved_chunks):
        """
        Generate an answer using only the retrieved chunks.
        """

        if not retrieved_chunks:
            return {
                "answer": "The available sources do not contain enough information to answer this question.",
                "citations": []
            }

        context = "\n\n".join(
            [
                (
                    f"Source: {chunk['act']}, "
                    f"Section: {chunk['section']}\n"
                    f"{chunk['text']}"
                )
                for chunk in retrieved_chunks
            ]
        )

        prompt = f"""
You are CivicConnect, an AI assistant that answers questions
about Indian laws and government information.

Answer the user's question using ONLY the provided context.

If the context does not contain enough information to answer,
say that the available sources do not provide enough information.

Do not invent laws, sections, penalties, dates, or facts.

User question:
{query}

Retrieved context:
{context}

Provide a clear and concise answer.
Mention the relevant Act and Section when available.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        answer = response.choices[0].message.content

        citations = [
            {
                "chunk_id": chunk["chunk_id"],
                "act": chunk["act"],
                "section": chunk["section"],
                "jurisdiction": chunk["jurisdiction"],
                "source_url": chunk["source_url"],
                # Carry the retriever diagnostics through. The hybrid retriever
                # attaches these; without them the API cannot show how a source
                # was found, and the Phase E comparison has nothing to measure.
                "_retrieval_scores": chunk.get("_retrieval_scores"),
                "_rrf_score": chunk.get("_rrf_score"),
            }
            for chunk in retrieved_chunks
        ]

        return {
            "answer": answer,
            "citations": citations
        }
