"""Embedding service for generating vector embeddings."""

from typing import List

from openai import OpenAI

from src.utils.exceptions import EmbeddingServiceError


class EmbeddingService:
    """Service for generating text embeddings using OpenAI."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """
        Initialize embedding service.

        Args:
            api_key: OpenAI API key
            model: Embedding model to use
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector

        Raises:
            EmbeddingServiceError: If embedding generation fails
        """
        if not text or not text.strip():
            raise EmbeddingServiceError("No se puede generar embedding de texto vacío")

        try:
            response = self.client.embeddings.create(input=text, model=self.model)
            return response.data[0].embedding
        except Exception as e:
            raise EmbeddingServiceError(f"Error al generar embedding: {str(e)}")

    def embed_batch(self, texts: List[str], max_batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            max_batch_size: Maximum batch size (OpenAI limit is ~2048)

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingServiceError: If embedding generation fails
        """
        if not texts:
            return []

        # Filter out empty texts
        non_empty_texts = [t for t in texts if t and t.strip()]
        if not non_empty_texts:
            raise EmbeddingServiceError("No hay textos válidos para generar embeddings")

        embeddings = []

        try:
            # Process in batches
            for i in range(0, len(non_empty_texts), max_batch_size):
                batch = non_empty_texts[i : i + max_batch_size]
                response = self.client.embeddings.create(input=batch, model=self.model)

                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)

            return embeddings
        except Exception as e:
            raise EmbeddingServiceError(f"Error al generar embeddings en batch: {str(e)}")
