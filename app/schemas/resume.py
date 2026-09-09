from pydantic import BaseModel, Field


class Experience(BaseModel):
    company: str
    role: str
    duration_years: float | None = None
    description: str | None = None


class Education(BaseModel):
    degree: str
    institution: str
    field: str | None = None


class Project(BaseModel):
    name: str
    description: str
    technologies: list[str] = Field(default_factory=list)
    target_audience: str | None = None


class ResumeProfile(BaseModel):
    name: str
    skills: list[str] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)