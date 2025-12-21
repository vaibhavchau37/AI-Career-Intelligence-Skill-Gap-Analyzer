"""Resume data model."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class ResumeSection:
    """Represents a section of a resume."""
    name: str  # e.g., "Education", "Experience", "Skills"
    content: str  # Raw text content
    items: List[Dict] = field(default_factory=list)  # Structured items if parsed


@dataclass
class Resume:
    """Structured representation of a resume."""
    
    # Basic Information
    raw_text: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Sections
    sections: List[ResumeSection] = field(default_factory=list)
    
    # Extracted Information
    skills: List[str] = field(default_factory=list)  # Technical + soft skills
    technical_skills: List[str] = field(default_factory=list)
    soft_skills: List[str] = field(default_factory=list)
    
    # Experience
    years_of_experience: float = 0.0
    experience_items: List[Dict] = field(default_factory=list)
    
    # Education
    education: List[Dict] = field(default_factory=list)  # Degrees, certifications
    degrees: List[str] = field(default_factory=list)
    
    # Additional
    certifications: List[str] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    
    def get_section(self, name: str) -> Optional[ResumeSection]:
        """Get a specific section by name."""
        for section in self.sections:
            if section.name.lower() == name.lower():
                return section
        return None
    
    def get_all_skills(self) -> List[str]:
        """Get all skills (technical + soft)."""
        return list(set(self.skills + self.technical_skills))
    
    def to_dict(self) -> Dict:
        """Convert resume to dictionary."""
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "skills": self.get_all_skills(),
            "technical_skills": self.technical_skills,
            "soft_skills": self.soft_skills,
            "years_of_experience": self.years_of_experience,
            "education": self.education,
            "degrees": self.degrees,
            "certifications": self.certifications,
            "projects": self.projects,
        }

