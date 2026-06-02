import os
import re
import json
import zipfile
from pathlib import Path

from config.prompts import DIAGRAM_SYSTEM_PROMPT, DIAGRAM_TASK_TEMPLATE
from config.settings import settings
from src.skills.base import BaseSkill
from src.utils.mermaid_renderer import MermaidRenderer
from src.utils.logger import logger


class DiagramSkill(BaseSkill):
    skill_name = "diagram"

    def __init__(self, retriever, llm_client=None, max_retries=2):
        super().__init__(retriever, llm_client, max_retries)
        self.renderer = MermaidRenderer()

    def _get_retrieval_query(self) -> str:
        return "系统流程 数据处理流程 用户交互 用例 角色 项目时间线 开发阶段 里程碑"

    def _get_system_prompt(self) -> str:
        return DIAGRAM_SYSTEM_PROMPT

    def _build_prompt(self, context: str, instruction_block: str = "") -> str:
        return DIAGRAM_TASK_TEMPLATE.format(context=context, instruction_block=instruction_block)

    def _generate_artifact(self, llm_output: str, session_id: str) -> str:
        output_dir = os.path.join(settings.output_dir, session_id)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        mermaid_blocks = self._extract_mermaid_blocks(llm_output)
        if not mermaid_blocks:
            full_code = self._try_extract_mermaid(llm_output)
            if full_code:
                mermaid_blocks = [{"type": "diagram", "title": "图表", "code": full_code}]

        rendered = []
        for i, block in enumerate(mermaid_blocks):
            name = f"diagram_{i + 1}_{block.get('type', 'unknown')}"
            result = self.renderer.render(block["code"], output_dir, name)
            if result["status"] == "success":
                rendered.append(result["png"])
            elif result.get("source"):
                rendered.append(result["source"])

        # Write manifest
        manifest_path = os.path.join(output_dir, "diagrams_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({"files": rendered, "blocks": mermaid_blocks}, f, ensure_ascii=False, indent=2)

        # Always pack all outputs into a single zip for download
        zip_path = os.path.join(output_dir, "diagrams.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname in sorted(os.listdir(output_dir)):
                fpath = os.path.join(output_dir, fname)
                if os.path.isfile(fpath) and not fname.endswith(".zip"):
                    zf.write(fpath, fname)

        logger.info(f"[diagram] Packed {len(rendered)} diagrams → {zip_path}")
        return zip_path

    def _generate_preview(self, llm_output: str) -> str:
        blocks = self._extract_mermaid_blocks(llm_output)
        if blocks:
            lines = [f"- {b.get('title', b.get('type', '图表'))}" for b in blocks]
            return "生成以下图表：\n" + "\n".join(lines)
        return llm_output[:500] + ("..." if len(llm_output) > 500 else "")

    @staticmethod
    def _extract_mermaid_blocks(text: str) -> list[dict]:
        blocks = []
        pattern = r"```mermaid\s*\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        for i, code in enumerate(matches):
            code = code.strip()
            # Detect mermaid diagram type from the first line of code
            first_line = code.split("\n")[0].strip().lower() if code else ""
            block_type = "flowchart"
            if "sequencediagram" in first_line:
                block_type = "sequence"
            elif "erdiagram" in first_line:
                block_type = "er"
            elif "classdiagram" in first_line:
                block_type = "class"
            elif "statediagram" in first_line or "state-v2" in first_line:
                block_type = "state"
            elif "gantt" in first_line:
                block_type = "gantt"
            elif "pie" in first_line:
                block_type = "pie"
            elif "flowchart" in first_line or "graph" in first_line:
                block_type = "flowchart"
            # Try to find a title before the code block
            title_match = re.search(
                r"(?:###?\s*|##\s*|-\s*\*\*)([^\n]*)" +
                re.escape("```mermaid"),
                text[:text.find(code) + text.find("```mermaid")] if text.find("```mermaid") > text.find(code) else text,
                re.DOTALL,
            )
            title = title_match.group(1).strip() if title_match else f"图表{i + 1}"
            blocks.append({"type": block_type, "title": title, "code": code})
        return blocks

    @staticmethod
    def _try_extract_mermaid(text: str) -> str:
        patterns = [
            r"(?:flowchart|graph)\s+(?:TD|LR|TB|RL)[\s\S]*?",
            r"sequenceDiagram[\s\S]*?",
            r"erDiagram[\s\S]*?",
            r"classDiagram[\s\S]*?",
            r"stateDiagram[-\w]*[\s\S]*?",
            r"gantt[\s\S]*?",
            r"pie\s+title[\s\S]*?",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return ""
