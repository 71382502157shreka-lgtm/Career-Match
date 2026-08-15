import os
import shutil
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserOut, UserUpdateProfile
from app.services.resume_parser import extract_skills, extract_text_from_pdf, skills_to_csv

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_profile(
    payload: UserUpdateProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.skills is not None:
        current_user.skills = payload.skills
    if payload.headline is not None:
        current_user.headline = payload.headline
    if payload.linkedin_url is not None:
        current_user.linkedin_url = payload.linkedin_url
    if payload.github_url is not None:
        current_user.github_url = payload.github_url
    if payload.current_company is not None:
        current_user.current_company = payload.current_company
    if payload.education is not None:
        current_user.education = payload.education
    if payload.age is not None:
        current_user.age = payload.age
    if payload.location is not None:
        current_user.location = payload.location
    if payload.degree is not None:
        current_user.degree = payload.degree
    if payload.experience_years is not None:
        current_user.experience_years = payload.experience_years
    if payload.expected_salary is not None:
        current_user.expected_salary = payload.expected_salary
    if payload.resume_text is not None:
        current_user.resume_text = payload.resume_text
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/resume", response_model=UserOut)
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        text = extract_text_from_pdf(tmp_path)
        detected_skills = extract_skills(text)
    finally:
        os.remove(tmp_path)

    current_user.resume_text = text
    # Merge newly detected skills with any the candidate already listed
    existing = {s.strip().lower() for s in current_user.skills.split(",") if s.strip()}
    merged = existing.union(set(detected_skills))
    current_user.skills = skills_to_csv(sorted(merged))

    db.commit()
    db.refresh(current_user)
    return current_user
