from pydantic import BaseModel, Field
from typing import Literal



# For storing the location of evidence in the resume (e.g., page number and coordinates)
class EvidenceLocation(BaseModel):
    page_number: int
    x0: float
    y0: float
    x1: float
    y1: float


# For storing the evidence of a match, including the text, page number, and relevance score
class Evidence(BaseModel):
    text: str
    page_number: int | None = None
    relevance_score: float = 0.0
    locations: list[EvidenceLocation] = Field(default_factory=list)

class MatchResult(BaseModel):
    requirement: str
    requirement_importance: Literal["required", "preferred"]

    status: Literal["matched", "partial", "missing"]

    match_type: Literal[
        "exact",
        "fuzzy",
        "semantic",
        "none",
    ]

    similarity_score: float = 0.0
    score_contribution: float = 0.0
    matched_text: str | None = None

    evidence: list[Evidence] = Field(
        default_factory=list
    )

class ScoreBreakdown(BaseModel):
    required_score: float = 0.0
    preferred_score: float = 0.0
    experience_score: float = 0.0
    education_score: float = 0.0
    overall_score: float = 0.0
    # Effective (normalized) weight of each category in the overall score.
    # Categories the job does not test are dropped and their weight is
    # redistributed, so an empty category no longer grants free marks.
    weights_used: dict[str, float] = Field(default_factory=dict)


class ExtraFeature(BaseModel):
    name: str
    explanation: str
    evidence: list[Evidence] = Field(default_factory=list)


class Recommendation(BaseModel):
    area: str
    suggestion: str


class CandidateEvaluation(BaseModel):
    candidate_name: str

    score: ScoreBreakdown

    matched_requirements: list[MatchResult] = Field(
        default_factory=list
    )

    partial_requirements: list[MatchResult] = Field(
        default_factory=list
    )

    missing_requirements: list[MatchResult] = Field(
        default_factory=list
    )

    extra_features: list[ExtraFeature] = Field(
        default_factory=list
    )

    recommendations: list[Recommendation] = Field(
        default_factory=list
    )