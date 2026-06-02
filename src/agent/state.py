import operator
from typing import List, Annotated, Any
from typing_extensions import TypedDict


class SkillOutput(TypedDict, total=False):
    skill_name: str
    status: str
    output_file_path: str
    preview_content: str
    error_message: str


def _last_value(current: Any, new: Any) -> Any:
    """Reducer: keep the latest non-None value."""
    return new if new is not None else current


def _merge_lists(current: List, new: List) -> List:
    """Reducer: concatenate lists."""
    return (current or []) + (new or [])


def skill_outputs_reducer(current: List[SkillOutput], new: List[SkillOutput]) -> List[SkillOutput]:
    merged = {s.get("skill_name"): s for s in (current or [])}
    for s in (new or []):
        merged[s.get("skill_name")] = s
    return list(merged.values())


def str_reducer(current: str, new: str) -> str:
    """Keep non-empty or latest."""
    return new if new else current


# All fields use Annotated to support LangGraph parallel node execution
class AgentState(TypedDict, total=False):
    file_paths: Annotated[List[str], _last_value]
    pasted_text: Annotated[str, str_reducer]
    session_id: Annotated[str, str_reducer]
    output_selections: Annotated[List[str], _last_value]
    user_instructions: Annotated[str, str_reducer]
    instruction_analysis: Annotated[dict, _last_value]

    raw_documents: Annotated[List[Any], _last_value]
    collection_name: Annotated[str, str_reducer]
    chunked_documents: Annotated[List[Any], _last_value]

    skill_outputs: Annotated[List[SkillOutput], skill_outputs_reducer]
    current_step: Annotated[str, str_reducer]
    errors: Annotated[List[str], _merge_lists]


def create_initial_state(
    file_paths: List[str],
    pasted_text: str,
    session_id: str,
    output_selections: List[str],
    user_instructions: str = "",
    instruction_analysis: dict = {},
) -> AgentState:
    return AgentState(
        file_paths=file_paths,
        pasted_text=pasted_text,
        session_id=session_id,
        output_selections=output_selections,
        user_instructions=user_instructions,
        instruction_analysis=instruction_analysis,
        raw_documents=[],
        collection_name=f"devdoc_{session_id}",
        chunked_documents=[],
        skill_outputs=[],
        current_step="init",
        errors=[],
    )
