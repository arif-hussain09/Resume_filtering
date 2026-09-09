"""CLI entry point.

Examples:

    python main.py --job data/jobs/sample_job.pdf \
                   --resumes data/resumes/sample_resume.pdf

    python main.py --job data/jobs/sample_job.pdf \
                   --resumes data/resumes/*.pdf \
                   --out data/outputs

Requires GROQ_API_KEY in the environment or a .env file.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()  # Load .env file if present

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app import config  # noqa: E402
from app.pipeline import run_batch  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AI resume filtering: score resumes against a job description."
    )
    parser.add_argument("--job", required=True, help="Path to the job-description PDF")
    parser.add_argument(
        "--resumes", required=True, nargs="+", help="Paths to resume PDFs"
    )
    parser.add_argument(
        "--out", default=str(ROOT / "data" / "outputs"), help="Output directory"
    )
    parser.add_argument(
        "--no-highlight", action="store_true", help="Skip PDF highlighting"
    )
    args = parser.parse_args()

    if not GROQ_API_KEY:
        print(
            "ERROR: GROQ_API_KEY is not set. Copy .env.example to .env "
            "and add your key (free at console.groq.com).",
            file=sys.stderr,
        )
        return 2

    resume_paths = [
        Path(pattern) for pattern in args.resumes
    ]

    def progress(stage: str, fraction: float) -> None:
        print(f"  [{fraction:5.1%}] {stage}")

    print(f"Job: {args.job}")
    print(f"Resumes: {len(resume_paths)}")
    results = run_batch(
        job_pdf=Path(args.job),
        resume_pdfs=resume_paths,
        progress=progress,
    )

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n===== RANKING =====")
    ranked = sorted(
        (r for r in results if r.evaluation),
        key=lambda r: r.evaluation.score.overall_score,
        reverse=True,
    )
    for position, result in enumerate(ranked, start=1):
        score = result.evaluation.score
        print(
            f"{position:2d}. {result.candidate_name:<30} "
            f"overall={score.overall_score:6.1f}  "
            f"(req {score.required_score:.0f}% | pref {score.preferred_score:.0f}% | "
            f"exp {score.experience_score:.0f}% | edu {score.education_score:.0f}%)"
        )

    for result in results:
        if result.error:
            print(f" !! {result.candidate_name}: {result.error}")
            continue

        stem = result.candidate_name.replace(" ", "_") or "candidate"
        report_path = out_dir / f"{stem}_report.json"
        report_path.write_text(
            json.dumps(result.evaluation.model_dump(), indent=2)
        )
        if result.highlight and result.highlight.pdf_bytes and not args.no_highlight:
            pdf_path = out_dir / f"{stem}_annotated.pdf"
            pdf_path.write_bytes(result.highlight.pdf_bytes)

    print(f"\nReports written to {out_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
