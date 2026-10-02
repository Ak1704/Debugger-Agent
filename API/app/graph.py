from langgraph.graph import StateGraph, START, END
from app.state import DebugState
from app.nodes.parse_failure import parse_failure
from app.nodes.git_analysis import git_analysis
from app.nodes.retrieval import retrieve_code
from app.nodes.diagnosis import diagnose
from app.nodes.patch import generate_patch
from app.nodes.report import make_report

def build_graph():
    graph = StateGraph(DebugState)
    graph.add_node("parse_failure", parse_failure)
    graph.add_node("git_analysis", git_analysis)
    graph.add_node("retrieve_code", retrieve_code)
    graph.add_node("diagnose", diagnose)
    graph.add_node("generate_patch", generate_patch)
    graph.add_node("report", make_report)
    graph.add_edge(START, "parse_failure")
    graph.add_edge("parse_failure", "git_analysis")
    graph.add_edge("git_analysis", "retrieve_code")
    graph.add_edge("retrieve_code", "diagnose")
    graph.add_edge("diagnose", "generate_patch")
    graph.add_edge("generate_patch", "report")
    graph.add_edge("report", END)
    return graph.compile()
