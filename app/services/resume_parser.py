"""
Resume Parser
-------------------------------------------------------------------
Extracts raw text from an uploaded PDF resume and pulls out a skills
list by matching against a predefined skill bank. Swap SKILL_BANK for
a larger taxonomy (e.g. ESCO, O*NET, or a scraped skills dataset) for
production use.
"""
import re
from typing import List

from PyPDF2 import PdfReader

SKILL_BANK = [
    "python", "java", "javascript", "typescript", "react", "node.js",
    "sql", "nosql", "mongodb", "postgresql", "mysql", "aws", "azure",
    "gcp", "docker", "kubernetes", "machine learning", "deep learning",
    "fastapi", "django", "flask", "tensorflow", "pytorch", "nlp",
    "data analysis", "data structures", "excel", "communication",
    "project management", "c++", "c#", "html", "css", "git", "linux",
    "rest api", "graphql", "agile", "scrum", "power bi", "tableau",
]


def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF file on disk."""
    reader = PdfReader(file_path)
    text_chunks = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(text_chunks)


def extract_skills(text: str) -> List[str]:
    """Naive keyword-based skill extraction. Case-insensitive, whole
    word/phrase match."""
    text_lower = text.lower()
    found = [
        skill for skill in SKILL_BANK
        if re.search(rf"\b{re.escape(skill)}\b", text_lower)
    ]
    return found


def skills_to_csv(skills: List[str]) -> str:
    return ",".join(skills)
