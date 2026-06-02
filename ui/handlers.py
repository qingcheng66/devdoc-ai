import os
import uuid
import shutil
from pathlib import Path
from typing import List, Tuple

import gradio as gr

from config.settings import settings
from src.agent.graph import DevDocAgent
from src.utils.file_manager import FileManager
from src.utils.logger import logger


def _status_html(text: str, kind: str = "idle") -> str:
    return f'<div class="status-bar status-{kind}">{text}</div>'


def handle_generate(
    files: List,
    pasted_text: str,
    gen_report: bool,
    gen_ppt: bool,
    gen_diagram: bool,
    instructions: str,
    progress=gr.Progress(),
) -> Tuple[str, str, str, str, str, str]:
    session_id = uuid.uuid4().hex[:12]
    logger.info(f"New session: {session_id}")
    fm = FileManager()
    fm.ensure_dirs(settings.upload_dir, settings.output_dir)

    # Build selections
    selections = []
    if gen_report:
        selections.append("report")
    if gen_ppt:
        selections.append("ppt")
    if gen_diagram:
        selections.append("diagram")

    if not selections:
        return ("", _status_html("请选择至少一种输出类型", "error"),
                None, None, None, "未选择输出类型")

    # Validate input
    has_files = files is not None and len(files) > 0
    has_text = pasted_text and pasted_text.strip()

    if not has_files and not has_text:
        return ("", _status_html("请上传文件或粘贴文本", "error"),
                None, None, None, "无输入内容")

    # Save uploaded files
    file_paths = []
    if has_files:
        progress(0.1, desc="保存上传文件...")
        for f in files:
            if isinstance(f, str):
                file_paths.append(f)
            elif hasattr(f, "name"):
                if hasattr(f, "read"):
                    content = f.read()
                    saved = fm.save_uploaded_file(session_id, os.path.basename(f.name), content)
                    file_paths.append(saved)
                elif isinstance(f.name, str) and os.path.exists(f.name):
                    dest = os.path.join(fm.get_session_upload_dir(session_id), os.path.basename(f.name))
                    shutil.copy2(f.name, dest)
                    file_paths.append(dest)

    if not file_paths and (not pasted_text or not pasted_text.strip()):
        return ("", _status_html("文件上传失败，请重试", "error"),
                None, None, None, "上传错误")

    # Run agent
    progress(0.2, desc="AI 分析处理中...")
    agent = DevDocAgent()
    try:
        result = agent.run(
            file_paths=file_paths,
            pasted_text=pasted_text.strip() if pasted_text else "",
            session_id=session_id,
            output_selections=selections,
            instructions=instructions.strip() if instructions else "",
        )
    except Exception as e:
        logger.error(f"Agent run failed: {e}", exc_info=True)
        return ("", _status_html(f"处理失败: {e}", "error"),
                None, None, None, str(e))

    # Extract results
    progress(0.9, desc="整理结果...")
    skill_outputs = result.get("skill_outputs", [])
    output_map = {so.get("skill_name"): so for so in skill_outputs}

    preview_parts = []
    errors = result.get("errors", [])

    # Report
    report_path = None
    report_output = output_map.get("report", {})
    if report_output.get("status") == "completed":
        report_path = report_output.get("output_file_path", "")
        preview_parts.append(report_output.get("preview_content", "报告已生成"))
    elif report_output.get("status") == "error":
        errors.append(f"报告生成失败: {report_output.get('error_message', '')}")

    # PPT
    ppt_path = None
    ppt_output = output_map.get("ppt", {})
    if ppt_output.get("status") == "completed":
        ppt_path = ppt_output.get("output_file_path", "")
        preview_parts.append(ppt_output.get("preview_content", "PPT已生成"))
    elif ppt_output.get("status") == "error":
        errors.append(f"PPT生成失败: {ppt_output.get('error_message', '')}")

    # Diagram — skill already packs everything into diagrams.zip
    diagram_path = None
    diagram_output = output_map.get("diagram", {})
    if diagram_output.get("status") == "completed":
        zip_path = diagram_output.get("output_file_path", "")
        preview_parts.append(diagram_output.get("preview_content", "图表已生成"))
        if zip_path and os.path.isfile(zip_path):
            diagram_path = zip_path
    elif diagram_output.get("status") == "error":
        errors.append(f"图表生成失败: {diagram_output.get('error_message', '')}")

    preview = "\n\n".join(preview_parts) if preview_parts else "（无内容生成）"
    status_html = _status_html("生成完成！", "done") if not errors else \
                  _status_html(f"部分完成（{len(errors)}个错误）", "warning")
    error_text = "\n".join(errors) if errors else ""

    progress(1.0, desc="完成!")

    # Convert to absolute paths for Gradio to serve files
    def _abs(p: str):
        if p and os.path.isfile(p):
            return os.path.abspath(p)
        return None

    return (
        preview,
        status_html,
        _abs(report_path or ""),
        _abs(ppt_path or ""),
        _abs(diagram_path or ""),
        error_text,
    )
