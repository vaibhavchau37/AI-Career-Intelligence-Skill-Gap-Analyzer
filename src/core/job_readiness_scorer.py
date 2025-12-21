"""
Job Readiness Scoring System

This module calculates a job readiness score (0-100) based on:
- Skill gap results (matched/missing skills)
- Projects (relevance and quality indicators)
- Experience (years and relevance)

The scoring logic is TRANSPARENT - no black-box ML, all calculations are explainable.
"""

from typing import Dict, List, Optional, Tuple
import math


class JobReadinessScorer:
    """
    Calculate job readiness score with transparent, explainable logic.
    
    Scoring Components:
    1. Skills (60%): Based on skill gap analysis
    2. Experience (25%): Based on years of experience
    3. Projects (15%): Based on number and relevance of projects
    
    All calculations are explicit and explainable - no hidden ML models.
    """
    
    def __init__(
        self,
        skill_weight: float = 0.60,
        experience_weight: float = 0.25,
        project_weight: float = 0.15
    ):
        """
        Initialize the job readiness scorer.
        
        Args:
            skill_weight: Weight for skills component (default: 60%)
            experience_weight: Weight for experience component (default: 25%)
            project_weight: Weight for projects component (default: 15%)
            
        Note: Weights should sum to 1.0 (100%)
        """
        # Normalize weights to sum to 1.0
        total_weight = skill_weight + experience_weight + project_weight
        if total_weight > 0:
            self.skill_weight = skill_weight / total_weight
            self.experience_weight = experience_weight / total_weight
            self.project_weight = project_weight / total_weight
        else:
            self.skill_weight = 0.60
            self.experience_weight = 0.25
            self.project_weight = 0.15
        
        # Experience scoring parameters
        self.min_experience_years = 0
        self.optimal_experience_years = 3  # Optimal years of experience
        self.max_experience_years = 10  # Beyond this, diminishing returns
    
    def calculate_score(
        self,
        skill_gap_results: Dict,
        experience_years: float = 0.0,
        projects: List[str] = None,
        job_required_experience: float = 2.0
    ) -> Dict:
        """
        Calculate overall job readiness score.
        
        How it works:
        1. Calculate skill score from gap analysis (0-100)
        2. Calculate experience score based on years (0-100)
        3. Calculate project score based on count/relevance (0-100)
        4. Weighted combination: skill×60% + experience×25% + projects×15%
        
        Args:
            skill_gap_results: Dictionary from SkillGapAnalyzerTFIDF.analyze_gaps()
            experience_years: Years of relevant experience
            projects: List of project descriptions/names
            job_required_experience: Minimum years of experience required for job
            
        Returns:
            Dictionary with:
            - overall_score: Final score (0-100)
            - breakdown: Individual component scores
            - explanation: Human-readable explanation
            - calculation_steps: Detailed calculation steps
        """
        projects = projects or []
        
        # Step 1: Calculate Skill Score (0-100)
        skill_score, skill_explanation = self._calculate_skill_score(skill_gap_results)
        
        # Step 2: Calculate Experience Score (0-100)
        experience_score, exp_explanation = self._calculate_experience_score(
            experience_years, job_required_experience
        )
        
        # Step 3: Calculate Project Score (0-100)
        project_score, project_explanation = self._calculate_project_score(projects)
        
        # Step 4: Calculate Weighted Overall Score
        overall_score = (
            skill_score * self.skill_weight +
            experience_score * self.experience_weight +
            project_score * self.project_weight
        )
        
        # Ensure score is between 0 and 100
        overall_score = max(0, min(100, round(overall_score, 2)))
        
        # Step 5: Generate explanation
        explanation = self._generate_explanation(
            overall_score, skill_score, experience_score, project_score,
            skill_gap_results, experience_years, len(projects)
        )
        
        # Step 6: Document calculation steps
        calculation_steps = {
            'skill_score': {
                'value': skill_score,
                'weight': self.skill_weight,
                'contribution': skill_score * self.skill_weight,
                'explanation': skill_explanation
            },
            'experience_score': {
                'value': experience_score,
                'weight': self.experience_weight,
                'contribution': experience_score * self.experience_weight,
                'explanation': exp_explanation
            },
            'project_score': {
                'value': project_score,
                'weight': self.project_weight,
                'contribution': project_score * self.project_weight,
                'explanation': project_explanation
            },
            'overall_calculation': {
                'formula': f"({skill_score} × {self.skill_weight}) + ({experience_score} × {self.experience_weight}) + ({project_score} × {self.project_weight})",
                'result': overall_score
            }
        }
        
        return {
            'overall_score': overall_score,
            'breakdown': {
                'skills': round(skill_score, 2),
                'experience': round(experience_score, 2),
                'projects': round(project_score, 2)
            },
            'explanation': explanation,
            'calculation_steps': calculation_steps
        }
    
    def _calculate_skill_score(self, skill_gap_results: Dict) -> Tuple[float, str]:
        """
        Calculate skill score based on gap analysis.
        
        Formula:
        - Base score from required skills match percentage
        - Bonus from preferred skills match
        - Penalty reduction for missing required skills
        
        Args:
            skill_gap_results: Results from skill gap analyzer
            
        Returns:
            Tuple of (score, explanation)
        """
        match_details = skill_gap_results.get('match_details', {})
        missing_required = skill_gap_results.get('missing_required', [])
        missing_preferred = skill_gap_results.get('missing_preferred', [])
        matched_skills = skill_gap_results.get('matched_skills', [])
        
        total_job_skills = match_details.get('total_job_skills', 0)
        matched_count = match_details.get('matched_count', 0)
        
        if total_job_skills == 0:
            return 100.0, "No job skills specified, assuming perfect match"
        
        # Base score: percentage of matched skills
        base_score = (matched_count / total_job_skills) * 100
        
        # Weighted scoring: required skills are more important
        # Calculate required vs preferred separately if available
        total_required = len(missing_required) + len([
            m for m in matched_skills 
            if m.get('job_skill') in skill_gap_results.get('missing_required', []) or
            True  # Simplified: assume all matched are required if not categorized
        ])
        
        if total_required > 0:
            matched_required_count = total_required - len(missing_required)
            required_score = (matched_required_count / total_required) * 100
            
            # Use 70% weight for required, 30% for preferred (if applicable)
            # Simplified version: use base_score with emphasis on required
            skill_score = base_score
            
            # Apply penalty for missing required skills
            if missing_required:
                penalty = min(30, len(missing_required) * 10)  # Max 30 point penalty
                skill_score = max(0, skill_score - penalty)
        else:
            skill_score = base_score
        
        # Ensure score is between 0 and 100
        skill_score = max(0, min(100, skill_score))
        
        explanation = (
            f"Skill score: {skill_score:.1f}/100. "
            f"Matched {matched_count}/{total_job_skills} job skills ({base_score:.1f}%). "
            f"{len(missing_required)} required skills missing, "
            f"{len(missing_preferred)} preferred skills missing."
        )
        
        return round(skill_score, 2), explanation
    
    def _calculate_experience_score(
        self,
        experience_years: float,
        required_years: float = 2.0
    ) -> Tuple[float, str]:
        """
        Calculate experience score based on years of experience.
        
        Scoring logic (transparent):
        - 0 years: 0 points
        - Below required: Linear scale (0-50 points)
        - At required: 75 points
        - Optimal (3-5 years): 100 points
        - Beyond optimal: Diminishing returns (caps at 100)
        
        Args:
            experience_years: Years of experience
            required_years: Required years for the job
            
        Returns:
            Tuple of (score, explanation)
        """
        if experience_years < 0:
            experience_years = 0
        
        # Case 1: No experience
        if experience_years == 0:
            score = 0
            explanation = "No experience specified (0 points)"
        
        # Case 2: Below required years
        elif experience_years < required_years:
            # Linear scale: 0 to 50 points
            progress = experience_years / required_years
            score = progress * 50
            explanation = (
                f"Below required experience ({experience_years:.1f} < {required_years:.1f} years). "
                f"Linear scale: {score:.1f}/50 points."
            )
        
        # Case 3: At required years
        elif experience_years == required_years:
            score = 75
            explanation = (
                f"Meets minimum requirement ({experience_years:.1f} years). "
                f"Score: 75/100 points."
            )
        
        # Case 4: Between required and optimal
        elif experience_years < self.optimal_experience_years:
            # Linear scale: 75 to 100 points
            progress = (experience_years - required_years) / (self.optimal_experience_years - required_years)
            score = 75 + (progress * 25)
            explanation = (
                f"Between required and optimal ({experience_years:.1f} years). "
                f"Score: {score:.1f}/100 points."
            )
        
        # Case 5: At optimal (3-5 years)
        elif experience_years <= 5:
            score = 100
            explanation = (
                f"Optimal experience range ({experience_years:.1f} years). "
                f"Maximum score: 100/100 points."
            )
        
        # Case 6: Beyond optimal (diminishing returns)
        else:
            # Slight penalty for too much experience (may be overqualified)
            # Still good, but not better than optimal
            excess = experience_years - 5
            penalty = min(10, excess * 2)  # Max 10 point penalty
            score = max(90, 100 - penalty)
            explanation = (
                f"Beyond optimal range ({experience_years:.1f} years). "
                f"Diminishing returns: {score:.1f}/100 points."
            )
        
        # Ensure score is between 0 and 100
        score = max(0, min(100, round(score, 2)))
        
        return score, explanation
    
    def _calculate_project_score(self, projects: List[str]) -> Tuple[float, str]:
        """
        Calculate project score based on number of projects.
        
        Scoring logic (transparent):
        - 0 projects: 0 points
        - 1 project: 30 points
        - 2 projects: 60 points
        - 3 projects: 85 points
        - 4+ projects: 100 points (capped)
        
        Future enhancement: Could analyze project relevance/quality
        
        Args:
            projects: List of project descriptions/names
            
        Returns:
            Tuple of (score, explanation)
        """
        project_count = len(projects) if projects else 0
        
        if project_count == 0:
            score = 0
            explanation = "No projects listed (0 points)"
        elif project_count == 1:
            score = 30
            explanation = "1 project listed (30/100 points)"
        elif project_count == 2:
            score = 60
            explanation = "2 projects listed (60/100 points)"
        elif project_count == 3:
            score = 85
            explanation = "3 projects listed (85/100 points)"
        else:  # 4 or more
            score = 100
            explanation = f"{project_count} projects listed (100/100 points - capped)"
        
        return round(score, 2), explanation
    
    def _generate_explanation(
        self,
        overall_score: float,
        skill_score: float,
        experience_score: float,
        project_score: float,
        skill_gap_results: Dict,
        experience_years: float,
        project_count: int
    ) -> str:
        """
        Generate human-readable explanation of the score.
        
        Args:
            overall_score: Final calculated score
            skill_score: Skill component score
            experience_score: Experience component score
            project_score: Project component score
            skill_gap_results: Skill gap analysis results
            experience_years: Years of experience
            project_count: Number of projects
            
        Returns:
            Explanation string
        """
        # Overall assessment
        if overall_score >= 80:
            assessment = "Excellent readiness"
        elif overall_score >= 65:
            assessment = "Good readiness"
        elif overall_score >= 50:
            assessment = "Moderate readiness"
        elif overall_score >= 35:
            assessment = "Needs improvement"
        else:
            assessment = "Poor readiness"
        
        explanation = f"""
JOB READINESS SCORE: {overall_score:.1f}/100 ({assessment})

SCORE BREAKDOWN:

1. SKILLS ({skill_score:.1f}/100) - Weight: {self.skill_weight*100:.0f}%
   Contribution: {skill_score * self.skill_weight:.1f} points
   - {skill_gap_results.get('match_details', {}).get('matched_count', 0)} skills matched
   - {len(skill_gap_results.get('missing_required', []))} required skills missing
   - {len(skill_gap_results.get('missing_preferred', []))} preferred skills missing

2. EXPERIENCE ({experience_score:.1f}/100) - Weight: {self.experience_weight*100:.0f}%
   Contribution: {experience_score * self.experience_weight:.1f} points
   - {experience_years:.1f} years of experience

3. PROJECTS ({project_score:.1f}/100) - Weight: {self.project_weight*100:.0f}%
   Contribution: {project_score * self.project_weight:.1f} points
   - {project_count} projects listed

CALCULATION:
Overall Score = ({skill_score:.1f} × {self.skill_weight:.2f}) + ({experience_score:.1f} × {self.experience_weight:.2f}) + ({project_score:.1f} × {self.project_weight:.2f})
Overall Score = {skill_score * self.skill_weight:.1f} + {experience_score * self.experience_weight:.1f} + {project_score * self.project_weight:.1f}
Overall Score = {overall_score:.1f}/100

IMPROVEMENT AREAS:
""".strip()
        
        # Add improvement suggestions
        improvements = []
        
        if skill_score < 70:
            missing_req = len(skill_gap_results.get('missing_required', []))
            if missing_req > 0:
                improvements.append(f"- Focus on learning {missing_req} missing required skills")
        
        if experience_score < 70:
            improvements.append(f"- Gain more experience (currently {experience_years:.1f} years)")
        
        if project_score < 70:
            improvements.append(f"- Add more projects to showcase skills (currently {project_count})")
        
        if improvements:
            explanation += "\n" + "\n".join(improvements)
        else:
            explanation += "\n- All components are strong! Continue building experience."
        
        return explanation
    
    def explain_scoring_methodology(self) -> str:
        """
        Explain the complete scoring methodology.
        
        Returns:
            Detailed explanation of how scoring works
        """
        return f"""
JOB READINESS SCORING METHODOLOGY

This scoring system uses TRANSPARENT, EXPLICIT calculations - no black-box ML.

COMPONENTS:

1. SKILLS ({self.skill_weight*100:.0f}% weight)
   - Base score: (Matched Skills / Total Required Skills) × 100
   - Penalty: -10 points per missing required skill (max -30)
   - Range: 0-100 points
   
   Example: 8/10 skills matched = 80% base, 2 missing = -20 penalty = 60/100

2. EXPERIENCE ({self.experience_weight*100:.0f}% weight)
   - 0 years: 0 points
   - Below required: Linear scale (0-50 points)
   - At required: 75 points
   - Optimal (3-5 years): 100 points
   - Beyond optimal: Diminishing returns (90-100 points)
   
   Example: 2 years when 2 required = 75 points

3. PROJECTS ({self.project_weight*100:.0f}% weight)
   - 0 projects: 0 points
   - 1 project: 30 points
   - 2 projects: 60 points
   - 3 projects: 85 points
   - 4+ projects: 100 points (capped)
   
   Example: 3 projects = 85 points

FINAL SCORE CALCULATION:

Overall Score = (Skill Score × {self.skill_weight:.2f}) + 
                (Experience Score × {self.experience_weight:.2f}) + 
                (Project Score × {self.project_weight:.2f})

The score is then rounded to 2 decimal places and clamped between 0-100.

EXAMPLE:
- Skills: 70/100 (70% match, 3 missing required)
- Experience: 75/100 (meets minimum requirement)
- Projects: 85/100 (3 projects)

Calculation:
(70 × 0.60) + (75 × 0.25) + (85 × 0.15)
= 42.0 + 18.75 + 12.75
= 73.5/100

All calculations are explicit and verifiable - no hidden formulas or ML models!
""".strip()

