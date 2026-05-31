"""Azure OpenAI embedding client."""
import os
import time
from typing import Optional

from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

def get_embedding_client() -> AzureOpenAI:
    """Create Azure OpenAI client from environment variables."""
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

# Dimension settings for embedding models
# text-embedding-3-small: native 1536
# text-embedding-3-large: native 3072, but HNSW max is 2000
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "2000"))

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def get_embeddings(
    texts: list[str],
    deployment_name: Optional[str] = None,
    dimensions: Optional[int] = None
) -> list[list[float]]:
    """Get embeddings for a batch of texts.

    Args:
        texts: List of text strings to embed
        deployment_name: Azure OpenAI deployment name (defaults to env var)
        dimensions: Output dimensions (defaults to EMBEDDING_DIMENSIONS env var)

    Returns:
        List of embedding vectors
    """
    if not deployment_name:
        deployment_name = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")

    if dimensions is None:
        dimensions = EMBEDDING_DIMENSIONS

    client = get_embedding_client()
    response = client.embeddings.create(
        model=deployment_name,
        input=texts,
        dimensions=dimensions
    )
    return [item.embedding for item in response.data]

def get_single_embedding(text: str) -> list[float]:
    """Get embedding for a single text string."""
    embeddings = get_embeddings([text])
    return embeddings[0]
