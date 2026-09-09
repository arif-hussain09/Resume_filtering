from dataclasses import dataclass, field


class BaseModel:
    """Local schema base class used when Pydantic is unavailable."""

    pass


@dataclass
class Experience(BaseModel):
    company: str
    role: str
    duration_years: float | None = None
    description: str | None = None


@dataclass
class Education(BaseModel):
    degree: str
    institution: str
    field: str | None = None


@dataclass
class Project(BaseModel):
    name: str
    description: str
    technologies: list[str] = field(default_factory=list)
    target_audience: str | None = None


@dataclass
class ResumeProfile(BaseModel):
    name: str
    skills: list[str] = field(default_factory=list)
    experience: list[Experience] = field(default_factory=list)
    education: list[Education] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    achievements: list[str] = field(default_factory=list)