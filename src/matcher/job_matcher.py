"""Job matcher - matches resume to multiple job roles."""

from typing import List, Dict
from src.models.resume import Resume
from src.models.job_role import JobRole
from src.core.score_calculator import ScoreCalculator
from src.core.skill_matcher import SkillMatcher


class JobMatcher:
    """Match resume to multiple job roles and rank them."""
    
    def __init__(self, config: Dict = None):
        """
        Initialize job matcher.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.score_calculator = ScoreCalculator(config)
        self.skill_matcher = SkillMatcher()
    
    def match_roles(
        self,
        resume: Resume,
        job_roles: List[JobRole],
        top_n: int = 5
    ) -> List[Dict]:
        """
        Match resume to multiple job roles and return ranked results.
        
        Args:
            resume: Resume object
            job_roles: List of job roles to match against
            top_n: Number of top matches to return
            
        Returns:
            List of match results, sorted by score (highest first)
            Each result contains: role_name, score, breakdown, details
        """
        results = []
        resume_skills = resume.get_all_skills()
        
        for job_role in job_roles:
            # Match skills
            skill_match_result = self.skill_matcher.match_skills(resume_skills, job_role)
            
            # Calculate score
            score_result = self.score_calculator.calculate_score(
                resume, job_role, skill_match_result
            )
            
            results.append({
                'role_name': job_role.name,
                'role_description': job_role.description,
                'score': score_result['overall_score'],
                'breakdown': score_result['breakdown'],
                'skill_match': skill_match_result,
                'job_role': job_role,  # Include full role for further processing
            })
        
        # Sort by score (descending)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top N
        return results[:top_n]
    
    def get_best_match(self, resume: Resume, job_roles: List[JobRole]) -> Dict:
        """Get the best matching job role."""
        matches = self.match_roles(resume, job_roles, top_n=1)
        return matches[0] if matches else None

