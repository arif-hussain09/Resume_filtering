from app.extraction.job_extractor import extract_job_profile
from app.extraction.resume_extractor import extract_resume_profile
from app.ingestion.pdf_parser import extract_pdf_pages
from app.matching.matcher import match_requirements
from app.scoring.scorer import build_evaluation
from app.graphs.state import PipelineState


def parse_job(state: PipelineState) -> dict:
    pages = extract_pdf_pages(state["job_pdf"])
    return {"job_text": "\n".join(p["text"] for p in pages)}


def extract_job(state: PipelineState) -> dict:
    return {"job_profile": extract_job_profile(state["job_text"])}


def parse_resume(state: PipelineState) -> dict:
    pages = extract_pdf_pages(state["resume_pdf"])
    return {"resume_text": "\n".join(p["text"] for p in pages)}


def extract_resume(state: PipelineState) -> dict:
    return {"resume_profile": extract_resume_profile(state["resume_text"])}


def match(state: PipelineState) -> dict:
    return {
        "match_results": match_requirements(
            state["job_profile"],
            state["resume_profile"],
        )
    }


def score(state: PipelineState) -> dict:
    # ← call YOUR scoring function here; adjust to its real signature
    evaluation = build_evaluation(
        state["job_profile"],
        state["resume_profile"],
        state["match_results"],
    )
    return {"evaluation": evaluation}