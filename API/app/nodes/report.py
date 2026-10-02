def make_report(state):
    return {"report": {
        "repository": f'{state.get("owner")}/{state.get("repo")}',
        "commit": state.get("commit"),
        "diagnosis": state.get("diagnosis"),
        "patch": state.get("patch"),
        "validation": "NOT_RUN",
        "note": "Patch is a proposal; no execution or test validation was performed."
    }}
