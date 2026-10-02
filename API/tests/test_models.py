from app.nodes.parse_failure import parse_failure

def test_parse_failure_extracts_python_path_and_error():
    state = {"failure_log": "File \"pkg/mod.py\", line 4\nTypeError: bad value"}
    result = parse_failure(state)["failure_analysis"]
    assert "pkg/mod.py" in result["candidate_paths"]
    assert result["error_signatures"][0]["type"] == "TypeError"
