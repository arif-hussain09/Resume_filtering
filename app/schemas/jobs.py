from typing import Literal
from pydantic import BaseModel, Field


class Requirement(BaseModel):
    name: str
    category: str
    importance: Literal["required", "preferred"]
    description: str | None = None


class ExperienceRequirement(BaseModel):
    description: str
    minimum_years: float | None = None


class JobProfile(BaseModel):
    title: str
    requirements: list[Requirement] = Field(default_factory=list)
    experience_requirements: list[ExperienceRequirement] = Field(
        default_factory=list
    )
    education_requirements: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    domain_context: list[str] = Field(default_factory=list)