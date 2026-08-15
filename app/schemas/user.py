from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field(default="candidate", pattern="^(candidate|recruiter)$")
    skills: Optional[str] = ""
    headline: Optional[str] = ""
    linkedin_url: Optional[str] = ""
    github_url: Optional[str] = ""
    current_company: Optional[str] = ""
    education: Optional[str] = ""
    age: Optional[int] = None
    location: Optional[str] = ""
    degree: Optional[str] = ""
    experience_years: Optional[int] = 0
    expected_salary: Optional[float] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdateProfile(BaseModel):
    full_name: Optional[str] = None
    skills: Optional[str] = None
    headline: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    current_company: Optional[str] = None
    education: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None
    degree: Optional[str] = None
    experience_years: Optional[int] = None
    expected_salary: Optional[float] = None
    resume_text: Optional[str] = None


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    skills: str
    headline: Optional[str] = ""
    linkedin_url: Optional[str] = ""
    github_url: Optional[str] = ""
    current_company: Optional[str] = ""
    education: Optional[str] = ""
    age: Optional[int] = None
    location: Optional[str] = ""
    degree: Optional[str] = ""
    experience_years: Optional[int] = 0
    expected_salary: Optional[float] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
