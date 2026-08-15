from types import SimpleNamespace

from app.services.ai_matcher import AIJobMatcher


def make_job(title, description, required_skills):
    return SimpleNamespace(title=title, description=description, required_skills=required_skills)


def test_strong_match_scores_higher_than_weak_match():
    matcher = AIJobMatcher()

    python_job = make_job(
        "Backend Python Developer",
        "Build REST APIs using FastAPI and PostgreSQL for a growing startup.",
        "python,fastapi,sql,postgresql",
    )
    marketing_job = make_job(
        "Social Media Marketing Manager",
        "Plan and run marketing campaigns across Instagram and Facebook.",
        "marketing,social media,content writing",
    )

    candidate_skills = "python,fastapi,sql,docker"
    resume_text = "Experienced backend engineer skilled in Python, FastAPI, and PostgreSQL."

    python_score = matcher.match_candidate_to_job(candidate_skills, resume_text, python_job)
    marketing_score = matcher.match_candidate_to_job(candidate_skills, resume_text, marketing_job)

    assert python_score > marketing_score


def test_ranking_orders_jobs_by_score_descending():
    matcher = AIJobMatcher()
    jobs = [
        make_job("Data Analyst", "Analyze data using SQL and Excel.", "sql,excel,data analysis"),
        make_job("Python Backend Engineer", "Build APIs with Python and FastAPI.", "python,fastapi"),
    ]
    ranked = matcher.rank_jobs_for_candidate("python,fastapi", "Python developer with FastAPI experience", jobs)
    scores = [score for _, score in ranked]
    assert scores == sorted(scores, reverse=True)


def test_skill_gap_detects_missing_skills():
    matcher = AIJobMatcher()
    missing = matcher.skill_gap(candidate_skills="python,sql", required_skills="python,sql,docker,aws")
    assert missing == ["aws", "docker"]


def test_empty_inputs_score_zero():
    matcher = AIJobMatcher()
    job = make_job("Any Role", "Some description", "some,skills")
    assert matcher.match_candidate_to_job("", "", job) == 0.0
