# Universal AI CI/CD Debugger (Groq)

API-first MVP scaffold using Groq via LangChain, GitHub API retrieval, local embeddings, ChromaDB, LangGraph, and Docker validation.

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with GROQ_API_KEY and GITHUB_TOKEN
```

Set `GROQ_MODEL` to a model ID enabled for your Groq account. `openai/gpt-oss-20b` is a Groq-hosted model ID example; it is not a Llama model. For a Llama model, use the exact currently available Llama ID shown in your Groq console.

## Run
```bash
python -m pytest
uvicorn app.main:app --reload
```
Health: `GET http://localhost:8000/health`

POST `/debug` JSON:
```json
{
  "owner":"ytdl-org",
  "repo":"youtube-dl",
  "commit":"<buggy-commit-sha>",
  "failure_log":"...pytest traceback...",
  "file_path":"youtube_dl/example.py"
}
```

The endpoint retrieves source at the specified commit and returns a diagnosis and proposed patch. This MVP does not automatically apply/test a patch yet. Treat model output as untrusted. The Docker runner is a separate isolated execution primitive and must be wired to a disposable checkout before enabling patch execution.

## Security
Never expose `ground_truth.json` to the agent. Use exact commit SHAs, least-privilege GitHub tokens, disabled Docker networking, resource limits, and disposable workspaces.
