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
        model="openai/gpt-oss-20b"
    ):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )

        self.model = model

    def synthesize(self, query, retrieved_chunks):
        """
        Generate an answer using only the retrieved chunks.
        """

        if not retrieved_chunks:
            return {
                "answer": "The available sources do not contain enough information to answer this question.",
                "sources": []
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

        sources = [
            {
                "chunk_id": chunk["chunk_id"],
                "act": chunk["act"],
                "section": chunk["section"],
                "source_url": chunk["source_url"]
            }
            for chunk in retrieved_chunks
        ]

        return {
            "answer": answer,
            "sources": sources
        }