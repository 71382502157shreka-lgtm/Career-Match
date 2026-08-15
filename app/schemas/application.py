from datetime import datetime

from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    job_id: int


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    match_score: float
    status: str
    applied_at: datetime

    class Config:
        from_attributes = True


class CandidateMatch(BaseModel):
    candidate_id: int
    full_name: str
    email: str
    match_score: float
