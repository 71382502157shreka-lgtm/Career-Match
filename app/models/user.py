from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="candidate")  # candidate | recruiter
    skills = Column(Text, default="")  # comma-separated skills, e.g. "python,sql,fastapi"
    resume_text = Column(Text, default="")  # raw extracted resume text
    headline = Column(String(255), default="")
    linkedin_url = Column(String(255), default="")
    github_url = Column(String(255), default="")
    current_company = Column(String(120), default="")
    education = Column(String(255), default="")
    age = Column(Integer, nullable=True)
    location = Column(String(120), default="")
    degree = Column(String(120), default="")
    experience_years = Column(Integer, default=0)
    expected_salary = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    jobs_posted = relationship("JobPosting", back_populates="recruiter")
