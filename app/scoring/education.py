from app.schemas.resume import Education


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def calculate_education_score(
    requirements: list[str],
    education: list[Education],
) -> float:

    if not requirements:
        return 100.0

    candidate_education = " ".join(
        normalize(
            f"{item.degree} {item.field or ''} {item.institution}"
        )
        for item in education
    )

    matched = 0

    for requirement in requirements:
        if normalize(requirement) in candidate_education:
            matched += 1

    return (matched / len(requirements)) * 100.0