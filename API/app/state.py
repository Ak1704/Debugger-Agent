from typing import TypedDict, Any

class DebugState(TypedDict, total=False):
    owner: str
    repo: str
    commit: str
    failure_log: str
    file_path: str
    failure_analysis: dict[str, Any]
    git_context: dict[str, Any]
    retrieved_code: list[dict[str, Any]]
    diagnosis: str
    patch: str
    report: dict[str, Any]
