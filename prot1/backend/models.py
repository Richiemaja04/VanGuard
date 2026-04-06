"""
models.py — Pydantic + DB Models for ResumeIQ
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class EducationLevel(str, Enum):
    HIGH_SCHOOL  = "High School Diploma"
    ASSOCIATE    = "Associate's Degree"
    BACHELOR     = "Bachelor's Degree"
    MASTER       = "Master's Degree"
    PHD          = "PhD / Doctorate"
    BOOTCAMP     = "Bootcamp / Self-taught"


class ExperienceLevel(str, Enum):
    ENTRY  = "Entry Level (0-1 years)"
    JUNIOR = "Junior (1-3 years)"
    MID    = "Mid-level (3-6 years)"
    SENIOR = "Senior (6-10 years)"
    LEAD   = "Lead / Staff (10+ years)"


class TemplateChoice(str, Enum):
    CLASSIC   = "classic"
    MODERN    = "modern"
    TECHNICAL = "technical"


# ──── Request Models ────

class UserProfile(BaseModel):
    name:             str = Field(..., min_length=1)
    email:            EmailStr
    phone:            Optional[str] = None
    location:         Optional[str] = None
    education_level:  Optional[EducationLevel] = None
    experience_level: Optional[ExperienceLevel] = None
    preferred_role:   Optional[str] = None
    linkedin:         Optional[str] = None

    class Config:
        use_enum_values = True


class JobDescriptionInput(BaseModel):
    title:       Optional[str] = None
    company:     Optional[str] = None
    description: str = Field(..., min_length=50)


class ScratchResumeInput(BaseModel):
    job_description: str = Field(..., min_length=50)
    template:        TemplateChoice = TemplateChoice.TECHNICAL
    user_data: Dict[str, Any] = Field(default_factory=dict)


# ──── Response Models ────

class ImprovementHint(BaseModel):
    type:   str  # "error" | "warning" | "info"
    title:  str
    detail: str


class SectionScore(BaseModel):
    section: str
    score:   float


class ParsedResume(BaseModel):
    text:       str
    skills:     List[str]
    word_count: int
    sections:   Dict[str, str]
    entities:   Dict[str, List[str]]


class AnalysisResult(BaseModel):
    ats_score:          float = Field(..., ge=0, le=100, description="Composite ATS score (0–100)")
    keyword_match:      float = Field(..., ge=0, le=100)
    skill_match:        float = Field(..., ge=0, le=100)
    experience_match:   float = Field(..., ge=0, le=100)
    formatting_score:   float = Field(..., ge=0, le=100)
    matched_keywords:   List[str] = []
    missing_keywords:   List[str] = []
    resume_skills:      List[str] = []
    jd_skills:          List[str] = []
    section_scores:     Dict[str, float] = {}
    improvements:       List[ImprovementHint] = []
    optimized_resume_url: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "ats_score":        87.4,
                "keyword_match":    78.0,
                "skill_match":      92.0,
                "experience_match": 74.0,
                "formatting_score": 96.0,
                "matched_keywords": ["Python", "FastAPI", "PostgreSQL"],
                "missing_keywords": ["Kubernetes", "Terraform"],
                "optimized_resume_url": "/static/generated_resumes/resume_abc123.pdf",
            }
        }