from typing import List


def should_run_skill(skill_name: str, selected_outputs: List[str]) -> bool:
    return skill_name in selected_outputs


def get_enabled_skills(selected_outputs: List[str]) -> List[str]:
    return selected_outputs
