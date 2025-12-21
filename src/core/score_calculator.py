"""Score calculator - calculates job readiness scores."""

from typing import Dict
import yaml
from pathlib import Path
from src.models.resume import Resume
from src.models.job_role import JobRole
from src.core.skill_matcher import SkillMatcher


class ScoreCalculator:
    """Calculate job readiness scores."""
    
    def __init__(self, config: Dict = None):
        """
        Initialize score calculator.
        
        Args:
            config: Configuration dictionary with scoring weights
        """
        self.config = config or {}
        self.weights = self.config.get('scoring', {
            'required_skills': 40,
            'preferred_skills': 20,
            'experience': 20,
            'education': 10,
            'certifications': 10,
        })
        
        # Normalize weights to sum to 100
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: (v / total) * 100 for k, v in self.weights.items()}
        
        self.skill_matcher = SkillMatcher()
    
    def calculate_score(
        self,
        resume: Resume,
        job_role: JobRole,
        skill_match_result: Dict = None
    ) -> Dict:
        """
        Calculate overall job readiness score.
        
        Args:
            resume: Resume object
            job_role: Job role to score against
            skill_match_result: Pre-computed skill matching result (optional)
            
        Returns:
            Dictionary with score breakdown and details
        """
        # Get skill matching results
        if skill_match_result is None:
            resume_skills = resume.get_all_skills()
            skill_match_result = self.skill_matcher.match_skills(resume_skills, job_role)
        
        # Calculate component scores
        required_skills_score = self._calculate_required_skills_score(
            skill_match_result, job_role
        )
        
        preferred_skills_score = self._calculate_preferred_skills_score(
            skill_match_result, job_role
        )
        
        experience_score = self._calculate_experience_score(resume, job_role)
        education_score = self._calculate_education_score(resume, job_role)
        certifications_score = self._calculate_certifications_score(resume, job_role)
        
        # Calculate weighted overall score
        overall_score = (
            required_skills_score * self.weights['required_skills'] / 100 +
            preferred_skills_score * self.weights['preferred_skills'] / 100 +
            experience_score * self.weights['experience'] / 100 +
            education_score * self.weights['education'] / 100 +
            certifications_score * self.weights['certifications'] / 100
        )
        
        # Ensure score is between 0 and 100
        overall_score = max(0, min(100, overall_score))
        
        return {
            'overall_score': round(overall_score, 2),
            'breakdown': {
                'required_skills': round(required_skills_score, 2),
                'preferred_skills': round(preferred_skills_score, 2),
                'experience': round(experience_score, 2),
                'education': round(education_score, 2),
                'certifications': round(certifications_score, 2),
            },
            'skill_match_result': skill_match_result,
            'component_scores': {
                'required_skills_score': required_skills_score,
                'preferred_skills_score': preferred_skills_score,
                'experience_score': experience_score,
                'education_score': education_score,
                'certifications_score': certifications_score,
            }
        }
    
    def _calculate_required_skills_score(self, skill_match_result: Dict, job_role: JobRole) -> float:
        """Calculate score based on required skills match."""
        matched_count = len(skill_match_result['matched_required'])
        total_required = len(job_role.required_skills)
        
        if total_required == 0:
            return 100.0  # No requirements means perfect score
        
        # Percentage of required skills matched
        match_ratio = matched_count / total_required
        
        # Linear scaling: 0% match = 0, 100% match = 100
        return match_ratio * 100.0
    
    def _calculate_preferred_skills_score(self, skill_match_result: Dict, job_role: JobRole) -> float:
        """Calculate score based on preferred skills match."""
        matched_count = len(skill_match_result['matched_preferred'])
        total_preferred = len(job_role.preferred_skills)
        
        if total_preferred == 0:
            return 100.0  # No preferred skills means perfect score
        
        match_ratio = matched_count / total_preferred
        return match_ratio * 100.0
    
    def _calculate_experience_score(self, resume: Resume, job_role: JobRole) -> float:
        """Calculate score based on years of experience."""
        resume_years = resume.years_of_experience
        required_years = job_role.min_years_experience
        preferred_years = job_role.preferred_years_experience
        
        # If below minimum, score decreases linearly
        if resume_years < required_years:
            if required_years > 0:
                return (resume_years / required_years) * 50  # Max 50 if below minimum
            return 0.0
        
        # If meets minimum but below preferred, score between 50-100
        if resume_years < preferred_years:
            if preferred_years > required_years:
                progress = (resume_years - required_years) / (preferred_years - required_years)
                return 50 + (progress * 50)
            return 75.0
        
        # If meets or exceeds preferred, score 100
        return 100.0
    
    def _calculate_education_score(self, resume: Resume, job_role: JobRole) -> float:
        """Calculate score based on education alignment."""
        resume_degrees = [deg.upper() for deg in resume.degrees]
        
        # Check if any required degree is present
        required_met = False
        if job_role.required_degrees:
            for req_degree in job_role.required_degrees:
                req_normalized = req_degree.upper().replace('.', '').replace(' ', '')
                for resume_degree in resume_degrees:
                    res_normalized = resume_degree.upper().replace('.', '').replace(' ', '')
                    if req_normalized in res_normalized or res_normalized in req_normalized:
                        required_met = True
                        break
        else:
            # No specific requirement
            required_met = True
        
        if not required_met:
            return 0.0
        
        # Check preferred degrees
        preferred_met = False
        if job_role.preferred_degrees:
            for pref_degree in job_role.preferred_degrees:
                pref_normalized = pref_degree.upper().replace('.', '').replace(' ', '')
                for resume_degree in resume_degrees:
                    res_normalized = resume_degree.upper().replace('.', '').replace(' ', '')
                    if pref_normalized in res_normalized or res_normalized in pref_normalized:
                        preferred_met = True
                        break
        else:
            preferred_met = True
        
        if preferred_met:
            return 100.0
        else:
            return 75.0  # Meets required but not preferred
    
    def _calculate_certifications_score(self, resume: Resume, job_role: JobRole) -> float:
        """Calculate score based on certifications."""
        if not job_role.certifications and not job_role.preferred_certifications:
            return 100.0  # No certification requirements
        
        resume_certs = [cert.lower() for cert in resume.certifications]
        
        # Check required certifications
        required_met = 0
        if job_role.certifications:
            for req_cert in job_role.certifications:
                req_normalized = req_cert.lower()
                for resume_cert in resume_certs:
                    if req_normalized in resume_cert or resume_cert in req_normalized:
                        required_met += 1
                        break
        
        # Check preferred certifications
        preferred_met = 0
        if job_role.preferred_certifications:
            for pref_cert in job_role.preferred_certifications:
                pref_normalized = pref_cert.lower()
                for resume_cert in resume_certs:
                    if pref_normalized in resume_cert or resume_cert in pref_normalized:
                        preferred_met += 1
                        break
        
        # Calculate score (weighted)
        total_required = len(job_role.certifications)
        total_preferred = len(job_role.preferred_certifications)
        
        if total_required == 0 and total_preferred == 0:
            return 100.0
        
        required_score = (required_met / max(total_required, 1)) * 50 if total_required > 0 else 50
        preferred_score = (preferred_met / max(total_preferred, 1)) * 50 if total_preferred > 0 else 50
        
        return required_score + preferred_score

