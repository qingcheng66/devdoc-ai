from typing import List

from sentence_transformers import SentenceTransformer

from src.utils.logger import logger


class Embedder:
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name, local_files_only=True)
        self._dim = self.model.get_embedding_dimension()
        logger.info(f"Embedding model loaded, dimension={self._dim}")

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        results = self.model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return [r.tolist() for r in results]

    def embed_query(self, text: str) -> List[float]:
        result = self.model.encode(text, normalize_embeddings=True)
        return result.tolist()
