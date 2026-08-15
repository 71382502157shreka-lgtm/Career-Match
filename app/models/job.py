from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    company = Column(String(150), nullable=False)
    location = Column(String(120), default="Remote")
    description = Column(Text, nullable=False)
    required_skills = Column(Text, nullable=False)  # comma-separated
    experience_years = Column(Integer, default=0)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    job_type = Column(String(50), default="Full-time")  # Full-time, Contract, Part-time, Internship
    workplace_type = Column(String(50), default="Hybrid")  # On-site, Hybrid, Remote
    linkedin_url = Column(String(255), default="")
    company_logo_url = Column(String(255), default="")
    posted_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    recruiter = relationship("User", back_populates="jobs_posted")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
