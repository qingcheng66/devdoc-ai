import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from src.utils.logger import logger


class ZipLoader:
    def can_load(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == ".zip"

    def load(self, file_path: str) -> List[Document]:
        extract_dir = os.path.join(tempfile.gettempdir(), f"devdoc_zip_{uuid.uuid4().hex[:8]}")
        os.makedirs(extract_dir, exist_ok=True)
        docs = []
        try:
            shutil.unpack_archive(file_path, extract_dir, "zip")
            from src.parser.loader import UnifiedLoader
            loader = UnifiedLoader()
            for root, _, files in os.walk(extract_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    if fpath.endswith(".zip"):
                        continue
                    if loader.can_load(fpath):
                        try:
                            loaded = loader.load(fpath)
                            for doc in loaded:
                                doc.metadata["zip_source"] = file_path
                            docs.extend(loaded)
                        except Exception as e:
                            logger.warning(f"Skipping {fname} in zip: {e}")
            logger.info(f"Loaded ZIP: {Path(file_path).name} ({len(docs)} docs)")
        except Exception as e:
            logger.error(f"Failed to extract ZIP {file_path}: {e}")
        finally:
            shutil.rmtree(extract_dir, ignore_errors=True)
        return docs
