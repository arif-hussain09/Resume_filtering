"""Streamlit UI for the AI Resume Filter.

Run from the project root:

    streamlit run app/ui/streamlit_app.py

Features:
  - upload one job-description PDF + many resume PDFs
  - batch analysis with live progress
  - candidate ranking table
  - per-candidate score breakdown, matched/partial/missing evidence
  - highlighted-resume evidence view + annotated PDF download
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from app import config  # noqa: E402
from app.pipeline import CandidateResult, run_pipeline  # noqa: E402
from app.schemas.jobs import JobProfile  # noqa: E402

st.set_page_config(
    page_title="AI Resume Filter",
    page_icon="🤖",
    layout="wide",
)

# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------

if "results" not in st.session_state:
    st.session_state.results = None

SAMPLE_JOB = ROOT / "data" / "jobs" / "sample_job.pdf"
SAMPLE_RESUME = ROOT / "data" / "resumes" / "sample_resume.pdf"


# --------------------------------------------------------------------------
# Cached heavy work
# --------------------------------------------------------------------------

@st.cache_resource(show_spinner="Loading embedding model…")
def _embedding_model_info() -> str:
    """Touch the embedding model once so the first match is not slow."""
    from app.matching.semantic import get_embedding_model

    model = get_embedding_model()
    dimension = getattr(
        model, "get_embedding_dimension", None
    ) or model.get_sentence_embedding_dimension
    return f"{config.get_embedding_model_name()} ({dimension()}d)"


@st.cache_data(show_spinner="Extracting job requirements…", ttl=600)
def _extract_job_cached(job_text: str, model: str) -> dict:
    """JobProfile extraction, cached on (text, model)."""
    from app.extraction.job_extractor import extract_job_profile

    profile = extract_job_profile(job_text)
    return profile.model_dump()


def _load_pdf_text(file_bytes: bytes) -> str:
    import fitz

    with fitz.open(stream=file_bytes, filetype="pdf") as document:
        return "\n".join(page.get_text("text") for page in document)


def _save_temp_upload(uploaded_file) -> Path:
    """Persist an upload to a temp file so the pipeline can re-open it."""
    tmp_dir = ROOT / "data" / "uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    safe = uploaded_file.name.replace("/", "_").replace("\\", "_")
    path = tmp_dir / f"{int(time.time() * 1000)}_{safe}"
    path.write_bytes(uploaded_file.getbuffer())
    return path


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------

with st.sidebar:
    st.header("⚙️ Settings")

    api_key = st.text_input(
        "Groq API key",
        value="*********",
        type="password",
        help="Get a free key at console.groq.com. Stored only in this session.",
    )
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key

    model_name = st.selectbox(
        "Extraction model",
        [
            "openai/gpt-oss-120b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
        ],
        index=0,
    )
    if model_name != config.get_groq_model():
        os.environ["GROQ_MODEL"] = model_name

    st.divider()
    st.caption("Embedding model: " + _embedding_model_info())
    st.caption(
        "Upload PDFs with a text layer. Scanned/image-only PDFs are not "
        "supported yet (OCR roadmap)."
    )

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------

st.title("🤖 AI Resume Filter")
st.caption(
    "Upload a job description and resumes. Each resume is parsed by an LLM, "
    "matched against the job's requirements (exact + fuzzy + semantic), "
    "scored 0–100, and the supporting evidence is highlighted in the PDF."
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Job description")
    use_sample = st.checkbox(
        "Use the bundled sample job description",
        value=True,
        help=f"Loads {SAMPLE_JOB.name}",
    )
    job_upload = None if use_sample else st.file_uploader(
        "Job description PDF", type=["pdf"]
    )

with col2:
    st.subheader("👥 Resumes")
    resumes_upload = st.file_uploader(
        "Resume PDFs (batch upload supported)",
        type=["pdf"],
        accept_multiple_files=True,
    )

# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------

analyze_clicked = st.button(
    "🔍 Analyze",
    type="primary",
    disabled=not (use_sample or job_upload) or not resumes_upload,
    use_container_width=True,
)

if analyze_clicked:
    if not config.get_groq_api_key():
        st.error(
            "A Groq API key is required for LLM extraction. Enter it in "
            "the sidebar (free at console.groq.com)."
        )
        st.stop()

    # Resolve job PDF
    if use_sample:
        job_path = SAMPLE_JOB
        job_bytes = job_path.read_bytes()
    else:
        assert job_upload is not None
        job_bytes = job_upload.getbuffer()
        job_path = _save_temp_upload(job_upload)

    job_text = _load_pdf_text(bytes(job_bytes))
    if not job_text.strip():
        st.error("The job-description PDF has no extractable text layer.")
        st.stop()

    # Job profile extraction (cached)
    with st.status("Extracting job requirements…", expanded=True) as status:
        st.write("Parsing PDF text…")
        try:
            job_profile_dict = _extract_job_cached(
                job_text, config.get_groq_model()
            )
            job_profile = JobProfile.model_validate(job_profile_dict)
        except Exception as exc:
            st.error(f"Job extraction failed: {exc}")
            st.stop()
        st.write(
            f"Found {len(job_profile.requirements)} requirements "
            f"for “{job_profile.title}”."
        )
        status.update(
            label=f"Job profile ready: {job_profile.title}", state="complete"
        )

    # Persist uploads
    resume_paths = [_save_temp_upload(f) for f in resumes_upload]

    progress_bar = st.progress(0.0, text="Starting…")
    results: list[CandidateResult] = []

    for index, resume_path in enumerate(resume_paths):
        def _progress(stage: str, fraction: float) -> None:
            overall = (index + fraction) / len(resume_paths)
            progress_bar.progress(
                min(overall, 1.0),
                text=f"({index + 1}/{len(resume_paths)}) {stage}",
            )

        results.append(
            run_pipeline(
                job_pdf=job_path,
                resume_pdf=resume_path,
                job_profile=job_profile,
                progress=_progress,
            )
        )

    progress_bar.progress(1.0, text="Done")
    st.session_state.results = results

# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------

results: list[CandidateResult] | None = st.session_state.results

if results:
    st.divider()
    st.header("🏆 Ranking")

    ok = [r for r in results if r.evaluation]
    failed = [r for r in results if r.error]

    ranking = sorted(
        ok, key=lambda r: r.evaluation.score.overall_score, reverse=True
    )

    if ranking:
        table_data = [
            {
                "candidate": r.candidate_name,
                "overall": r.evaluation.score.overall_score,
                "required %": r.evaluation.score.required_score,
                "preferred %": r.evaluation.score.preferred_score,
                "experience %": r.evaluation.score.experience_score,
                "education %": r.evaluation.score.education_score,
                "matched": len(r.evaluation.matched_requirements),
                "partial": len(r.evaluation.partial_requirements),
                "missing": len(r.evaluation.missing_requirements),
            }
            for r in ranking
        ]
        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "overall": st.column_config.ProgressColumn(
                    "Overall score",
                    min_value=0,
                    max_value=100,
                    format="%.1f",
                ),
            },
        )

    for r in failed:
        st.warning(f"⚠️ {Path(r.resume_path).name} failed: {r.error}")

    if ranking:
        st.divider()
        st.header("👤 Candidate details")

        selected_name = st.selectbox(
            "Candidate", [r.candidate_name for r in ranking]
        )
        selected = next(
            r for r in ranking if r.candidate_name == selected_name
        )
        evaluation = selected.evaluation
        score = evaluation.score

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Overall", f"{score.overall_score:.1f}")
        m2.metric("Required", f"{score.required_score:.0f}%")
        m3.metric("Preferred", f"{score.preferred_score:.0f}%")
        m4.metric("Experience", f"{score.experience_score:.0f}%")
        m5.metric("Education", f"{score.education_score:.0f}%")

        with st.expander(
            f"📋 Requirement breakdown "
            f"({len(evaluation.matched_requirements)} matched / "
            f"{len(evaluation.partial_requirements)} partial / "
            f"{len(evaluation.missing_requirements)} missing)",
            expanded=True,
        ):
            def _row(match, status_label: str) -> dict:
                return {
                    "requirement": match.requirement,
                    "importance": match.requirement_importance,
                    "status": status_label,
                    "match type": match.match_type,
                    "similarity": round(match.similarity_score, 2),
                    "contribution": round(match.score_contribution, 2),
                    "evidence (in resume)": (
                        match.evidence[0].text
                        if match.evidence
                        else (match.matched_text or "")
                    ),
                    "page": match.evidence[0].page_number if match.evidence else "",
                }

            _rows = (
                [
                    _row(m, "🟢 matched")
                    for m in evaluation.matched_requirements
                ]
                + [
                    _row(m, "🟠 partial")
                    for m in evaluation.partial_requirements
                ]
                + [
                    {
                        "requirement": m.requirement,
                        "importance": m.requirement_importance,
                        "status": "🔴 missing",
                        "match type": "none",
                        "similarity": 0.0,
                        "contribution": 0.0,
                        "evidence (in resume)": "",
                        "page": "",
                    }
                    for m in evaluation.missing_requirements
                ]
            )
            st.dataframe(_rows, use_container_width=True, hide_index=True)

        if evaluation.recommendations:
            with st.expander("💡 Recommendations"):
                for rec in evaluation.recommendations:
                    st.markdown(f"**{rec.area}** — {rec.suggestion}")

        tab1, tab2 = st.tabs(["🖍️ Highlighted evidence", "⬇️ Downloads"])

        with tab1:
            if selected.html_evidence:
                st.markdown(selected.html_evidence, unsafe_allow_html=True)
            else:
                st.info("No highlights available for this resume.")

        with tab2:
            if selected.highlight and selected.highlight.pdf_bytes:
                st.download_button(
                    "⬇️ Download annotated PDF (highlights + summary page)",
                    data=selected.highlight.pdf_bytes,
                    file_name=f"{selected.candidate_name}_annotated.pdf",
                    mime="application/pdf",
                )
            if evaluation:
                import json

                report = json.dumps(evaluation.model_dump(), indent=2)
                st.download_button(
                    "⬇️ Download JSON report",
                    data=report,
                    file_name=f"{selected.candidate_name}_report.json",
                    mime="application/json",
                )

else:
    st.info(
        "Upload a job description (or tick the sample) plus one or more "
        "resumes, then press **Analyze**."
    )
