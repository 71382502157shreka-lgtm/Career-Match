from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"))
    candidate_id = Column(Integer, ForeignKey("users.id"))
    match_score = Column(Float, default=0.0)  # AI-computed compatibility %
    status = Column(String(30), default="applied")  # applied | shortlisted | rejected | hired
    applied_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("JobPosting", back_populates="applications")
    candidate = relationship("User", back_populates="applications")
