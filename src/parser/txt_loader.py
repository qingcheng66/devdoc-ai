from pathlib import Path
from typing import List
import chardet

from langchain_core.documents import Document
from src.parser.sanitizer import sanitize_text
from src.utils.logger import logger


class TxtLoader:
    SUPPORTED_EXTENSIONS = {".txt", ".md", ".py", ".java", ".js", ".ts",
                            ".json", ".yaml", ".yml", ".xml", ".html", ".css",
                            ".c", ".cpp", ".h", ".go", ".rs", ".rb", ".php"}

    def can_load(self, file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS

    def load(self, file_path: str) -> List[Document]:
        with open(file_path, "rb") as f:
            raw = f.read()
        detected = chardet.detect(raw)
        encoding = detected.get("encoding", "utf-8") or "utf-8"
        text = raw.decode(encoding, errors="replace")
        text = sanitize_text(text)
        if not text.strip():
            logger.warning(f"Empty content from {file_path}")
            return []
        logger.info(f"Loaded text file: {Path(file_path).name} ({len(text)} chars)")
        return [Document(
            page_content=text,
            metadata={"source": file_path, "file_type": "text",
                       "extension": Path(file_path).suffix.lower()}
        )]
