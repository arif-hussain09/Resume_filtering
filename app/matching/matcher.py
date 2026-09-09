# 
## -----------------Update the import statement in matcher.py-----------------
from rapidfuzz.fuzz import ratio

from app.schemas.evaluation import MatchResult
from app.schemas.jobs import JobProfile
from app.schemas.resume import ResumeProfile
from app.matching.semantic import semantic_similarity
from app.evidence.evidence_finder import collect_resume_evidence


FUZZY_THRESHOLD = 0.85
SEMANTIC_MATCH_THRESHOLD = 0.75
SEMANTIC_PARTIAL_THRESHOLD = 0.55


def normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def fuzzy_similarity(text1: str, text2: str) -> float:
    return ratio(
        normalize_text(text1),
        normalize_text(text2),
    ) / 100.0


def find_best_resume_skill(
    requirement: str,
    resume_skills: list[str],
) -> tuple[str | None, str, float]:

    normalized_requirement = normalize_text(requirement)

    best_skill = None
    best_match_type = "none"
    best_score = 0.0

    for skill in resume_skills:

        normalized_skill = normalize_text(skill)

        # 1. Exact
        if normalized_requirement == normalized_skill:
            return skill, "exact", 1.0

        # 2. Fuzzy
        fuzzy_score = fuzzy_similarity(
            requirement,
            skill,
        )

        if fuzzy_score > best_score:
            best_skill = skill
            best_match_type = "fuzzy"
            best_score = fuzzy_score

    # 3. Semantic
    for skill in resume_skills:

        semantic_score = semantic_similarity(
            requirement,
            skill,
        )

        if semantic_score > best_score:
            best_skill = skill
            best_match_type = "semantic"
            best_score = semantic_score

    return best_skill, best_match_type, best_score


def match_requirements(
    job: JobProfile,
    resume: ResumeProfile,
) -> list[MatchResult]:

    results = []

    for requirement in job.requirements:

        resume_evidence = collect_resume_evidence(resume)

        matched_text, match_type, score = find_best_resume_skill(
            requirement.name,
            resume_evidence,
        )

        if match_type == "exact":

            status = "matched"

        elif match_type == "fuzzy" and score >= FUZZY_THRESHOLD:

            status = "matched"

        elif match_type == "semantic" and score >= SEMANTIC_MATCH_THRESHOLD:

            status = "matched"

        elif (
            match_type == "semantic"
            and score >= SEMANTIC_PARTIAL_THRESHOLD
        ):

            status = "partial"

        else:

            status = "missing"
            match_type = "none"
            score = 0.0

        results.append(
             MatchResult(
            requirement=requirement.name,
            requirement_importance=requirement.importance,
            status=status,
            match_type=match_type,
            similarity_score=score,
            matched_text=matched_text,
    )
        )

    return results