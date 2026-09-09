"""Requirement -> resume matching.

Fixes vs. the original implementation:

1. `collect_resume_evidence` is now called ONCE per resume, not once per
   requirement (O(N) -> O(1) rebuilds).
2. Fuzzy and semantic scores no longer compete on a single raw `best_score`
   scale (lexical ratio and cosine similarity are not comparable). Each
   strategy is evaluated on its own; the best *qualified* result wins by
   priority: exact > fuzzy > semantic.
3. Missing requirements no longer carry a stale `matched_text`.
4. Each MatchResult now carries `evidence` (the actual resume strings that
   support the match) so the UI/highlighter can show WHERE the score
   came from.
5. A canonical alias map (SQL<->MySQL, K8s<->Kubernetes, ...) resolves
   the most common naming mismatches as exact matches.
"""

from __future__ import annotations

from rapidfuzz.fuzz import ratio

from app import config
from app.evidence.evidence_finder import collect_resume_evidence
from app.matching.aliases import canonicalize
from app.matching.semantic import similarity_matrix
from app.schemas.evaluation import Evidence, MatchResult
from app.schemas.jobs import JobProfile
from app.schemas.resume import ResumeProfile

FUZZY_THRESHOLD = config.get_fuzzy_threshold()
FUZZY_PARTIAL_THRESHOLD = config.get_fuzzy_partial_threshold()
SEMANTIC_MATCH_THRESHOLD = config.get_semantic_match_threshold()
SEMANTIC_PARTIAL_THRESHOLD = config.get_semantic_partial_threshold()

# How many supporting evidence snippets to attach per requirement.
MAX_EVIDENCE_SNIPPETS = 3
# Extra evidence items with semantic similarity >= this value are attached
# as supporting context even if they are not the winning match.
SUPPORTING_EVIDENCE_THRESHOLD = 0.50


def normalize_text(text: str) -> str:
    return " ".join((text or "").lower().strip().split())


def fuzzy_similarity(text1: str, text2: str) -> float:
    return ratio(normalize_text(text1), normalize_text(text2)) / 100.0


def find_best_resume_skill(
    requirement: str,
    resume_evidence: list[str],
    semantic_scores: list[float],
) -> tuple[str | None, str, float, list[int]]:
    """Find the best match for one requirement.

    Returns (matched_text, match_type, score, supporting_indices) where
    supporting_indices lists evidence positions that back the decision.

    Strategy priority: exact (canonical) > fuzzy >= FUZZY_THRESHOLD >
    semantic >= SEMANTIC_MATCH_THRESHOLD. Below the match thresholds,
    fuzzy >= FUZZY_PARTIAL_THRESHOLD or semantic >= SEMANTIC_PARTIAL_
    THRESHOLD counts as "partial".
    """
    best_skill: str | None = None
    best_match_type = "none"
    best_score = 0.0
    matched_index: int | None = None

    # 1. Exact match on the canonical form (handles aliases + casing).
    canonical_requirement = canonicalize(requirement)
    for index, item in enumerate(resume_evidence):
        if canonicalize(item) == canonical_requirement:
            return item, "exact", 1.0, [index]

    # 2. Fuzzy (lexical) pass -- cheap, run over all evidence.
    for index, item in enumerate(resume_evidence):
        fuzzy_score = fuzzy_similarity(requirement, item)
        if fuzzy_score >= FUZZY_THRESHOLD and fuzzy_score > best_score:
            best_skill, best_match_type, best_score = item, "fuzzy", fuzzy_score
            matched_index = index

    # 3. Semantic pass -- uses precomputed similarity scores.
    for index, semantic_score in enumerate(semantic_scores):
        if semantic_score >= SEMANTIC_MATCH_THRESHOLD and semantic_score > best_score:
            best_skill, best_match_type, best_score = (
                resume_evidence[index],
                "semantic",
                semantic_score,
            )
            matched_index = index

    # 4. Partial tier (only if nothing fully matched yet).
    if best_match_type == "none":
        partial_fuzzy_best = 0.0
        partial_fuzzy_index: int | None = None
        for index, item in enumerate(resume_evidence):
            fuzzy_score = fuzzy_similarity(requirement, item)
            if (
                fuzzy_score >= FUZZY_PARTIAL_THRESHOLD
                and fuzzy_score > partial_fuzzy_best
            ):
                partial_fuzzy_best, partial_fuzzy_index = fuzzy_score, index
        if partial_fuzzy_index is not None:
            best_skill = resume_evidence[partial_fuzzy_index]
            best_match_type, best_score = "fuzzy", partial_fuzzy_best
            matched_index = partial_fuzzy_index

        for index, semantic_score in enumerate(semantic_scores):
            if (
                semantic_score >= SEMANTIC_PARTIAL_THRESHOLD
                and semantic_score > best_score
            ):
                best_skill = (
                    resume_evidence[index]
                )
                best_match_type, best_score = "semantic", semantic_score
                matched_index = index

    supporting: list[int] = []
    if matched_index is not None:
        supporting.append(matched_index)
        for index, semantic_score in enumerate(semantic_scores):
            if index == matched_index:
                continue
            if semantic_score >= SUPPORTING_EVIDENCE_THRESHOLD and index not in supporting:
                supporting.append(index)

    return best_skill, best_match_type, best_score, supporting


def match_requirements(
    job: JobProfile,
    resume: ResumeProfile,
) -> list[MatchResult]:
    """Match every job requirement against the resume's evidence pool."""

    # Built ONCE per resume (was previously re-built per requirement).
    evidence_pool = collect_resume_evidence(resume)

    requirements = [requirement.name for requirement in job.requirements]

    # Semantic scores for every (requirement, evidence) pair, computed in
    # ONE batched embedding pass instead of pairwise encode() calls.
    if evidence_pool and requirements:
        sim_matrix = similarity_matrix(requirements, evidence_pool)
    else:
        sim_matrix = None

    results: list[MatchResult] = []

    for requirement_index, requirement in enumerate(job.requirements):

        semantic_scores = (
            list(sim_matrix[requirement_index])
            if sim_matrix is not None
            else []
        )

        matched_text, match_type, score, supporting = find_best_resume_skill(
            requirement.name,
            evidence_pool,
            semantic_scores,
        )

        if match_type == "exact":
            status = "matched"
        elif match_type in ("fuzzy", "semantic"):
            if match_type == "fuzzy":
                status = (
                    "matched" if score >= FUZZY_THRESHOLD else "partial"
                )
            else:
                status = (
                    "matched"
                    if score >= SEMANTIC_MATCH_THRESHOLD
                    else "partial"
                )
        else:
            status = "missing"

        if status == "missing":
            # Keep missing requirements truly empty -- a stale
            # matched_text here would poison the UI ("Missing: SQL,
            # evidence: MySQL").
            match_type = "none"
            score = 0.0
            matched_text = None
            evidence_items: list[Evidence] = []
        else:
            evidence_items = [
                Evidence(
                    text=evidence_pool[index],
                    relevance_score=(
                        float(semantic_scores[index]) if semantic_scores else 0.0
                    ),
                )
                for index in supporting[:MAX_EVIDENCE_SNIPPETS]
                if index < len(evidence_pool)
            ]

        results.append(
            MatchResult(
                requirement=requirement.name,
                requirement_importance=requirement.importance,
                status=status,
                match_type=match_type,
                similarity_score=round(score, 4),
                matched_text=matched_text,
                evidence=evidence_items,
            )
        )

    return results
