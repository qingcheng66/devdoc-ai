from typing import List, Optional

from langgraph.graph import StateGraph, END

from src.agent.state import AgentState, create_initial_state
from src.agent.nodes import (
    parse_input_node,
    embed_docs_node,
    analyze_instructions_node,
    report_skill_node,
    ppt_skill_node,
    diagram_skill_node,
    merge_outputs_node,
)
from src.agent.router import get_enabled_skills
from src.utils.logger import logger


class DevDocAgent:
    def run(
        self,
        file_paths: List[str],
        pasted_text: str,
        session_id: str,
        output_selections: List[str],
        instructions: str = "",
    ) -> AgentState:
        logger.info(f"DevDocAgent.run: session={session_id}, "
                     f"files={len(file_paths)}, selections={output_selections}")

        if not output_selections:
            return AgentState(
                file_paths=file_paths, pasted_text=pasted_text,
                session_id=session_id, output_selections=[],
                user_instructions=instructions,
                skill_outputs=[], errors=["未选择任何输出类型"],
                current_step="error", raw_documents=[],
                collection_name="", chunked_documents=[],
            )

        state = create_initial_state(
            file_paths=file_paths,
            pasted_text=pasted_text,
            session_id=session_id,
            output_selections=output_selections,
            user_instructions=instructions,
        )

        # Step 1: parse
        state = parse_input_node(state)

        # Step 2: embed
        state = embed_docs_node(state)
        if state.get("errors") and any("未找到" in e for e in state["errors"]):
            return state

        # Step 3: analyze user instructions
        state = analyze_instructions_node(state)

        # Step 4: run selected skills SEQUENTIALLY (avoids LangGraph parallel merge issues)
        skills = {"report": report_skill_node, "ppt": ppt_skill_node, "diagram": diagram_skill_node}
        for name in output_selections:
            if name in skills:
                logger.info(f"Running skill: {name}")
                try:
                    state = skills[name](state)
                except Exception as e:
                    logger.error(f"Skill {name} failed: {e}")
                    state["skill_outputs"].append({
                        "skill_name": name, "status": "error",
                        "output_file_path": "", "preview_content": "",
                        "error_message": str(e),
                    })

        # Step 5: merge
        state = merge_outputs_node(state)

        logger.info(f"DevDocAgent.run complete: {len(state.get('skill_outputs', []))} outputs")
        return state
