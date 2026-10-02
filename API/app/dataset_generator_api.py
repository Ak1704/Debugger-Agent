"""
FastAPI bridge: run the dataset generator in a BugsInPy++ Docker worker.

Host requirements:
  - Docker Desktop installed and running
  - Build the worker image once (see commands in the answer)
  - API process has permission to invoke `docker`

This avoids requiring BugsInPy++ on the host Python/VS Code environment.
"""
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

router = APIRouter(prefix="/dataset", tags=["dataset-generator"])

IMAGE_NAME = "ci-debugger-bugsinpy:local"
OUTPUT_DIR = Path("dataset/cases").resolve()


class GenerateDatasetRequest(BaseModel):
    project: str = Field(..., min_length=1, max_length=100)
    bug_id: int = Field(..., ge=1)
    overwrite: bool = False


def _run_worker(project: str, bug_id: int, overwrite: bool) -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Verify Docker is reachable from the same environment as uvicorn.
    check = subprocess.run(
        ["docker", "info"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if check.returncode:
        raise RuntimeError(
            "Docker is not reachable. Start Docker Desktop and retry. "
            + (check.stderr.strip() or check.stdout.strip())
        )

    command = [
        "docker", "run", "--rm",
        "--network", "bridge",
        "-v", f"{OUTPUT_DIR}:/workspace/dataset/cases",
        IMAGE_NAME,
        "--project", project,
        "--bug", str(bug_id),
    ]
    if overwrite:
        command.append("--overwrite")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=60 * 60,
    )

    case_dir = OUTPUT_DIR / f"{project}_{bug_id}"
    files = [
        str(case_dir / name)
        for name in ("metadata.json", "failure.json", "ground_truth.json")
        if (case_dir / name).is_file()
    ]

    if result.returncode != 0 and not files:
        raise RuntimeError(
            "Worker failed before producing dataset artifacts.\n"
            f"stdout:\n{result.stdout[-6000:]}\n"
            f"stderr:\n{result.stderr[-6000:]}"
        )

    return {
        "case_id": f"{project}_{bug_id}",
        "success": result.returncode == 0,
        "status": "generated_and_verified" if result.returncode == 0
                  else "generated_with_warnings",
        "output_dir": str(case_dir) if case_dir.exists() else None,
        "files": files,
        "worker_stdout": result.stdout[-6000:],
        "worker_stderr": result.stderr[-6000:],
    }


@router.post("/generate")
async def generate_dataset(request: GenerateDatasetRequest):
    try:
        return await run_in_threadpool(
            _run_worker,
            request.project,
            request.bug_id,
            request.overwrite,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(
            status_code=504,
            detail="Dataset generation exceeded the 60-minute timeout.",
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="Docker CLI was not found by the uvicorn process. "
                   "Install/start Docker Desktop and restart VS Code.",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
