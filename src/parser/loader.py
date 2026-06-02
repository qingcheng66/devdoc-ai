from pathlib import Path
from typing import List

from langchain_core.documents import Document
from src.parser.pdf_loader import PDFLoader
from src.parser.docx_loader import DocxLoader
from src.parser.txt_loader import TxtLoader
from src.parser.zip_loader import ZipLoader
from src.parser.sanitizer import sanitize_text
from src.utils.logger import logger


class UnifiedLoader:
    def __init__(self):
        self.loaders = [PDFLoader(), DocxLoader(), TxtLoader(), ZipLoader()]

    def can_load(self, file_path: str) -> bool:
        for loader in self.loaders:
            if loader.can_load(file_path):
                return True
        return False

    def load(self, file_path: str) -> List[Document]:
        for loader in self.loaders:
            if loader.can_load(file_path):
                return loader.load(file_path)
        logger.warning(f"No loader for file: {file_path}")
        return []

    def load_batch(self, file_paths: List[str]) -> List[Document]:
        all_docs = []
        for fp in file_paths:
            try:
                docs = self.load(fp)
                all_docs.extend(docs)
                logger.info(f"Loaded {len(docs)} documents from {Path(fp).name}")
            except Exception as e:
                logger.error(f"Error loading {fp}: {e}")
        return all_docs

    def load_pasted_text(self, text: str) -> List[Document]:
        if not text.strip():
            return []
        text = sanitize_text(text)
        return [Document(
            page_content=text,
            metadata={"source": "pasted_text", "file_type": "text"}
        )]
