"""Skill matcher - matches resume skills with job requirements."""

from typing import List, Dict, Tuple
from fuzzywuzzy import fuzz
from src.models.job_role import JobRole, SkillRequirement
from src.utils.text_processor import normalize_skill_name


class SkillMatcher:
    """Match resume skills with job role requirements."""
    
    def __init__(self, similarity_threshold: float = 0.8, fuzzy_threshold: int = 85):
        """
        Initialize skill matcher.
        
        Args:
            similarity_threshold: Minimum similarity for match (0-1) - for future use with embeddings
            fuzzy_threshold: Fuzzy matching threshold (0-100)
        """
        self.similarity_threshold = similarity_threshold
        self.fuzzy_threshold = fuzzy_threshold
    
    def match_skills(
        self,
        resume_skills: List[str],
        job_role: JobRole
    ) -> Dict[str, any]:
        """
        Match resume skills with job role requirements.
        
        Args:
            resume_skills: List of skills from resume
            job_role: Job role to match against
            
        Returns:
            Dictionary with matching results:
            - matched_required: List of matched required skills
            - matched_preferred: List of matched preferred skills
            - missing_required: List of missing required skills
            - missing_preferred: List of missing preferred skills
            - match_details: Detailed matching information
        """
        resume_skills_normalized = {normalize_skill_name(s): s for s in resume_skills}
        
        # Match required skills
        matched_required, missing_required = self._match_skill_list(
            resume_skills_normalized,
            job_role.required_skills
        )
        
        # Match preferred skills
        matched_preferred, missing_preferred = self._match_skill_list(
            resume_skills_normalized,
            job_role.preferred_skills
        )
        
        return {
            'matched_required': matched_required,
            'matched_preferred': matched_preferred,
            'missing_required': missing_required,
            'missing_preferred': missing_preferred,
            'match_ratio_required': len(matched_required) / max(len(job_role.required_skills), 1),
            'match_ratio_preferred': len(matched_preferred) / max(len(job_role.preferred_skills), 1),
        }
    
    def _match_skill_list(
        self,
        resume_skills: Dict[str, str],  # normalized -> original
        required_skills: List[SkillRequirement]
    ) -> Tuple[List[str], List[SkillRequirement]]:
        """
        Match a list of required skills with resume skills.
        
        Returns:
            Tuple of (matched skill names, missing SkillRequirements)
        """
        matched = []
        missing = []
        
        for req in required_skills:
            req_skill_normalized = normalize_skill_name(req.skill)
            
            # Exact match
            if req_skill_normalized in resume_skills:
                matched.append(req.skill)
                continue
            
            # Fuzzy match
            best_match = None
            best_score = 0
            
            for resume_skill_norm, resume_skill_orig in resume_skills.items():
                # Check substring match first (faster)
                if req_skill_normalized in resume_skill_norm or resume_skill_norm in req_skill_normalized:
                    score = 100
                else:
                    # Use fuzzy matching
                    score = fuzz.ratio(req_skill_normalized, resume_skill_norm)
                
                if score > best_score and score >= self.fuzzy_threshold:
                    best_score = score
                    best_match = resume_skill_orig
            
            if best_match:
                matched.append(req.skill)  # Use canonical name from requirement
            else:
                missing.append(req)
        
        return matched, missing
    
    def calculate_skill_similarity(self, skill1: str, skill2: str) -> float:
        """
        Calculate similarity between two skills.
        
        Returns:
            Similarity score (0-100)
        """
        norm1 = normalize_skill_name(skill1)
        norm2 = normalize_skill_name(skill2)
        
        # Exact match
        if norm1 == norm2:
            return 100.0
        
        # Substring match
        if norm1 in norm2 or norm2 in norm1:
            return 90.0
        
        # Fuzzy match
        return float(fuzz.ratio(norm1, norm2))

