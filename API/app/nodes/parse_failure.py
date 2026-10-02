import re

def parse_failure(state):
    log = state.get("failure_log", "")
    paths = re.findall(r'([\w./-]+\.py)', log)
    errors = re.findall(r'([A-Za-z]+Error):?\s*(.*)', log)
    return {"failure_analysis": {
        "candidate_paths": list(dict.fromkeys(paths))[:20],
        "error_signatures": [{"type": e[0], "message": e[1][:500]} for e in errors[-10:]],
        "summary": log[-5000:],
    }}
