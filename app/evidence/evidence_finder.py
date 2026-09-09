from app.schemas.resume import ResumeProfile


def collect_resume_evidence(
    resume: ResumeProfile,
) -> list[str]:

    evidence: list[str] = []

    evidence.extend(resume.skills)

    for experience in resume.experience:
        evidence.append(experience.role)

        if experience.description:
            evidence.append(experience.description)

    for project in resume.projects:
        evidence.append(project.name)
        evidence.append(project.description)
        evidence.extend(project.technologies)

    evidence.extend(resume.certifications)
    evidence.extend(resume.achievements)

    return [
        item.strip()
        for item in evidence
        if item and item.strip()
    ]