from app.services.code_search import CodeRetriever


MAX_SOURCE_CHARS = 8000


def retrieve_code(state):
    path = state.get("file_path")

    if not path:
        failure_analysis = state.get("failure_analysis", {})

        if isinstance(failure_analysis, dict):
            paths = failure_analysis.get("candidate_paths", [])
        else:
            paths = []

        path = next(
            (p for p in paths if not p.startswith("/")),
            None,
        )

    if not path:
        return {
            "retrieved_code": ""
        }

    code = CodeRetriever().retrieve_file(
        state["owner"],
        state["repo"],
        state["commit"],
        path,
    )

    # GitHub returns the complete source file.
    # Do not pass an arbitrarily large file to the LLM.
    results = []

    for item in code:
        source = item.get("source", "")

        if len(source) > MAX_SOURCE_CHARS:
            source = (
                source[:MAX_SOURCE_CHARS]
                + "\n\n"
                "[...source truncated for LLM context...]"
            )

        results.append(
            {
                "path": item.get("path"),
                "commit": item.get("commit"),
                "source": source,
            }
        )

    retrieved_code = "\n\n".join(
        f"FILE: {item['path']}\n"
        f"COMMIT: {item['commit']}\n"
        f"{item['source']}"
        for item in results
    )

    print(
        f"[retrieval] file={path} "
        f"chars={len(retrieved_code)}"
    )

    return {
        "retrieved_code": retrieved_code
    }