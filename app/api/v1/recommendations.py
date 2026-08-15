from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.application import Application
from app.models.job import JobPosting
from app.models.user import User
from app.schemas.application import ApplicationOut, CandidateMatch
from app.schemas.job import JobMatch
from app.services.ai_matcher import ai_matcher

router = APIRouter(tags=["AI Recommendations"])


@router.get("/recommendations", response_model=List[JobMatch])
def recommend_jobs(
    top_n: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the top_n jobs best matching the current candidate's
    skills + resume, ranked by AI match score (0-100)."""
    jobs = db.query(JobPosting).all()
    ranked = ai_matcher.rank_jobs_for_candidate(current_user.skills, current_user.resume_text, jobs)

    results = []
    for job, score in ranked:
        if score < settings.MIN_MATCH_SCORE:
            continue
        job_out = JobMatch.model_validate(job)
        job_out.match_score = score
        results.append(job_out)
        if len(results) >= top_n:
            break
    return results


@router.get("/jobs/{job_id}/skill-gap")
def get_skill_gap(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Shows which required skills for a job the candidate is missing."""
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    missing = ai_matcher.skill_gap(current_user.skills, job.required_skills)
    return {"job_id": job_id, "missing_skills": missing}


@router.post("/jobs/{job_id}/apply", response_model=ApplicationOut, status_code=201)
def apply_to_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = (
        db.query(Application)
        .filter(Application.job_id == job_id, Application.candidate_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already applied to this job")

    score = ai_matcher.match_candidate_to_job(current_user.skills, current_user.resume_text, job)
    application = Application(job_id=job_id, candidate_id=current_user.id, match_score=score)
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("/jobs/{job_id}/candidates", response_model=List[CandidateMatch])
def ranked_candidates_for_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recruiter view: applicants for a job ranked by AI match score."""
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.posted_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view these candidates")

    applications = db.query(Application).filter(Application.job_id == job_id).all()
    candidates = [app.candidate for app in applications]
    ranked = ai_matcher.rank_candidates_for_job(job, candidates)

    return [
        CandidateMatch(
            candidate_id=c.id, full_name=c.full_name, email=c.email, match_score=score
        )
        for c, score in ranked
    ]
