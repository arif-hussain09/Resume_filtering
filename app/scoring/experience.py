from app.schemas.jobs import ExperienceRequirement
from app.schemas.resume import Experience


def calculate_experience_score(
    requirements: list[ExperienceRequirement],
    experiences: list[Experience],
) -> float:
    if not requirements:
        return 100.0

    total_score = 0.0

    for requirement in requirements:
        if requirement.minimum_years is None:
            total_score += 100.0
            continue

        candidate_years = sum(
            experience.duration_years or 0.0
            for experience in experiences
        )

        if candidate_years >= requirement.minimum_years:
            total_score += 100.0
        else:
            total_score += (
                candidate_years / requirement.minimum_years
            ) * 100.0

    return min(total_score / len(requirements), 100.0)