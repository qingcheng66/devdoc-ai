"""Adapter for ppt-master's SVG → PPTX conversion engine.

Calls create_pptx_with_native_svg() directly — no full project structure needed.
Falls back to Pandoc (markdown → pptx) when SVG conversion fails.
"""

import os
import subprocess
import sys
from pathlib import Path

from config.settings import settings
from src.utils.logger import logger

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_PPT_MASTER_SCRIPTS = _PROJECT_ROOT / ".agents/skills/ppt-master/scripts"


def _ensure_ppt_master_on_path():
    if str(_PPT_MASTER_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_PPT_MASTER_SCRIPTS))


def convert_svg_to_pptx(svg_paths: list[Path], output_path: Path,
                        canvas_format: str = "ppt169") -> Path:
    """Convert a list of SVG files to a native PPTX via ppt-master's engine.

    Args:
        svg_paths: SVG file paths (one per slide), in order.
        output_path: Destination .pptx path.
        canvas_format: 'ppt169' (16:9) or 'ppt43' (4:3).

    Returns:
        The output_path on success.
    """
    _ensure_ppt_master_on_path()
    from svg_to_pptx.pptx_builder import create_pptx_with_native_svg

    output_path.parent.mkdir(parents=True, exist_ok=True)
    create_pptx_with_native_svg(
        svg_files=svg_paths,
        output_path=output_path,
        canvas_format=canvas_format,
        transition="fade",
        animation="auto",
        use_compat_mode=True,
    )
    logger.info(f"PPTX created: {output_path} ({len(svg_paths)} slides)")
    return output_path


def convert_markdown_via_pandoc(slides_md: list[str], title: str,
                                output_path: Path) -> Path:
    """Fallback: join markdown slides and convert to PPTX via Pandoc.

    Args:
        slides_md: List of markdown strings, one per slide.
        title: Presentation title (becomes slide 1 heading).
        output_path: Destination .pptx path.

    Returns:
        The output_path on success.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    full_md = f"% {title}\n\n"
    for i, slide in enumerate(slides_md):
        full_md += slide.strip() + "\n\n"
        if i < len(slides_md) - 1:
            full_md += "----------\n\n"

    md_path = output_path.with_suffix(".md")
    md_path.write_text(full_md, encoding="utf-8")

    pandoc = getattr(settings, "pandoc_path", "pandoc")
    cmd = [
        pandoc,
        str(md_path),
        "-o", str(output_path),
        "--from", "markdown",
        "--to", "pptx",
    ]
    logger.info(f"Running Pandoc: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"Pandoc failed: {result.stderr}")
    logger.info(f"PPTX created via Pandoc: {output_path}")
    return output_path


def validate_svg(svg_content: str) -> bool:
    """Basic validation that svg_content looks like a valid SVG."""
    stripped = svg_content.strip()
    if not stripped.startswith("<svg") and not stripped.startswith("<?xml"):
        return False
    if "viewBox" not in stripped[:500]:
        return False
    if "</svg>" not in stripped[-100:]:
        return False
    return True
