"""Job role data model."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class SkillRequirement:
    """Represents a skill requirement for a job role."""
    skill: str
    required: bool  # True for must-have, False for nice-to-have
    importance: float = 1.0  # Weight (0-1) for scoring
    description: Optional[str] = None


@dataclass
class JobRole:
    """Represents a job role with its requirements."""
    
    name: str  # e.g., "ML Engineer", "Data Scientist"
    description: str
    
    # Skill Requirements
    required_skills: List[SkillRequirement] = field(default_factory=list)
    preferred_skills: List[SkillRequirement] = field(default_factory=list)
    
    # Experience Requirements
    min_years_experience: float = 0.0
    preferred_years_experience: float = 2.0
    
    # Education Requirements
    required_degrees: List[str] = field(default_factory=list)  # e.g., ["BS", "MS"]
    preferred_degrees: List[str] = field(default_factory=list)
    
    # Additional Requirements
    certifications: List[str] = field(default_factory=list)
    preferred_certifications: List[str] = field(default_factory=list)
    
    # Role-specific attributes
    attributes: Dict = field(default_factory=dict)
    
    def get_all_required_skills(self) -> List[str]:
        """Get list of all required skill names."""
        return [req.skill for req in self.required_skills]
    
    def get_all_preferred_skills(self) -> List[str]:
        """Get list of all preferred skill names."""
        return [req.skill for req in self.preferred_skills]
    
    def get_all_skills(self) -> List[str]:
        """Get all skills (required + preferred)."""
        return list(set(self.get_all_required_skills() + self.get_all_preferred_skills()))
    
    def to_dict(self) -> Dict:
        """Convert job role to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "required_skills": [req.skill for req in self.required_skills],
            "preferred_skills": [req.skill for req in self.preferred_skills],
            "min_years_experience": self.min_years_experience,
            "preferred_years_experience": self.preferred_years_experience,
            "required_degrees": self.required_degrees,
            "preferred_degrees": self.preferred_degrees,
        }

