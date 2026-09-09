# AI Resume Filter

Score resumes against a job description and **see the evidence** for every
point awarded — matched skills are highlighted directly in the resume PDF.

```
Job PDF ──► LLM extraction (JobProfile)
Resume PDF ─► LLM extraction (ResumeProfile) ─► exact / fuzzy / semantic matching
                                             ─► scoring 0–100 + per-requirement contributions
                                             ─► evidence highlighting in the PDF
                                             ─► ranking + recommendations
```

## Features

- **Batch upload**: one job description + many resumes, ranked in a table.
- **Multi-strategy matching**: canonical aliases (SQL↔MySQL, K8s↔Kubernetes),
  fuzzy (RapidFuzz), and batched semantic embeddings (all-MiniLM-L6-v2).
- **Explainable scoring**: honest 0–100 category percentages, dynamic
  weights (categories the job doesn't test are dropped, not given free
  marks), and a per-requirement `score_contribution`.
- **Evidence highlighting**: green = matched requirement evidence,
  orange = partial. Rendered into an annotated PDF (plus a summary page)
  and as an in-app HTML view. Every evidence item carries page number and
  coordinates.
- **Per-candidate isolation**: one broken upload fails alone, never the batch.
- **CLI + Streamlit UI**.

## Quickstart

```bash
# 1. Install (uv or pip)
uv sync                 # or: pip install -r requirements.txt

# 2. Configure
cp .env.example .env    # then add your free GROQ_API_KEY (console.groq.com)

# 3. Run the UI
streamlit run app/ui/streamlit_app.py

# Or the CLI
python main.py --job data/jobs/sample_job.pdf --resumes data/resumes/*.pdf
```

First run downloads the embedding model (~90 MB). Analysis needs PDFs with
a text layer — scanned/image-only PDFs are rejected with a clear error
(OCR is on the roadmap).

## Tests

```bash
pytest            # 31 tests; LLM tests auto-skip without GROQ_API_KEY
```

Test strategy: matching/scoring/highlighting logic is tested against
deterministic embedding stubs (no network, no API key). Live LLM tests run
only when `GROQ_API_KEY` is set. An end-to-end demo with injected profiles
is in `scripts/smoke_e2e.py`.

## Project structure

```
app/
  config.py            env/threshold configuration (single source of truth)
  pipeline.py          end-to-end orchestrator (parse → extract → match → score → highlight)
  ingestion/           PDF text extraction (PyMuPDF, page-aware)
  extraction/          Groq LLM → JobProfile / ResumeProfile (with retries)
  schemas/             Pydantic models (jobs, resume, evaluation, evidence locations)
  matching/            aliases, fuzzy, batched semantic embeddings
  scoring/             scorer (dynamic weights), experience, education (degree levels)
  evidence/            evidence pool + PDF highlighter + HTML evidence view
  services/            evaluation service + rule-based recommendations
  ui/                  Streamlit app
main.py                CLI
scripts/               smoke_e2e.py — end-to-end demo
data/                  sample job + resume
```

## Design notes

- **No LangGraph**: the original LangGraph pipeline was strictly linear
  and crashed at import (`build_evaluation` never existed). A plain
  function chain with a progress callback does the same job with less
  machinery; `app/pipeline.py` documents this.
- **Batched embeddings**: evidence and requirements are embedded once per
  resume, then compared with one matrix multiply — the pairwise
  `encode()`-per-call version was 1000+ model round-trips.
- **Honest scoring**: `ScoreBreakdown` fields are true percentages;
  overall = weighted mean over the categories the job actually tests.

## Roadmap

- OCR fallback for scanned PDFs (EasyOCR)
- DOCX resume support
- "Extras" detection (relevant resume content beyond requirements)
- HR vs applicant views

## Tuning

All thresholds are env-overridable (see `.env.example`):
`FUZZY_THRESHOLD` (0.85), `FUZZY_PARTIAL_THRESHOLD` (0.70),
`SEMANTIC_MATCH_THRESHOLD` (0.75), `SEMANTIC_PARTIAL_THRESHOLD` (0.55).
