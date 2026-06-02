from typing import List

from langchain_core.documents import Document

from config.settings import settings
from src.rag.embedder import Embedder
from src.rag.vector_store import ChromaStore


class Retriever:
    def __init__(self, store: ChromaStore, embedder: Embedder = None):
        self.store = store
        self.embedder = embedder or Embedder()
        self.top_k = settings.retrieval_top_k

    def retrieve(self, query: str, k: int = None) -> List[Document]:
        k = k or self.top_k
        query_embedding = self.embedder.embed_query(query)
        return self.store.search(query_embedding, k=k)
