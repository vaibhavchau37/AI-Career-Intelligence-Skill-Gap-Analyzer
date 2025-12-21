"""Analysis result data models."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class SkillGap:
    """Represents a missing skill with details."""
    skill: str
    category: str  # "required" or "preferred"
    importance: float
    description: Optional[str] = None
    learning_resources: List[str] = field(default_factory=list)


@dataclass
class RoleScore:
    """Score breakdown for a specific job role."""
    role_name: str
    overall_score: float  # 0-100
    breakdown: Dict[str, float]  # Score breakdown by category
    explanation: str  # Human-readable explanation
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[SkillGap] = field(default_factory=list)
    experience_score: float = 0.0
    education_score: float = 0.0
    skill_score: float = 0.0


@dataclass
class LearningPath:
    """A learning path for skill improvement."""
    skill: str
    priority: int  # 1 = highest priority
    estimated_days: int
    resources: List[str]  # URLs, course names, etc.
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Complete analysis result for a resume."""
    
    # Resume identifier
    resume_name: Optional[str] = None
    
    # Scores for each role
    scores: Dict[str, RoleScore] = field(default_factory=dict)
    
    # Skill gaps by role
    skill_gaps: Dict[str, List[SkillGap]] = field(default_factory=dict)
    
    # Learning roadmaps by role
    roadmaps: Dict[str, List[LearningPath]] = field(default_factory=dict)
    
    # Predicted suitable roles
    predicted_roles: List[str] = field(default_factory=list)
    
    # Top recommended roles (ranked)
    top_roles: List[str] = field(default_factory=list)
    
    # Summary
    summary: str = ""
    
    def get_top_role(self) -> Optional[str]:
        """Get the top recommended role."""
        return self.top_roles[0] if self.top_roles else None
    
    def get_role_score(self, role_name: str) -> Optional[float]:
        """Get overall score for a specific role."""
        if role_name in self.scores:
            return self.scores[role_name].overall_score
        return None
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary for JSON serialization."""
        return {
            "resume_name": self.resume_name,
            "top_roles": self.top_roles,
            "predicted_roles": self.predicted_roles,
            "scores": {
                role: {
                    "overall_score": score.overall_score,
                    "breakdown": score.breakdown,
                    "explanation": score.explanation,
                    "matched_skills": score.matched_skills,
                    "missing_skills": [
                        {
                            "skill": gap.skill,
                            "category": gap.category,
                            "importance": gap.importance,
                        }
                        for gap in score.missing_skills
                    ],
                }
                for role, score in self.scores.items()
            },
            "summary": self.summary,
        }

