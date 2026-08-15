import pytest
from app.core.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.job import JobPosting
from app.models.application import Application

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_missing_user_returns_none(db_session):
    non_existent_user = db_session.query(User).filter(User.id == 999999).first()
    assert non_existent_user is None

def test_user_skills_and_resume_text_empty_check(db_session):
    user = User(
        full_name="Test User",
        email="test_empty@example.com",
        hashed_password="hashed_pwd",
        skills="",
        resume_text=""
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert not (user.skills or "").strip()
    assert not (user.resume_text or "").strip()

    # Clean up
    db_session.delete(user)
    db_session.commit()
