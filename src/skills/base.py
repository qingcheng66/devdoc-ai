import json
import time
from abc import ABC, abstractmethod
from typing import List

from langchain_core.documents import Document
from src.rag.retriever import Retriever
from src.utils.llm_client import DeepSeekClient
from src.utils.logger import logger


class SkillOutput(dict):
    def __init__(self, skill_name: str, status: str = "pending",
                 output_file_path: str = "", preview_content: str = "",
                 error_message: str = ""):
        super().__init__(
            skill_name=skill_name,
            status=status,
            output_file_path=output_file_path,
            preview_content=preview_content,
            error_message=error_message,
        )

    @property
    def skill_name(self): return self["skill_name"]

    @property
    def status(self): return self["status"]

    @property
    def output_file_path(self): return self["output_file_path"]

    @property
    def preview_content(self): return self["preview_content"]

    @property
    def error_message(self): return self["error_message"]

    def update(self, **kwargs):
        self.update(kwargs)


class BaseSkill(ABC):
    skill_name: str = "base"

    def __init__(self, retriever: Retriever, llm_client: DeepSeekClient = None,
                 max_retries: int = 2):
        self.retriever = retriever
        self.llm = llm_client or DeepSeekClient()
        self.max_retries = max_retries

    def generate(self, state: dict) -> SkillOutput:
        logger.info(f"[{self.skill_name}] Starting generation")
        try:
            context = self._retrieve_context(state)
            if not context:
                context = "（未找到相关文档上下文，请基于通用知识生成）"
            instruction_block = self._format_instruction_block(state)
            prompt = self._build_prompt(context, instruction_block)
            llm_output = self._call_llm_with_retry(prompt)
            artifact_path = self._generate_artifact(llm_output, state.get("session_id", "default"))
            preview = self._generate_preview(llm_output)
            logger.info(f"[{self.skill_name}] Generation complete: {artifact_path}")
            return SkillOutput(
                skill_name=self.skill_name,
                status="completed",
                output_file_path=artifact_path,
                preview_content=preview,
                error_message="",
            )
        except Exception as e:
            logger.error(f"[{self.skill_name}] Failed: {e}", exc_info=True)
            return SkillOutput(
                skill_name=self.skill_name,
                status="error",
                output_file_path="",
                preview_content="",
                error_message=str(e),
            )

    def _retrieve_context(self, state: dict) -> str:
        analysis = state.get("instruction_analysis", {})
        base_query = self._get_retrieval_query()
        user_keywords = " ".join(analysis.get("focus_keywords", []))
        query = f"{base_query} {user_keywords}".strip()
        docs = self.retriever.retrieve(query)
        if not docs:
            pasted = state.get("pasted_text", "")
            if pasted:
                return pasted[:8000]
            raw_docs = state.get("raw_documents", [])
            if raw_docs:
                return "\n\n".join(d.page_content[:2000] for d in raw_docs[:5])
            return ""
        return "\n\n---\n\n".join(d.page_content for d in docs)

    def _format_instruction_block(self, state: dict) -> str:
        """Convert instruction_analysis dict into a structured prompt block."""
        analysis = state.get("instruction_analysis", {})
        if not analysis.get("has_instructions"):
            return ""

        lines = ["## 用户指令（必须严格遵守）"]

        keywords = analysis.get("focus_keywords", [])
        if keywords:
            lines.append(f"- 重点关注主题：{'、'.join(keywords)}")

        style = analysis.get("style", "")
        if style and style != "详细":
            lines.append(f"- 输出风格：{style}")

        language = analysis.get("language", "zh")
        if language == "en":
            lines.append("- 输出语言：英文（所有内容必须用英文撰写）")
        else:
            lines.append("- 输出语言：中文（所有节点、标题、标签、正文必须使用中文）")

        focus = analysis.get("focus_sections", [])
        if focus:
            lines.append(f"- 重点展开章节：{'、'.join(focus)}")

        skip = analysis.get("skip_sections", [])
        if skip:
            lines.append(f"- 跳过章节：{'、'.join(skip)}")

        diagram_types = analysis.get("diagram_types", [])
        if diagram_types:
            lines.append(f"- 需要的图表类型：{'、'.join(diagram_types)}")

        slide_count = analysis.get("slide_count")
        if slide_count is not None:
            lines.append(f"- PPT页数要求：{slide_count}页")

        custom = analysis.get("custom_requirements", "")
        if custom:
            lines.append(f"- 其他要求：{custom}")

        return "\n".join(lines) + "\n"

    @abstractmethod
    def _get_retrieval_query(self) -> str: ...

    @abstractmethod
    def _build_prompt(self, context: str, instruction_block: str = "") -> str: ...

    @abstractmethod
    def _generate_artifact(self, llm_output: str, session_id: str) -> str: ...

    @abstractmethod
    def _generate_preview(self, llm_output: str) -> str: ...

    def _call_llm_with_retry(self, prompt: str) -> str:
        for attempt in range(self.max_retries + 1):
            try:
                return self.llm.chat(system_prompt=self._get_system_prompt(),
                                     user_message=prompt)
            except Exception as e:
                logger.warning(f"[{self.skill_name}] LLM call attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries:
                    raise
                time.sleep(2 ** attempt)

    @abstractmethod
    def _get_system_prompt(self) -> str: ...

    @staticmethod
    def _parse_json_output(llm_output: str) -> dict:
        text = llm_output.strip()
        # Remove markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"[{BaseSkill.skill_name}] JSON parse error: {e}, attempting repair")
            # Try to repair common JSON issues: unclosed strings, trailing commas
            import re
            fixed = text
            # Remove trailing commas before } or ]
            fixed = re.sub(r",(\s*[}\]])", r"\1", fixed)
            # Try to close unclosed strings by finding the last valid position
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass
            # Last resort: wrap raw text as a report section
            logger.warning(f"[{BaseSkill.skill_name}] JSON repair failed, using raw text fallback")
            return {
                "title": "",
                "abstract": "",
                "keywords": [],
                "sections": [{"heading": "生成内容", "content": llm_output[:4000]}],
                "conclusion": "",
            }
