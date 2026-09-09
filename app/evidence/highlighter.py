"""Evidence highlighting on the resume PDF.

This is the "transparent highlights" feature from the architecture doc:
for every matched/partial requirement, locate the supporting text in the
original PDF (PyMuPDF `page.search_for`) and add colored highlight
annotations:

  - green  = evidence for a MATCHED requirement
  - orange = evidence for a PARTIALLY matched requirement

The same highlight rectangles are also used to build an HTML evidence
view (safe to embed in Streamlit) and to populate
`EvidenceLocation` (page number + coordinates) on each MatchResult,
which the original pipeline never filled in.

A summary page (candidate, scores, requirement table, color legend) is
appended to the annotated PDF.
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from pathlib import Path

import fitz

from app.schemas.evaluation import CandidateEvaluation, EvidenceLocation

STATUS_COLORS: dict[str, tuple[float, float, float]] = {
    "matched": (0.180, 0.800, 0.251),   # green
    "partial": (1.0, 0.627, 0.0),       # orange
}

# Never highlight needles shorter than this (avoids "C"/"R" noise).
MIN_NEEDLE_LENGTH = 2
# Cap occurrences per needle per page.
MAX_RECTS_PER_NEEDLE = 5
# Long needles are also searched by their first N words.
LONG_NEEDLE_WORDS = 8
# A text span counts as highlighted when this fraction of its area is
# covered by a highlight rectangle.
SPAN_OVERLAP_THRESHOLD = 0.35


@dataclass
class SpanInfo:
    text: str
    status: str | None  # "matched" | "partial" | None


@dataclass
class PageHighlights:
    page_number: int
    lines: list[list[SpanInfo]] = field(default_factory=list)
    highlight_count: int = 0


@dataclass
class HighlightResult:
    pdf_bytes: bytes
    pages: list[PageHighlights] = field(default_factory=list)
    total_highlights: int = 0


# --------------------------------------------------------------------------
# Searching helpers
# --------------------------------------------------------------------------

def _needle_variants(needle: str) -> list[str]:
    """Full text first; for long descriptions also the leading words."""
    variants = [needle]
    words = needle.split()
    if len(words) > LONG_NEEDLE_WORDS:
        variants.append(" ".join(words[:LONG_NEEDLE_WORDS]))
        variants.append(" ".join(words[-LONG_NEEDLE_WORDS:]))
    return variants


def _search_page(page: fitz.Page, needle: str) -> list[fitz.Rect]:
    """All rects for a needle on a page, capped at MAX_RECTS_PER_NEEDLE."""
    for variant in _needle_variants(needle):
        try:
            rects = page.search_for(variant)
        except Exception:
            rects = []
        if rects:
            return rects[:MAX_RECTS_PER_NEEDLE]
    return []


def _rect_area(rect: fitz.Rect) -> float:
    return max(0.0, rect.width) * max(0.0, rect.height)


def _span_status(
    span_bbox: fitz.Rect,
    page_rects: list[tuple[fitz.Rect, str]],
) -> str | None:
    """Status of the strongest highlight covering a text span."""
    span_area = _rect_area(span_bbox)
    if span_area <= 0:
        return None

    status: str | None = None
    best_overlap = 0.0
    for rect, rect_status in page_rects:
        intersection = fitz.Rect(span_bbox) & rect
        overlap = _rect_area(intersection) / span_area
        if overlap >= SPAN_OVERLAP_THRESHOLD:
            if overlap > best_overlap or (
                overlap == best_overlap and rect_status == "matched"
            ):
                best_overlap = overlap
                status = rect_status
    return status


# --------------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------------

def highlight_resume(
    pdf_path: str | Path,
    evaluation: CandidateEvaluation,
) -> HighlightResult:
    """Annotate the resume PDF with evidence highlights.

    Mutates `evaluation` in place by filling EvidenceLocation records
    (page + coordinates) on every evidence item that was located.
    """

    all_matches = (
        evaluation.matched_requirements
        + evaluation.partial_requirements
    )

    # Build the deduplicated needle list (text, status). Deduplication
    # avoids stacking duplicate highlight annotations when several
    # requirements point at the same resume text; evidence locations
    # for EVERY match are back-filled afterwards from the hit map.
    needles: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for match in all_matches:
        candidates = []
        if match.matched_text:
            candidates.append(match.matched_text)
        candidates.extend(ev.text for ev in match.evidence if ev.text)
        # The requirement name itself frequently appears in the resume
        # (exact matches), so it is worth highlighting as well.
        candidates.append(match.requirement)

        for text in candidates:
            text = text.strip()
            if len(text) < MIN_NEEDLE_LENGTH:
                continue
            key = (text.lower(), match.status)
            if key in seen:
                continue
            seen.add(key)
            needles.append((text, match.status))

    doc = fitz.open(pdf_path)
    pages_out: list[PageHighlights] = []
    total_highlights = 0
    # needle key -> list of (page_number, rects)
    needle_hits: dict[tuple[str, str], list[tuple[int, list[fitz.Rect]]]] = {}

    for page_number in range(len(doc)):
        page = doc[page_number]
        page_rects: list[tuple[fitz.Rect, str]] = []

        for needle, status in needles:
            rects = _search_page(page, needle)
            if not rects:
                continue

            color = STATUS_COLORS[status]
            annot = page.add_highlight_annot(rects)
            annot.set_colors(stroke=color)
            annot.update()
            page_rects.extend((rect, status) for rect in rects)
            total_highlights += len(rects)

            key = (needle.lower(), status)
            needle_hits.setdefault(key, []).append((page_number + 1, rects))

        pages_out.append(
            PageHighlights(
                page_number=page_number + 1,
                lines=_extract_lines(page, page_rects),
                highlight_count=len(page_rects),
            )
        )

    # Back-fill evidence locations for every match (not just the first
    # match that triggered the search).
    for match in all_matches:
        _fill_evidence_locations(match, needle_hits)

    _append_summary_page(doc, evaluation)

    pdf_bytes = doc.tobytes(garbage=3, deflate=True)
    doc.close()

    return HighlightResult(
        pdf_bytes=pdf_bytes,
        pages=pages_out,
        total_highlights=total_highlights,
    )


def _fill_evidence_locations(
    match,
    needle_hits: dict[tuple[str, str], list[tuple[int, list[fitz.Rect]]]],
) -> None:
    """Fill page_number + locations on the match's evidence items.

    Looks the evidence text up in the needle hit map (same status first,
    then the opposite status), and records the first page + rects found.
    """
    for evidence in match.evidence:
        target = (evidence.text or "").strip()
        if not target or evidence.page_number is not None:
            continue
        key = (target.lower(), match.status)
        other_status = (
            "partial" if match.status == "matched" else "matched"
        )
        hits = needle_hits.get(key) or needle_hits.get(
            (target.lower(), other_status)
        )
        if not hits:
            continue
        page_number, rects = hits[0]
        evidence.page_number = page_number
        if not evidence.locations:
            evidence.locations = [
                EvidenceLocation(
                    page_number=page_number,
                    x0=round(rect.x0, 2),
                    y0=round(rect.y0, 2),
                    x1=round(rect.x1, 2),
                    y1=round(rect.y1, 2),
                )
                for rect in rects
            ]


def _extract_lines(
    page: fitz.Page,
    page_rects: list[tuple[fitz.Rect, str]],
) -> list[list[SpanInfo]]:
    """Build per-line span info with highlight status for the HTML view."""
    lines: list[list[SpanInfo]] = []
    text_dict = page.get_text("dict")
    for block in text_dict.get("blocks", []):
        for line in block.get("lines", []):
            spans = []
            for span in line.get("spans", []):
                bbox = fitz.Rect(span["bbox"])
                spans.append(
                    SpanInfo(
                        text=span["text"],
                        status=_span_status(bbox, page_rects),
                    )
                )
            if spans:
                lines.append(spans)
    return lines


# --------------------------------------------------------------------------
# Summary page
# --------------------------------------------------------------------------

def _append_summary_page(doc: fitz.Document, evaluation: CandidateEvaluation) -> None:
    """Append a score-summary page with the color legend to the PDF."""

    page = doc.new_page()  # defaults to A4
    width, height = page.rect.width, page.rect.height
    margin = 50.0
    box = fitz.Rect(margin, margin, width - margin, height - margin)

    score = evaluation.score
    lines: list[tuple[str, float, tuple[float, float, float]]] = [
        ("RESUME SCREENING REPORT", 16, (0.1, 0.1, 0.4)),
        ("", 6, (0, 0, 0)),
        (f"Candidate: {evaluation.candidate_name}", 11, (0, 0, 0)),
        (f"Overall score: {score.overall_score:.1f} / 100", 13, (0.0, 0.45, 0.1)),
        (f"Required: {score.required_score:.1f}%   "
         f"Preferred: {score.preferred_score:.1f}%", 10, (0.25, 0.25, 0.25)),
        (f"Experience: {score.experience_score:.1f}%   "
         f"Education: {score.education_score:.1f}%", 10, (0.25, 0.25, 0.25)),
        ("", 8, (0, 0, 0)),
        ("LEGEND: green highlight = matched requirement evidence, "
         "orange = partial match evidence", 9, (0.4, 0.4, 0.4)),
        ("", 10, (0, 0, 0)),
        (f"MATCHED ({len(evaluation.matched_requirements)})", 11, (0.0, 0.45, 0.1)),
    ]
    lines.extend(
        (f"  + {m.requirement}  ({m.match_type}, {m.similarity_score:.2f})", 9, (0.2, 0.2, 0.2))
        for m in evaluation.matched_requirements[:25]
    )
    lines.append((f"PARTIAL ({len(evaluation.partial_requirements)})", 11, (0.8, 0.5, 0.0)))
    lines.extend(
        (f"  ~ {m.requirement}  ({m.similarity_score:.2f})", 9, (0.2, 0.2, 0.2))
        for m in evaluation.partial_requirements[:25]
    )
    lines.append((f"MISSING ({len(evaluation.missing_requirements)})", 11, (0.7, 0.1, 0.1)))
    lines.extend(
        (f"  - {m.requirement}", 9, (0.2, 0.2, 0.2))
        for m in evaluation.missing_requirements[:25]
    )

    cursor = box.y0
    for text, fontsize, color in lines:
        if not text:
            cursor += fontsize
            continue
        # NOTE: insert_textbox returns a negative value (and draws
        # NOTHING) when the rect is too small for one line, so the rect
        # height must comfortably exceed the line height.
        rect = fitz.Rect(box.x0, cursor, box.x1, cursor + fontsize * 2.2)
        page.insert_textbox(
            rect,
            text,
            fontsize=fontsize,
            fontname="helv",
            color=color,
            lineheight=1.25,
        )
        cursor += fontsize * 1.9
        if cursor > box.y1 - 20:
            page.insert_textbox(
                fitz.Rect(box.x0, box.y1 - 15, box.x1, box.y1),
                "... (truncated)",
                fontsize=8,
                fontname="helv",
                color=(0.5, 0.5, 0.5),
            )
            break


# --------------------------------------------------------------------------
# HTML evidence view (embeddable in Streamlit)
# --------------------------------------------------------------------------

def build_html_evidence_view(result: HighlightResult) -> str:
    """Render highlighted pages as HTML with colored <mark> tags."""

    parts = [
        "<style>"
        ".ev-pages{max-height:640px;overflow-y:auto;border:1px solid #e0e0e0;"
        "border-radius:8px;background:#fafafa;padding:4px;}"
        ".ev-page{background:#fff;border:1px solid #ddd;border-radius:6px;"
        "margin:10px;padding:14px 18px;font-family:Georgia,serif;"
        "font-size:13px;line-height:1.55;white-space:pre-wrap;"
        "word-wrap:break-word;box-shadow:0 1px 3px rgba(0,0,0,0.06);}"
        ".ev-page-header{font-family:sans-serif;font-size:11px;color:#888;"
        "letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;}"
        "mark.matched{background:#b7f0c0;padding:0 2px;border-radius:3px;}"
        "mark.partial{background:#ffd9a0;padding:0 2px;border-radius:3px;}"
        "</style>",
        '<div class="ev-pages">',
    ]

    for page in result.pages:
        if not page.highlight_count and not page.lines:
            continue
        header = (
            f'Page {page.page_number}'
            + (
                f' &middot; {page.highlight_count} highlight(s)'
                if page.highlight_count
                else ''
            )
        )
        parts.append(
            f'<div class="ev-page"><div class="ev-page-header">{header}</div>'
        )

        for line in page.lines:
            rendered = "".join(
                f'<mark class="{span.status}">{html.escape(span.text)}</mark>'
                if span.status
                else html.escape(span.text)
                for span in line
            )
            parts.append(rendered + "\n")

        parts.append("</div>")

    parts.append("</div>")
    return "".join(parts)
