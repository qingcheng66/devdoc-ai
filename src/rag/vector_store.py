import uuid
from typing import List

import chromadb
from langchain_core.documents import Document

from config.settings import settings
from src.utils.logger import logger


class ChromaStore:
    def __init__(self, persist_dir: str = None, collection_name: str = "devdoc_default"):
        persist_dir = persist_dir or settings.chroma_persist_dir
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(name=collection_name)
        logger.info(f"ChromaDB collection '{collection_name}' ready at {persist_dir}")

    def add_documents(self, docs: List[Document], embeddings: List[List[float]]):
        ids = [doc.metadata.get("chunk_id", str(uuid.uuid4())) for doc in docs]
        texts = [doc.page_content for doc in docs]
        metadatas = [doc.metadata for doc in docs]
        self.collection.add(ids=ids, embeddings=embeddings, documents=texts,
                            metadatas=metadatas)
        logger.info(f"Added {len(docs)} documents to collection '{self.collection_name}'")

    def search(self, query_embedding: List[float], k: int = 5) -> List[Document]:
        results = self.collection.query(query_embeddings=[query_embedding], n_results=k)
        docs = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                docs.append(Document(
                    page_content=results["documents"][0][i] if results["documents"] else "",
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {}
                ))
        return docs

    def delete_collection(self):
        self.client.delete_collection(name=self.collection_name)
        logger.info(f"Deleted collection '{self.collection_name}'")

    def clear(self):
        self.delete_collection()
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
