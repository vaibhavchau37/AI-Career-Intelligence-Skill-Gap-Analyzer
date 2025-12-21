"""Role predictor - predicts suitable job roles based on skills."""

from typing import List, Dict
from src.models.resume import Resume
from src.models.job_role import JobRole
from src.core.skill_matcher import SkillMatcher


class RolePredictor:
    """Predict suitable job roles based on resume skills."""
    
    def __init__(self):
        """Initialize role predictor."""
        self.skill_matcher = SkillMatcher()
    
    def predict_roles(
        self,
        resume: Resume,
        all_job_roles: List[JobRole],
        top_n: int = 3
    ) -> List[str]:
        """
        Predict suitable job roles based on skills.
        
        This is a simple implementation based on skill overlap.
        Can be enhanced with ML models if needed.
        
        Args:
            resume: Resume object
            all_job_roles: All available job roles
            top_n: Number of predictions to return
            
        Returns:
            List of predicted role names (sorted by suitability)
        """
        resume_skills = set(resume.get_all_skills())
        role_scores = []
        
        for job_role in all_job_roles:
            # Calculate skill overlap
            role_skills = set(job_role.get_all_skills())
            
            if not role_skills:
                continue
            
            # Calculate overlap ratio
            overlap = resume_skills.intersection(role_skills)
            overlap_ratio = len(overlap) / len(role_skills)
            
            # Also consider total number of matched skills
            matched_count = len(overlap)
            
            # Combined score (weighted)
            score = overlap_ratio * 0.7 + (min(matched_count / 10, 1.0) * 0.3)
            
            role_scores.append({
                'role_name': job_role.name,
                'score': score,
                'matched_skills_count': matched_count,
                'overlap_ratio': overlap_ratio,
            })
        
        # Sort by score
        role_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top N role names
        return [r['role_name'] for r in role_scores[:top_n]]

