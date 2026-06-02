import os
import shutil
import time
from pathlib import Path

from config.settings import settings
from src.utils.logger import logger


class FileManager:
    @staticmethod
    def ensure_dirs(*dirs: str):
        for d in dirs:
            Path(d).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_session_upload_dir(session_id: str) -> str:
        path = os.path.join(settings.upload_dir, session_id)
        Path(path).mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_session_output_dir(session_id: str) -> str:
        path = os.path.join(settings.output_dir, session_id)
        Path(path).mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def save_uploaded_file(session_id: str, file_name: str, content: bytes) -> str:
        upload_dir = FileManager.get_session_upload_dir(session_id)
        file_path = os.path.join(upload_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(content)
        return file_path

    @staticmethod
    def cleanup_old_sessions():
        max_age = settings.session_ttl_hours * 3600
        now = time.time()
        for base_dir in [settings.upload_dir, settings.output_dir]:
            path = Path(base_dir)
            if not path.exists():
                continue
            for session_dir in path.iterdir():
                if session_dir.is_dir() and (now - session_dir.stat().st_mtime) > max_age:
                    shutil.rmtree(session_dir, ignore_errors=True)
                    logger.info(f"Cleaned up old session: {session_dir}")

    @staticmethod
    def cleanup_session(session_id: str):
        for base_dir in [settings.upload_dir, settings.output_dir]:
            path = Path(base_dir) / session_id
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
