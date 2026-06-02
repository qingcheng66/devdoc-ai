from pathlib import Path

from config.prompts import PPT_CONTENT_SYSTEM_PROMPT, PPT_CONTENT_TASK_TEMPLATE
from config.settings import settings
from src.skills.base import BaseSkill
from src.skills.ppt_template import generate_pptx
from src.utils.logger import logger


class PPTSkill(BaseSkill):
    skill_name = "ppt"

    def _get_retrieval_query(self) -> str:
        return "项目概述 核心功能 技术亮点 项目成果 总结展望 关键指标 创新点"

    def _get_system_prompt(self) -> str:
        return PPT_CONTENT_SYSTEM_PROMPT

    def _build_prompt(self, context: str, instruction_block: str = "") -> str:
        return PPT_CONTENT_TASK_TEMPLATE.format(
            context=context, instruction_block=instruction_block
        )

    def _generate_artifact(self, llm_output: str, session_id: str) -> str:
        data = self._parse_json_output(llm_output)
        slides = data.get("slides", [])
        if not slides:
            raise ValueError("LLM 未生成 slides 内容 —— 请重试")

        output_dir = Path(settings.output_dir) / session_id
        output_dir.mkdir(parents=True, exist_ok=True)
        pptx_path = output_dir / "presentation.pptx"

        template = settings.ppt_template_path or None
        return str(generate_pptx(slides, pptx_path, template_path=template))

    def _generate_preview(self, llm_output: str) -> str:
        try:
            data = self._parse_json_output(llm_output)
            title = data.get("title", "")
            slides = data.get("slides", [])
            if slides:
                type_names = {
                    "cover": "封面", "toc": "目录", "content": "内容",
                    "section": "过渡", "summary": "总结",
                }
                lines = [f"**{title}**\n\n共 {len(slides)} 页"]
                for s in slides[:8]:
                    t = type_names.get(s.get("type", ""), "")
                    lines.append(f"- [{t}] {s.get('title', '')}")
                if len(slides) > 8:
                    lines.append(f"... 等 {len(slides)} 页")
                return "\n".join(lines)
            return llm_output[:500] + ("..." if len(llm_output) > 500 else "")
        except Exception:
            return llm_output[:500] + ("..." if len(llm_output) > 500 else "")
