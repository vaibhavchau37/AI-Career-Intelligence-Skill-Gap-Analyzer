"""Skill gap analyzer - identifies missing skills."""

from typing import List, Dict
from src.models.job_role import JobRole
from src.models.analysis_result import SkillGap
from src.core.skill_matcher import SkillMatcher


class SkillGapAnalyzer:
    """Analyze skill gaps between resume and job requirements."""
    
    def __init__(self):
        """Initialize skill gap analyzer."""
        self.skill_matcher = SkillMatcher()
    
    def analyze_gaps(
        self,
        resume_skills: List[str],
        job_role: JobRole
    ) -> List[SkillGap]:
        """
        Identify skill gaps for a job role.
        
        Args:
            resume_skills: List of skills from resume
            job_role: Job role to analyze against
            
        Returns:
            List of SkillGap objects
        """
        # Match skills to get missing ones
        match_result = self.skill_matcher.match_skills(resume_skills, job_role)
        
        gaps = []
        
        # Process missing required skills
        for req in match_result['missing_required']:
            gap = SkillGap(
                skill=req.skill,
                category='required',
                importance=req.importance,
                description=req.description,
            )
            gaps.append(gap)
        
        # Process missing preferred skills (lower priority)
        for pref in match_result['missing_preferred']:
            gap = SkillGap(
                skill=pref.skill,
                category='preferred',
                importance=pref.importance,
                description=pref.description,
            )
            gaps.append(gap)
        
        # Sort by importance (required first, then by importance value)
        gaps.sort(key=lambda x: (0 if x.category == 'required' else 1, -x.importance))
        
        return gaps

