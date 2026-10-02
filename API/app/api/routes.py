from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.graph import build_graph

router = APIRouter()
graph = build_graph()

class DebugRequest(BaseModel):
    owner: str
    repo: str
    commit: str = Field(min_length=7)
    failure_log: str = Field(min_length=1)
    file_path: str | None = None

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/debug")
def debug(request: DebugRequest):
    try:
        return graph.invoke(request.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
