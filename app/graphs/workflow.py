from langgraph.graph import END, START, StateGraph

from app.graphs.nodes import (
    extract_job,
    extract_resume,
    match,
    parse_job,
    parse_resume,
    score,
)
from app.graphs.state import PipelineState


def build_workflow():
    builder = StateGraph(PipelineState)

    builder.add_node("parse_job", parse_job)
    builder.add_node("extract_job", extract_job)
    builder.add_node("parse_resume", parse_resume)
    builder.add_node("extract_resume", extract_resume)
    builder.add_node("match", match)
    builder.add_node("score", score)

    builder.add_edge(START, "parse_job")
    builder.add_edge("parse_job", "extract_job")
    builder.add_edge("extract_job", "parse_resume")
    builder.add_edge("parse_resume", "extract_resume")
    builder.add_edge("extract_resume", "match")
    builder.add_edge("match", "score")
    builder.add_edge("score", END)

    return builder.compile()


workflow = build_workflow()