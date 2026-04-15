from pydantic import BaseModel, Field
from typing import List


class ImprovementItem(BaseModel):
    section: str = Field(description="Which section this applies to, e.g. 'Experience', 'Skills'")
    issue: str = Field(description="Short description of the problem")
    suggestion: str = Field(description="Concrete fix or rewrite suggestion")


class FeedbackResponse(BaseModel):
    overall_score: int = Field(ge=0, le=100, description="Overall resume score out of 100")
    summary: str = Field(description="2-3 sentence overall assessment")
    strengths: List[str] = Field(description="List of 3-5 strong points in the resume")
    improvements: List[ImprovementItem] = Field(description="List of specific improvement suggestions")
    keywords_found: List[str] = Field(description="Relevant skills/keywords detected in the resume")
    keywords_missing: List[str] = Field(description="Important keywords that are absent but recommended")
    ats_score: int = Field(ge=0, le=100, description="ATS (Applicant Tracking System) compatibility score")
    ats_notes: str = Field(description="Short note on ATS compatibility issues or passes")