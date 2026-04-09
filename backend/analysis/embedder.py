import asyncio

from pydantic_ai import Embedder

DEFAULT_EMBEDDING_MODEL = "openai:text-embedding-3-small"

embedder = Embedder(DEFAULT_EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts, returning one vector per input (order-preserved).

    Uses pydantic_ai Embedder with API-level batching — one HTTP call returns
    N vectors.  Runs async embed_documents in a sync context for Celery.
    """
    result = asyncio.run(embedder.embed_documents(texts))
    return [list(v) for v in result.embeddings]
