import logging
from typing import Optional
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding service using fastembed (ONNX-based, lightweight)."""

    def __init__(self):
        self._model = None
        self._dimension = None

    def _get_model(self):
        """Lazy-initialize the embedding model."""
        if self._model is not None:
            return self._model
        try:
            from fastembed import TextEmbedding
            self._model = TextEmbedding(model_name=settings.EMBEDDING_MODEL)
            # Get dimension by running a test embedding
            test = list(self._model.embed(["test"]))[0]
            self._dimension = len(test)
            logger.info(
                "Embedding model loaded: %s (dim=%d)",
                settings.EMBEDDING_MODEL,
                self._dimension,
            )
            return self._model
        except Exception as e:
            logger.error("Failed to load embedding model: %s", str(e))
            raise

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            self._get_model()
        return self._dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        try:
            model = self._get_model()
            embeddings = list(model.embed(texts))
            return [e.tolist() for e in embeddings]
        except Exception as e:
            logger.error("Embedding generation error: %s", str(e))
            raise

    async def embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        results = await self.embed([text])
        return results[0]

    async def similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        import math
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


embedding_service = EmbeddingService()
