import os
import subprocess
from pathlib import Path

from config.prompts import REPORT_SYSTEM_PROMPT, REPORT_TASK_TEMPLATE
from config.settings import settings
from src.skills.base import BaseSkill
from src.utils.logger import logger


class ReportSkill(BaseSkill):
    skill_name = "report"

    def _get_retrieval_query(self) -> str:
        return "项目目标 研究方法 实验结果 数据分析 系统设计 实现过程 测试结果 结论"

    def _get_system_prompt(self) -> str:
        return REPORT_SYSTEM_PROMPT

    def _build_prompt(self, context: str, instruction_block: str = "") -> str:
        return REPORT_TASK_TEMPLATE.format(context=context, instruction_block=instruction_block)

    def _generate_artifact(self, llm_output: str, session_id: str) -> str:
        md_content = self._clean_markdown(llm_output)

        output_dir = os.path.join(settings.output_dir, session_id)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Save .md file
        md_path = os.path.join(output_dir, "report.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # Convert to DOCX via Pandoc
        docx_path = os.path.join(output_dir, "report.docx")
        cmd = [
            settings.pandoc_path, md_path,
            "-o", docx_path,
            "--from", "markdown+pipe_tables",
            "--to", "docx",
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Report DOCX saved to {docx_path}")
        return docx_path

    def _generate_preview(self, llm_output: str) -> str:
        md_content = self._clean_markdown(llm_output)
        return md_content[:500] + ("..." if len(md_content) > 500 else "")

    @staticmethod
    def _clean_markdown(llm_output: str) -> str:
        text = llm_output.strip()
        # Remove markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return text
