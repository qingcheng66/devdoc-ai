import json
import os
import uuid
from typing import List

from src.agent.state import AgentState
from config.prompts import INSTRUCTION_ANALYSIS_SYSTEM_PROMPT
from src.parser.loader import UnifiedLoader
from src.rag.splitter import DocumentSplitter
from src.rag.embedder import Embedder
from src.rag.vector_store import ChromaStore
from src.rag.retriever import Retriever
from src.skills.report_skill import ReportSkill
from src.skills.ppt_skill import PPTSkill
from src.skills.diagram_skill import DiagramSkill
from src.utils.llm_client import DeepSeekClient
from src.utils.logger import logger

_loader = UnifiedLoader()
_splitter = DocumentSplitter()
_embedder = Embedder()
_llm_client = DeepSeekClient()


def _get_or_create_store(collection_name: str) -> ChromaStore:
    return ChromaStore(collection_name=collection_name)


def _get_retriever(collection_name: str) -> Retriever:
    return Retriever(store=_get_or_create_store(collection_name), embedder=_embedder)


def parse_input_node(state: AgentState) -> AgentState:
    logger.info(f"[parse_input] Starting, session={state.get('session_id')}")
    state["current_step"] = "parsing"

    file_paths = state.get("file_paths", [])
    pasted_text = state.get("pasted_text", "")

    all_docs = []
    if file_paths:
        all_docs.extend(_loader.load_batch(file_paths))
    if pasted_text.strip():
        all_docs.extend(_loader.load_pasted_text(pasted_text))

    if not all_docs:
        err = "未找到可解析的内容，请上传文件或粘贴文本"
        logger.warning(f"[parse_input] {err}")
        state["errors"].append(err)
    else:
        logger.info(f"[parse_input] Loaded {len(all_docs)} documents")

    state["raw_documents"] = all_docs
    return state


def embed_docs_node(state: AgentState) -> AgentState:
    logger.info("[embed_docs] Starting")
    state["current_step"] = "embedding"

    docs = state.get("raw_documents", [])
    if not docs:
        return state

    chunks = _splitter.split(docs)
    texts = [c.page_content for c in chunks]
    embeddings = _embedder.embed_documents(texts)

    collection_name = state.get("collection_name", f"devdoc_{uuid.uuid4().hex[:8]}")
    store = _get_or_create_store(collection_name)
    store.add_documents(chunks, embeddings)

    state["chunked_documents"] = chunks
    logger.info(f"[embed_docs] Stored {len(chunks)} chunks in '{collection_name}'")
    return state


def analyze_instructions_node(state: AgentState) -> AgentState:
    """Parse user instructions into structured analysis via LLM."""
    instructions = state.get("user_instructions", "").strip()
    if not instructions:
        state["instruction_analysis"] = {"has_instructions": False}
        logger.info("[analyze_instructions] No user instructions, skipping")
        return state

    logger.info(f"[analyze_instructions] Analyzing: {instructions[:80]}...")
    try:
        llm = DeepSeekClient()
        prompt = f"分析以下用户指令：\n\n{instructions}"
        result = llm.chat(
            system_prompt=INSTRUCTION_ANALYSIS_SYSTEM_PROMPT,
            user_message=prompt,
        )
        analysis = json.loads(_clean_json(result))
        analysis["has_instructions"] = True
        analysis["raw"] = instructions
        state["instruction_analysis"] = analysis
        logger.info(f"[analyze_instructions] Keywords: {analysis.get('focus_keywords', [])}, "
                     f"style={analysis.get('style')}, language={analysis.get('language')}")
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"[analyze_instructions] Parse failed: {e}, using fallback")
        state["instruction_analysis"] = {
            "has_instructions": True,
            "focus_keywords": [],
            "style": "详细",
            "language": "zh",
            "focus_sections": [],
            "skip_sections": [],
            "slide_count": None,
            "diagram_types": [],
            "custom_requirements": instructions,
            "raw": instructions,
        }
    return state


def _clean_json(text: str) -> str:
    """Remove markdown code fences from LLM JSON output."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text


def report_skill_node(state: AgentState) -> AgentState:
    logger.info("[report_skill] Starting")
    state["current_step"] = "generating_report"
    collection_name = state.get("collection_name", "")
    retriever = _get_retriever(collection_name) if collection_name else None

    if retriever is None:
        output = {"skill_name": "report", "status": "error",
                   "output_file_path": "", "preview_content": "",
                   "error_message": "Retriever not available"}
    else:
        skill = ReportSkill(retriever=retriever, llm_client=_llm_client)
        output = skill.generate(state)

    state["skill_outputs"].append(output)
    return state


def ppt_skill_node(state: AgentState) -> AgentState:
    logger.info("[ppt_skill] Starting")
    state["current_step"] = "generating_ppt"
    collection_name = state.get("collection_name", "")
    retriever = _get_retriever(collection_name) if collection_name else None

    if retriever is None:
        output = {"skill_name": "ppt", "status": "error",
                   "output_file_path": "", "preview_content": "",
                   "error_message": "Retriever not available"}
    else:
        skill = PPTSkill(retriever=retriever, llm_client=_llm_client)
        output = skill.generate(state)

    state["skill_outputs"].append(output)
    return state


def diagram_skill_node(state: AgentState) -> AgentState:
    logger.info("[diagram_skill] Starting")
    state["current_step"] = "generating_diagrams"
    collection_name = state.get("collection_name", "")
    retriever = _get_retriever(collection_name) if collection_name else None

    if retriever is None:
        output = {"skill_name": "diagram", "status": "error",
                   "output_file_path": "", "preview_content": "",
                   "error_message": "Retriever not available"}
    else:
        skill = DiagramSkill(retriever=retriever, llm_client=_llm_client)
        output = skill.generate(state)

    state["skill_outputs"].append(output)
    return state


def merge_outputs_node(state: AgentState) -> AgentState:
    logger.info("[merge_outputs] Aggregating skill outputs")
    state["current_step"] = "complete"

    skill_outputs = state.get("skill_outputs", [])
    for so in skill_outputs:
        name = so.get("skill_name", "unknown")
        status = so.get("status", "unknown")
        logger.info(f"[merge_outputs] {name}: {status}")

    errors = state.get("errors", [])
    for so in skill_outputs:
        if so.get("status") == "error" and so.get("error_message"):
            errors.append(f"[{so.get('skill_name', '')}] {so.get('error_message', '')}")
    state["errors"] = errors

    return state
