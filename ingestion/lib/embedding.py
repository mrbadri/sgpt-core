"""
Custom embedding models (AvalAI, GapGPT).

OpenAI-compatible clients against provider base URLs.

Documentation: https://developers.llamaindex.ai/python/framework/module_guides/models/embeddings/
"""

import os
from typing import List

from langchain_core.embeddings import Embeddings
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Constants
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDING_DIM = os.getenv("EMBEDDING_DIM", 3072)

class OpenAIEmbeddingLangchain(Embeddings):
    """
    LangChain-compatible embeddings for OpenAI (OpenAI-compatible /v1/embeddings).

    API key: pass `api_key` or set env `EMBEDDING_API_KEY`.
    """

    def __init__(
        self,
        api_key: str | None = EMBEDDING_API_KEY,
        model: str | None = EMBEDDING_MODEL,
        base_url: str | None = EMBEDDING_BASE_URL,
    ):
        if not api_key:
            raise ValueError(
                "API key required: pass api_key=... or set EMBEDDING_API_KEY"
            )
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def embed_query(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [item.embedding for item in response.data]