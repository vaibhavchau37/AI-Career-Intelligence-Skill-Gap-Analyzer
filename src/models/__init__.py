"""Data models for the career analyzer."""

from .resume import Resume, ResumeSection
from .job_role import JobRole, SkillRequirement
from .analysis_result import AnalysisResult, RoleScore, SkillGap

__all__ = [
    "Resume",
    "ResumeSection",
    "JobRole",
    "SkillRequirement",
    "AnalysisResult",
    "RoleScore",
    "SkillGap",
]

