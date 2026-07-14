from sentence_transformers import SentenceTransformer
from app.core.config import EMBEDDING_MODEL_NAME

# Load the embedding model only once
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def create_embeddings(chunks):
    """
    Generate embeddings for each text chunk.

    Args:
        chunks (list): List of dictionaries containing page number and text.

    Returns:
        list: List of dictionaries containing page, text, and embedding.
    """

    embedded_chunks = []

    for chunk in chunks:

        embedding = embedding_model.encode(chunk["text"], normalize_embeddings=True).tolist()

        embedded_chunks.append(
            {
                "id": chunk["id"],
                "page": chunk["page"],
                "text": chunk["text"],
                "embedding": embedding
            }
        )

    return embedded_chunks


def get_query_embedding(query: str):
    """
    Generate normalized embedding for a query.
    """
    return embedding_model.encode(query, normalize_embeddings=True).tolist()