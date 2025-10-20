"""
Embedding Generation
Generate dense and sparse embeddings using Gemini API
"""

from google import genai
from google.genai import types
from app.config import settings

# Initialize Gemini Client
client = genai.Client(api_key=settings.gemini_api_key)


async def generate_dense_embedding(text: str) -> list[float]:
    """
    Generate dense embedding using Gemini embedding model

    Args:
        text: Input text to embed

    Returns:
        Dense embedding vector (1536 dimensions)

    Note: Uses Gemini's output_dimensionality parameter to directly receive
    the configured dimension size (leveraging Matryoshka Representation Learning).
    """
    try:
        result = await client.aio.models.embed_content(
            model=f"models/{settings.dense_model}",
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=settings.dense_dimension
            )
        )
        embedding = result.embeddings[0].values
        return embedding
    except Exception as e:
        raise ValueError(f"Failed to generate dense embedding: {str(e)}")


async def generate_dense_embedding_from_paragraphs(paragraphs: list[str]) -> list[float]:
    """
    Generate dense embedding from list of paragraph texts
    Combines paragraphs into single text before embedding

    Args:
        paragraphs: List of paragraph texts

    Returns:
        Dense embedding vector (1536 dimensions)
    """
    combined_text = "\n".join(paragraphs)
    return await generate_dense_embedding(combined_text)


async def generate_sparse_embedding(text: str) -> dict[int, float]:
    """
    Generate sparse embedding using multilingual sparse embedder
    - Korean text (>= 30%): Kiwi morphological analyzer with POS filtering
    - Non-Korean text: FastEmbed BM25

    Args:
        text: Input text to process

    Returns:
        Sparse vector as {index: value} dictionary
    """
    from app.multilingual_sparse_embedding import create_multilingual_sparse_embedding
    # Note: Sparse embedding is CPU-bound, no benefit from async
    # But we maintain async signature for backward compatibility
    return create_multilingual_sparse_embedding(text)


async def generate_sparse_embedding_from_paragraphs(paragraphs: list[str]) -> dict[int, float]:
    """
    Generate sparse embedding from list of paragraph texts

    Args:
        paragraphs: List of paragraph texts

    Returns:
        Sparse vector as {index: value} dictionary
    """
    combined_text = "\n".join(paragraphs)
    return await generate_sparse_embedding(combined_text)


async def generate_query_dense_embedding(query: str) -> list[float]:
    """
    Generate dense embedding for search query

    Args:
        query: Search query text

    Returns:
        Dense embedding vector (1536 dimensions)

    Note: Uses Gemini's output_dimensionality parameter to directly receive
    the configured dimension size (leveraging Matryoshka Representation Learning).
    """
    try:
        result = await client.aio.models.embed_content(
            model=f"models/{settings.dense_model}",
            contents=query,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=settings.dense_dimension
            )
        )
        embedding = result.embeddings[0].values
        return embedding
    except Exception as e:
        raise ValueError(f"Failed to generate query embedding: {str(e)}")


async def generate_query_sparse_embedding(query: str) -> dict[int, float]:
    """
    Generate sparse embedding for search query
    - Korean text (>= 30%): Kiwi morphological analyzer with POS filtering
    - Non-Korean text: FastEmbed BM25

    Args:
        query: Search query text

    Returns:
        Sparse vector as {index: value} dictionary
    """
    from app.multilingual_sparse_embedding import create_multilingual_sparse_embedding
    # Note: Sparse embedding is CPU-bound, no benefit from async
    # But we maintain async signature for consistency with other query embedding functions
    return create_multilingual_sparse_embedding(query)


async def batch_generate_dense_embeddings(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT"
) -> list[list[float]]:
    """
    Generate dense embeddings for multiple texts in a single API call

    This is significantly more efficient than calling generate_dense_embedding
    multiple times, as it reduces API calls from N to 1.

    Args:
        texts: List of texts to embed
        task_type: Either "RETRIEVAL_DOCUMENT" or "RETRIEVAL_QUERY"

    Returns:
        List of dense embedding vectors (each 1536 dimensions)

    Example:
        texts = ["text 1", "text 2", "text 3"]
        embeddings = await batch_generate_dense_embeddings(texts)
        # Returns [[emb1], [emb2], [emb3]]
    """
    if not texts:
        return []

    try:
        result = await client.aio.models.embed_content(
            model=f"models/{settings.dense_model}",
            contents=texts,  # Pass list of texts
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=settings.dense_dimension
            )
        )
        embeddings = [emb.values for emb in result.embeddings]
        return embeddings
    except Exception as e:
        raise ValueError(f"Failed to batch generate dense embeddings: {str(e)}")
