from typing import Optional

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    company: str = Field(..., min_length=2, max_length=150)
    location: str = "Remote"
    description: str = Field(..., min_length=10)
    required_skills: str  # comma-separated, e.g. "python,fastapi,sql"
    experience_years: int = 0
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    job_type: Optional[str] = "Full-time"
    workplace_type: Optional[str] = "Hybrid"
    linkedin_url: Optional[str] = ""
    company_logo_url: Optional[str] = ""


class JobOut(BaseModel):
    id: int
    title: str
    company: str
    location: str
    description: str
    required_skills: str
    experience_years: int
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    job_type: Optional[str] = "Full-time"
    workplace_type: Optional[str] = "Hybrid"
    linkedin_url: Optional[str] = ""
    company_logo_url: Optional[str] = ""

    class Config:
        from_attributes = True


class JobMatch(JobOut):
    match_score: float = 0.0
