"""
AI Matching Engine
-------------------------------------------------------------------
Scores how well a candidate (skills + resume text) matches a job
posting (title + description + required skills) using TF-IDF
vectorization and cosine similarity.

Why TF-IDF instead of a transformer model:
- Zero external downloads / no internet dependency at runtime, so it
  works instantly in any environment.
- Fast enough to rank hundreds of jobs/candidates in milliseconds.
- Fully swappable: replace `_vectorize` with sentence-transformers
  embeddings later without touching any calling code, since the
  public methods (`match_candidate_to_job`, `rank_jobs_for_candidate`,
  `rank_candidates_for_job`) keep the same signature.

Score = cosine_similarity(candidate_vector, job_vector) * 100,
expressed as a 0-100 percentage match.
"""
from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class AIJobMatcher:
    def __init__(self, skill_weight: float = 2.0):
        """
        skill_weight: how many times the skills list is repeated in the
        combined text before vectorizing, so exact skill overlap counts
        more heavily than incidental word overlap in free-text.
        """
        self.skill_weight = skill_weight
        self.vectorizer = TfidfVectorizer(stop_words="english")

    def _build_candidate_text(self, skills: str, resume_text: str) -> str:
        weighted_skills = (skills + " ") * int(self.skill_weight)
        return f"{weighted_skills} {resume_text}".strip()

    def _build_job_text(self, title: str, description: str, required_skills: str) -> str:
        weighted_skills = (required_skills + " ") * int(self.skill_weight)
        return f"{title} {weighted_skills} {description}".strip()

    def _cosine_score(self, text_a: str, text_b: str) -> float:
        if not text_a.strip() or not text_b.strip():
            return 0.0
        try:
            tfidf_matrix = self.vectorizer.fit_transform([text_a, text_b])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except ValueError:
            # Happens if both texts are pure stop-words / empty after cleaning
            return 0.0
        return round(float(similarity) * 100, 2)

    def match_candidate_to_job(self, candidate_skills: str, resume_text: str, job) -> float:
        """job must expose .title, .description, .required_skills attributes."""
        candidate_text = self._build_candidate_text(candidate_skills, resume_text)
        job_text = self._build_job_text(job.title, job.description, job.required_skills)
        return self._cosine_score(candidate_text, job_text)

    def rank_jobs_for_candidate(
        self, candidate_skills: str, resume_text: str, jobs: List
    ) -> List[Tuple]:
        """Returns [(job, score), ...] sorted by score descending."""
        scored = [
            (job, self.match_candidate_to_job(candidate_skills, resume_text, job))
            for job in jobs
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored

    def rank_candidates_for_job(self, job, candidates: List) -> List[Tuple]:
        """Returns [(candidate, score), ...] sorted by score descending.
        Used by recruiters to see the best-fit applicants for a job."""
        scored = [
            (candidate, self.match_candidate_to_job(candidate.skills, candidate.resume_text, job))
            for candidate in candidates
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored

    def skill_gap(self, candidate_skills: str, required_skills: str) -> List[str]:
        """Returns required skills the candidate does NOT list, for
        'skills you're missing' style feedback."""
        have = {s.strip().lower() for s in candidate_skills.split(",") if s.strip()}
        need = {s.strip().lower() for s in required_skills.split(",") if s.strip()}
        missing = sorted(need - have)
        return missing


# Singleton instance used across the app
ai_matcher = AIJobMatcher()
