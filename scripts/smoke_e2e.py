"""End-to-end smoke test with REAL embeddings + REAL sample PDFs.

LLM profiles are hand-injected (matching the actual PDF contents) because
this sandbox has no GROQ_API_KEY. Everything else -- parsing, matching,
scoring, highlighting, report generation -- runs for real.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.pipeline import run_pipeline  # noqa: E402
from app.schemas.jobs import ExperienceRequirement, JobProfile, Requirement  # noqa: E402
from app.schemas.resume import (  # noqa: E402
    Education,
    Experience,
    Project,
    ResumeProfile,
)

OUT = ROOT.parent / "download" / "resume_filter_demo"
OUT.mkdir(parents=True, exist_ok=True)
# --- JobProfile: mirrors data/jobs/sample_job.pdf (AI Engineering Intern) ---
job = JobProfile(
    title="AI Engineering Intern (Campus Hiring 2026 - Generative AI)",
    requirements=[
        Requirement(name="Python", category="skill", importance="required"),
        Requirement(name="PyTorch", category="framework", importance="required"),
        Requirement(name="Machine Learning", category="skill", importance="required"),
        Requirement(name="Statistics", category="domain", importance="required"),
        Requirement(name="LLMs", category="domain", importance="required"),
        Requirement(name="RAG", category="domain", importance="required"),
        Requirement(name="Prompt Engineering", category="skill", importance="required"),
        Requirement(name="Vector Databases", category="tool", importance="required"),
        Requirement(name="LangChain", category="framework", importance="required"),
        Requirement(name="TensorFlow", category="framework", importance="preferred"),
        Requirement(name="FastAPI", category="framework", importance="preferred"),
        Requirement(name="Hugging Face", category="tool", importance="preferred"),
        Requirement(name="Pydantic AI", category="framework", importance="preferred"),
    ],
    experience_requirements=[
        ExperienceRequirement(
            description="Academic or project exposure to LLMs, RAG or fine-tuning",
            minimum_years=0.5,
        ),
    ],
    education_requirements=[
        "B.Tech degree",
    ],
    responsibilities=[
        "Support the development and deployment of Generative AI solutions, including RAG pipelines and vector databases",
        "Assist in integrating frameworks like LangChain and improving context-aware AI workflows",
        "Monitor and evaluate model performance, quality, bias and reliability",
    ],
    domain_context=[
        "Generative AI at the center of how India buys, insures and finances vehicles",
    ],
)

# --- ResumeProfile: mirrors data/resumes/sample_resume.pdf (Arif Hussain) ---
resume = ResumeProfile(
    name="Arif Hussain",
    skills=[
        "Python",
        "C",
        "ANN",
        "RNN",
        "CNN",
        "Transformer Architectures",
        "Statistical Modeling",
        "Data Analysis",
        "Diffusion Models",
        "Vision Transformers (ViTs)",
        "LangChain",
        "LangGraph",
        "OpenCV",
        "MediaPipe",
        "VS Code",
        "Google Colab",
        "Jupyter Notebook",
    ],
    experience=[
        Experience(
            company="Meity",
            role="Research Intern",
            duration_years=0.2,
            description=(
                "Worked on a hybrid AI-based Intrusion Detection System (IDS) "
                "integrating supervised learning for known attack detection and "
                "unsupervised learning for zero-day anomaly detection."
            ),
        ),
        Experience(
            company="Delhi Technological University",
            role="President, MCE Students Community",
            duration_years=1.7,
            description=(
                "Elected President of the MCE Students Community, leading "
                "departmental initiatives and student engagement."
            ),
        ),
    ],
    education=[
        Education(
            degree="BTech in Mathematics and Computer Science",
            institution="Delhi Technological University",
            field="Mathematics and Computer Science",
        ),
    ],
    projects=[
        Project(
            name="ML/Applied-Math Approaches to Early Detection of Zero-Day IoT Botnet Propagation",
            description=(
                "Built a cross-dataset IoT botnet detection framework, training on "
                "CICIoT2023 and testing zero-day generalization on MedBIoT. Applied "
                "feature selection and Optuna-based hyperparameter tuning across "
                "multiple ML models."
            ),
            technologies=["Optuna", "CUSUM", "EWMA", "scikit-learn"],
        ),
        Project(
            name="Movie Recommendation System",
            description="Developed a Movie Recommendation System using machine learning techniques.",
            technologies=["Python"],
        ),
        Project(
            name="Hand-Gesture Volume Controller",
            description=(
                "Implemented object detection and a hand-gesture-based volume "
                "controller using computer vision."
            ),
            technologies=["OpenCV", "MediaPipe"],
        ),
    ],
    certifications=[],
    achievements=[
        "Served as NEP SAARTHI, a student ambassador for academic reforms",
    ],
)

if __name__ == "__main__":
    print("Running pipeline with REAL embeddings on the sample PDFs...\n")

    result = run_pipeline(
        job_pdf=ROOT / "data" / "jobs" / "sample_job.pdf",
        resume_pdf=ROOT / "data" / "resumes" / "sample_resume.pdf",
        job_profile=job,
        resume_profile=resume,
    )

    if result.error:
        print(f"FAILED: {result.error}")
        sys.exit(1)

    ev = result.evaluation
    print(f"Candidate     : {ev.candidate_name}")
    print(f"Overall score : {ev.score.overall_score}")
    print(f"Breakdown     : required {ev.score.required_score}% | "
          f"preferred {ev.score.preferred_score}% | "
          f"experience {ev.score.experience_score}% | "
          f"education {ev.score.education_score}%")
    print(f"Weights used  : {ev.score.weights_used}")
    print(f"Timings       : { {k: round(v, 3) for k, v in result.timings.items()} }")

    print(f"\nMATCHED ({len(ev.matched_requirements)}):")
    for m in ev.matched_requirements:
        pages = [e.page_number for e in m.evidence if e.page_number]
        print(f"  + {m.requirement:<24} {m.match_type:<8} "
              f"{m.similarity_score:.2f}  contrib={m.score_contribution:<5} pages={pages}")

    print(f"\nPARTIAL ({len(ev.partial_requirements)}):")
    for m in ev.partial_requirements:
        pages = [e.page_number for e in m.evidence if e.page_number]
        print(f"  ~ {m.requirement:<24} {m.match_type:<8} "
              f"{m.similarity_score:.2f}  contrib={m.score_contribution:<5} pages={pages}")

    print(f"\nMISSING ({len(ev.missing_requirements)}):")
    for m in ev.missing_requirements:
        print(f"  - {m.requirement}")

    print("\nRecommendations:")
    for r in ev.recommendations:
        print(f"  * [{r.area}] {r.suggestion[:90]}")

    # Save artifacts
    (OUT / "arif_annotated.pdf").write_bytes(result.highlight.pdf_bytes)
    (OUT / "arif_report.json").write_text(
        ev.model_dump_json(indent=2)
    )
    (OUT / "arif_evidence_view.html").write_text(result.html_evidence)

    print(f"\nArtifacts written to {OUT}:")
    for f in sorted(OUT.iterdir()):
        print(f"  {f.name} ({f.stat().st_size:,} bytes)")
