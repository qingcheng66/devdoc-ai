from pathlib import Path
from typing import List

from langchain_core.documents import Document
from src.parser.sanitizer import sanitize_text
from src.utils.logger import logger


class PDFLoader:
    def can_load(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == ".pdf"

    def load(self, file_path: str) -> List[Document]:
        import fitz
        docs = []
        try:
            pdf = fitz.open(file_path)
        except Exception as e:
            logger.error(f"Failed to open PDF {file_path}: {e}")
            return []

        for i, page in enumerate(pdf):
            text = page.get_text("text")
            text = sanitize_text(text)
            if text.strip():
                docs.append(Document(
                    page_content=text,
                    metadata={"source": file_path, "file_type": "pdf",
                               "page_num": i + 1}
                ))
        pdf.close()
        if not docs:
            logger.warning(f"No extractable text from {file_path}")
        else:
            logger.info(f"Loaded PDF: {Path(file_path).name} ({len(docs)} pages)")
        return docs
