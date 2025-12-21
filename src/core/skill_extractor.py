"""Skill extractor - identifies skills from resume text."""

import json
import os
from typing import List, Set, Dict
from pathlib import Path
from src.models.resume import Resume
from src.utils.text_processor import normalize_skill_name, clean_text


class SkillExtractor:
    """Extract skills from resume using skill taxonomy."""
    
    def __init__(self, skill_taxonomy_path: str = None, skill_synonyms_path: str = None):
        """
        Initialize skill extractor.
        
        Args:
            skill_taxonomy_path: Path to skill taxonomy JSON file
            skill_synonyms_path: Path to skill synonyms JSON file
        """
        self.skill_taxonomy: Dict = {}
        self.skill_synonyms: Dict = {}
        
        # Load skill taxonomy if provided
        if skill_taxonomy_path and os.path.exists(skill_taxonomy_path):
            with open(skill_taxonomy_path, 'r', encoding='utf-8') as f:
                self.skill_taxonomy = json.load(f)
        
        # Load skill synonyms if provided
        if skill_synonyms_path and os.path.exists(skill_synonyms_path):
            with open(skill_synonyms_path, 'r', encoding='utf-8') as f:
                self.skill_synonyms = json.load(f)
        
        # Build skill lookup maps
        self._build_skill_maps()
    
    def _build_skill_maps(self):
        """Build lookup maps for efficient skill matching."""
        # Normalized skill name -> canonical skill name
        self.normalized_to_canonical: Dict[str, str] = {}
        
        # Add skills from taxonomy
        if isinstance(self.skill_taxonomy, dict):
            for category, skills in self.skill_taxonomy.items():
                if isinstance(skills, list):
                    for skill in skills:
                        canonical = skill if isinstance(skill, str) else skill.get('name', '')
                        normalized = normalize_skill_name(canonical)
                        self.normalized_to_canonical[normalized] = canonical
        
        # Add synonyms
        if isinstance(self.skill_synonyms, dict):
            for canonical, synonyms in self.skill_synonyms.items():
                normalized_canonical = normalize_skill_name(canonical)
                self.normalized_to_canonical[normalized_canonical] = canonical
                
                if isinstance(synonyms, list):
                    for synonym in synonyms:
                        normalized_syn = normalize_skill_name(synonym)
                        self.normalized_to_canonical[normalized_syn] = canonical
    
    def extract_skills(self, resume: Resume) -> List[str]:
        """
        Extract all skills from resume.
        
        Args:
            resume: Resume object
            
        Returns:
            List of identified skills (canonical names)
        """
        all_skills: Set[str] = set()
        
        # Extract from skills section
        skills_section = resume.get_section("skills")
        if skills_section:
            skills_text = skills_section.content
            skills = self._extract_from_text(skills_text)
            all_skills.update(skills)
        
        # Extract from entire resume text
        skills_from_text = self._extract_from_text(resume.raw_text)
        all_skills.update(skills_from_text)
        
        # Add skills already identified in resume
        for skill in resume.skills:
            normalized = normalize_skill_name(skill)
            if normalized in self.normalized_to_canonical:
                all_skills.add(self.normalized_to_canonical[normalized])
            else:
                # Keep original if not in taxonomy
                all_skills.add(skill)
        
        return sorted(list(all_skills))
    
    def _extract_from_text(self, text: str) -> List[str]:
        """
        Extract skills from text using taxonomy matching.
        
        Args:
            text: Text to extract skills from
            
        Returns:
            List of identified skills
        """
        if not text:
            return []
        
        text_lower = text.lower()
        found_skills: Set[str] = set()
        
        # Match against normalized skill names
        for normalized, canonical in self.normalized_to_canonical.items():
            # Check if skill name appears in text
            if normalized in text_lower:
                found_skills.add(canonical)
        
        # Also check for common technical skills patterns
        common_patterns = {
            r'\bpython\b': 'Python',
            r'\bjava\b': 'Java',
            r'\bjavascript\b': 'JavaScript',
            r'\bjava\s*script\b': 'JavaScript',
            r'\btypescript\b': 'TypeScript',
            r'\bsql\b': 'SQL',
            r'\bhtml\b': 'HTML',
            r'\bcss\b': 'CSS',
            r'\baws\b': 'AWS',
            r'\bdocker\b': 'Docker',
            r'\bkubernetes\b': 'Kubernetes',
            r'\bmachine\s+learning\b': 'Machine Learning',
            r'\bdeep\s+learning\b': 'Deep Learning',
            r'\bdata\s+science\b': 'Data Science',
            r'\btensorflow\b': 'TensorFlow',
            r'\bkeras\b': 'Keras',
            r'\bpytorch\b': 'PyTorch',
            r'\bscikit-learn\b': 'Scikit-learn',
            r'\bscikit\s+learn\b': 'Scikit-learn',
            r'\bgit\b': 'Git',
            r'\bgithub\b': 'GitHub',
        }
        
        import re
        for pattern, skill_name in common_patterns.items():
            if re.search(pattern, text_lower):
                found_skills.add(skill_name)
        
        return list(found_skills)
    
    def categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """
        Categorize skills into technical and soft skills.
        
        Args:
            skills: List of skill names
            
        Returns:
            Dictionary with 'technical' and 'soft' keys
        """
        technical_keywords = [
            'programming', 'language', 'framework', 'library', 'tool',
            'database', 'cloud', 'ml', 'ai', 'algorithm', 'software',
            'development', 'engineering', 'system', 'api', 'web',
        ]
        
        soft_keywords = [
            'communication', 'leadership', 'teamwork', 'problem solving',
            'management', 'collaboration', 'presentation', 'negotiation',
        ]
        
        technical = []
        soft = []
        other = []
        
        for skill in skills:
            skill_lower = skill.lower()
            
            if any(keyword in skill_lower for keyword in technical_keywords):
                technical.append(skill)
            elif any(keyword in skill_lower for keyword in soft_keywords):
                soft.append(skill)
            else:
                # Default to technical for unknown
                technical.append(skill)
        
        return {
            'technical': technical,
            'soft': soft,
            'other': other,
        }

