import os
from typing import TypedDict

import requests
from langgraph.graph import END, START, StateGraph


class InvestigationState(TypedDict, total=False):
    case: dict
    evidence: list[dict]
    summary: str


def triage(state: InvestigationState) -> InvestigationState:
    case = state["case"]
    return {
        "evidence": [
            {"source": "case_record", "detail": f"Event: {case['event_json']}"},
            {"source": "model_output", "detail": f"Risk score: {case['score']:.3f}"},
        ]
    }


def report(state: InvestigationState) -> InvestigationState:
    case = state["case"]
    evidence = state["evidence"]
    deterministic = (
        f"Case {case['id']}: model score {case['score']:.3f}. "
        "This is a preliminary automated finding, not a confirmed incident. "
        "An analyst must review evidence and decide disposition."
    )
    if os.getenv("USE_OLLAMA") == "1":
        prompt = (
            "Write a cautious security case summary based ONLY on the evidence below. "
            "Do not claim the event is malicious without proof. No remediation instructions.\n"
            + repr(evidence)
        )
        try:
            response = requests.post(
                os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate"),
                json={
                    "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=45,
            )
            response.raise_for_status()
            narrative = response.json().get("response", "").strip()
            if narrative:
                deterministic += "\nUnverified LLM narrative (review required): " + narrative[:2000]
        except (requests.RequestException, ValueError) as exc:
            deterministic += (
                f"\nLLM unavailable ({type(exc).__name__}); deterministic summary used."
            )
    return {"summary": deterministic}


builder = StateGraph(InvestigationState)
builder.add_node("triage", triage)
builder.add_node("report", report)
builder.add_edge(START, "triage")
builder.add_edge("triage", "report")
builder.add_edge("report", END)
graph = builder.compile()


def investigate(case: dict) -> dict:
    return graph.invoke({"case": case})
