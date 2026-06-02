import subprocess
import tempfile
import os
import requests
from pathlib import Path

from config.settings import settings
from src.utils.logger import logger


class MermaidRenderer:
    def __init__(self):
        # Prefer project-local mmdc over system-wide
        project_root = Path(__file__).parent.parent.parent
        local_mmdc = project_root / "node_modules" / ".bin" / "mmdc.cmd"
        if local_mmdc.exists():
            self.cli_path = str(local_mmdc)
        else:
            self.cli_path = settings.mermaid_cli_path
        self.api_url = settings.mermaid_api_url

    def _render_with_cli(self, mermaid_code: str, output_path: str) -> bool:
        try:
            mmd_file = output_path.replace(".png", ".mmd")
            with open(mmd_file, "w", encoding="utf-8") as f:
                f.write(mermaid_code)
            result = subprocess.run(
                [self.cli_path, "-i", mmd_file, "-o", output_path],
                capture_output=True, text=True, timeout=30,
                encoding="utf-8", errors="replace",
            )
            os.remove(mmd_file)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _render_with_api(self, mermaid_code: str, output_path: str) -> bool:
        try:
            encoded = self._encode_mermaid(mermaid_code)
            url = f"{self.api_url}/img/{encoded}?type=png"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return True
            return False
        except requests.RequestException:
            return False

    def render(self, mermaid_code: str, output_dir: str, name: str) -> dict:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        png_path = os.path.join(output_dir, f"{name}.png")

        success = self._render_with_cli(mermaid_code, png_path)
        if not success:
            logger.warning("Mermaid CLI failed, trying API fallback")
            success = self._render_with_api(mermaid_code, png_path)

        if success:
            logger.info(f"Diagram rendered: {png_path}")
            return {"png": png_path, "status": "success"}
        else:
            mmd_path = os.path.join(output_dir, f"{name}.mmd")
            with open(mmd_path, "w", encoding="utf-8") as f:
                f.write(mermaid_code)
            logger.error(f"Failed to render diagram, saved source to {mmd_path}")
            return {"png": "", "source": mmd_path, "status": "error"}

    @staticmethod
    def _encode_mermaid(code: str) -> str:
        import base64
        import zlib
        data = zlib.compress(code.encode("utf-8"), 9)
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")
