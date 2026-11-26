import operator
from typing import Annotated, Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send

class FileReviewState(TypedDict):
    filename: str
    diff_content: str
    review_status: str
    vulnerabilities_found: List[str]

class OverallGraphState(TypedDict):
    pull_request_id: str
    changed_files: List[Dict[str, str]]
    consolidated_reviews: Annotated[List[Dict[str, Any]], operator.add]
    overall_status: str

def analyze_individual_file_node(state: FileReviewState) -> Dict[str, Any]:
    """Independent worker node executed concurrently per forked file."""
    print(f"[WORKER] Reviewing file: {state['filename']} ({len(state['diff_content'])} bytes)")
    vulns = []
    if "eval(" in state["diff_content"]:
        vulns.append("CRITICAL: Insecure eval() detected")
    
    return {
        "consolidated_reviews": [{
            "file": state["filename"],
            "passed": len(vulns) == 0,
            "vulnerabilities": vulns
        }]
    }

def dynamic_fork_router(state: OverallGraphState) -> List[Send]:
    """Generates a dynamic list of Send objects during Pregel superstep dispatch."""
    forked_sends = []
    for file_info in state["changed_files"]:
        payload: FileReviewState = {
            "filename": file_info["filename"],
            "diff_content": file_info["diff"],
            "review_status": "IN_PROGRESS",
            "vulnerabilities_found": []
        }
        forked_sends.append(Send("review_file_node", payload))
    print(f"[PREGEL FORK] Dynamically spawned {len(forked_sends)} concurrent review subgraphs.")
    return forked_sends

def synthesize_pull_request_verdict(state: OverallGraphState) -> Dict[str, Any]:
    all_passed = all(r["passed"] for r in state["consolidated_reviews"])
    verdict = "APPROVED" if all_passed else "REJECTED_SECURITY_FAILURES"
    print(f"[SYNTHESIZER] Aggregated {len(state['consolidated_reviews'])} reviews. Verdict: {verdict}")
    return {"overall_status": verdict}

# Construct dynamic fan-out graph
forking_builder = StateGraph(OverallGraphState)
forking_builder.add_node("review_file_node", analyze_individual_file_node)
forking_builder.add_node("synthesize_verdict", synthesize_pull_request_verdict)
forking_builder.add_conditional_edges(START, dynamic_fork_router, ["review_file_node"])
forking_builder.add_edge("review_file_node", "synthesize_verdict")
forking_builder.add_edge("synthesize_verdict", END)
forking_app = forking_builder.compile()
