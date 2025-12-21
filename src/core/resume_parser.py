"""Resume parser - extracts structured information from resume text."""

import re
from typing import List, Optional
from src.models.resume import Resume, ResumeSection
from src.utils.text_processor import clean_text, extract_email, extract_phone, extract_degrees


class ResumeParser:
    """Parse resume text into structured Resume object."""
    
    # Common section headers
    SECTION_KEYWORDS = {
        "education": ["education", "academic", "qualifications"],
        "experience": ["experience", "work experience", "employment", "work history"],
        "skills": ["skills", "technical skills", "competencies", "expertise"],
        "projects": ["projects", "portfolio", "work samples"],
        "certifications": ["certifications", "certificates", "licenses"],
        "achievements": ["achievements", "awards", "honors"],
        "summary": ["summary", "objective", "profile", "about"],
    }
    
    def __init__(self):
        """Initialize the parser."""
        pass
    
    def parse(self, resume_text: str) -> Resume:
        """
        Parse resume text into structured Resume object.
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Parsed Resume object
        """
        resume = Resume(raw_text=resume_text)
        
        # Extract basic information
        resume.email = extract_email(resume_text)
        resume.phone = extract_phone(resume_text)
        resume.name = self._extract_name(resume_text)
        
        # Split into sections
        resume.sections = self._split_into_sections(resume_text)
        
        # Extract structured information
        resume.skills = self._extract_skills_from_text(resume_text)
        resume.years_of_experience = self._extract_experience_years(resume_text)
        resume.education = self._extract_education(resume_text)
        resume.degrees = extract_degrees(resume_text)
        resume.certifications = self._extract_certifications(resume_text)
        resume.projects = self._extract_projects(resume_text)
        
        return resume
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract name from resume (usually first line)."""
        lines = text.split('\n')
        if lines:
            first_line = lines[0].strip()
            # Simple heuristic: first line that's not too long and has capital letters
            if len(first_line) < 50 and any(c.isupper() for c in first_line):
                return first_line
        return None
    
    def _split_into_sections(self, text: str) -> List[ResumeSection]:
        """Split resume text into sections."""
        sections = []
        lines = text.split('\n')
        
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line is a section header
            section_name = self._identify_section_header(line)
            
            if section_name:
                # Save previous section
                if current_section:
                    current_section.content = '\n'.join(current_content)
                    sections.append(current_section)
                
                # Start new section
                current_section = ResumeSection(name=section_name, content="")
                current_content = []
            else:
                # Add to current section
                if current_section:
                    current_content.append(line)
                else:
                    # Content before any section - might be header/summary
                    if not current_section:
                        current_section = ResumeSection(name="header", content="")
                        current_content.append(line)
        
        # Save last section
        if current_section:
            current_section.content = '\n'.join(current_content)
            sections.append(current_section)
        
        return sections
    
    def _identify_section_header(self, line: str) -> Optional[str]:
        """Identify if a line is a section header."""
        line_lower = line.lower().strip()
        
        # Check for common patterns
        for section_name, keywords in self.SECTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in line_lower:
                    # Check if it's likely a header (short line, may have colons, etc.)
                    if len(line) < 50 or line.endswith(':'):
                        return section_name
        
        return None
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills mentioned in text (basic version)."""
        # This is a simple implementation - SkillExtractor will do better
        skills_section = None
        for section in self._split_into_sections(text):
            if section.name == "skills":
                skills_section = section.content
                break
        
        if skills_section:
            # Split by common delimiters
            skills = re.split(r'[,;•\-\n]', skills_section)
            skills = [s.strip() for s in skills if s.strip()]
            return skills[:50]  # Limit to avoid noise
        
        return []
    
    def _extract_experience_years(self, text: str) -> float:
        """Extract years of experience from resume."""
        # Look for patterns like "5 years", "3+ years", etc.
        patterns = [
            r'(\d+\.?\d*)\s*\+?\s*years?\s+(?:of\s+)?(?:experience|exp)',
            r'(\d+\.?\d*)\s*yrs?\s+(?:of\s+)?(?:experience|exp)',
        ]
        
        max_years = 0.0
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    years = float(match)
                    max_years = max(max_years, years)
                except ValueError:
                    continue
        
        return max_years
    
    def _extract_education(self, text: str) -> List[dict]:
        """Extract education information."""
        education = []
        edu_section = None
        
        for section in self._split_into_sections(text):
            if section.name == "education":
                edu_section = section.content
                break
        
        if edu_section:
            # Simple extraction - can be enhanced
            lines = edu_section.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['bachelor', 'master', 'phd', 'degree', 'bs', 'ms']):
                    education.append({"text": line.strip()})
        
        return education
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications."""
        certifications = []
        cert_section = None
        
        for section in self._split_into_sections(text):
            if section.name == "certifications":
                cert_section = section.content
                break
        
        if cert_section:
            lines = cert_section.split('\n')
            certifications = [line.strip() for line in lines if line.strip()]
        
        return certifications
    
    def _extract_projects(self, text: str) -> List[str]:
        """Extract projects."""
        projects = []
        project_section = None
        
        for section in self._split_into_sections(text):
            if section.name == "projects":
                project_section = section.content
                break
        
        if project_section:
            # Split projects by bullet points or newlines
            items = re.split(r'\n(?=\w)', project_section)
            projects = [item.strip() for item in items if item.strip()]
        
        return projects

