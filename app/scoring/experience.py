"""Experience scoring.

Keeps the original years-based logic but adds one safeguard: if the LLM
could not parse ANY duration (dates like "Jun 2020 - Present" sometimes
fail), the candidate gets documented partial credit instead of a hard 0,
which previously punished strong candidates for an extraction hiccup.
"""

from __future__ import annotations

from app.schemas.jobs import ExperienceRequirement
from app.schemas.resume import Experience

# Credit per requirement when durations could not be parsed at all but
# the candidate clearly has work experience entries.
UNPARSED_DURATION_CREDIT = 50.0


def calculate_experience_score(
    requirements: list[ExperienceRequirement],
    experiences: list[Experience],
) -> float:

    if not requirements:
        # Dynamic weights drop this category when the job has no
        # experience requirements.
        return 100.0

    candidate_years = sum(
        experience.duration_years or 0.0 for experience in experiences
    )
    durations_unparsed = bool(experiences) and candidate_years == 0.0

    total = 0.0
    for requirement in requirements:
        if requirement.minimum_years is None:
            total += 100.0
            continue

        if durations_unparsed:
            total += UNPARSED_DURATION_CREDIT
            continue

        if candidate_years >= requirement.minimum_years:
            total += 100.0
        else:
            total += (
                candidate_years / requirement.minimum_years
            ) * 100.0

    return round(min(total / len(requirements), 100.0), 2)
