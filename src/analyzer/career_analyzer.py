"""Main career analyzer orchestrator."""

import yaml
import os
from pathlib import Path
from typing import List, Optional, Dict
from src.models.resume import Resume
from src.models.job_role import JobRole
from src.models.analysis_result import AnalysisResult, RoleScore, SkillGap, LearningPath
from src.core.resume_parser import ResumeParser
from src.core.skill_extractor import SkillExtractor
from src.core.skill_matcher import SkillMatcher
from src.core.score_calculator import ScoreCalculator
from src.matcher.job_matcher import JobMatcher
from src.matcher.role_predictor import RolePredictor
from src.roadmap.skill_gaps import SkillGapAnalyzer
from src.roadmap.roadmap_generator import RoadmapGenerator
from src.utils.explainer import generate_score_explanation


class CareerAnalyzer:
    """Main orchestrator for career analysis."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize career analyzer.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize core components
        self.resume_parser = ResumeParser()
        self.skill_extractor = SkillExtractor(
            skill_taxonomy_path=self.config.get('skills', {}).get('taxonomy_path'),
            skill_synonyms_path=self.config.get('skills', {}).get('synonyms_path'),
        )
        self.skill_matcher = SkillMatcher(
            similarity_threshold=self.config.get('skill_matching', {}).get('similarity_threshold', 0.8),
            fuzzy_threshold=self.config.get('skill_matching', {}).get('fuzzy_threshold', 85),
        )
        self.score_calculator = ScoreCalculator(self.config)
        self.job_matcher = JobMatcher(self.config)
        self.role_predictor = RolePredictor()
        self.skill_gap_analyzer = SkillGapAnalyzer()
        self.roadmap_generator = RoadmapGenerator(
            default_timeline_days=self.config.get('roadmap', {}).get('default_timeline_days', 90)
        )
        
        # Load job roles
        self.job_roles = self._load_job_roles()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _load_job_roles(self) -> List[JobRole]:
        """Load job roles from data directory."""
        job_roles = []
        roles_path = self.config.get('job_roles', {}).get('data_path', 'data/job_roles')
        
        if not os.path.exists(roles_path):
            # Return default job roles if directory doesn't exist
            return self._get_default_job_roles()
        
        # Load YAML files from job_roles directory
        for yaml_file in Path(roles_path).glob('*.yaml'):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    role_data = yaml.safe_load(f)
                    if role_data:
                        job_role = self._job_role_from_dict(role_data)
                        job_roles.append(job_role)
            except Exception as e:
                print(f"Error loading job role from {yaml_file}: {e}")
        
        return job_roles if job_roles else self._get_default_job_roles()
    
    def _job_role_from_dict(self, data: Dict) -> JobRole:
        """Create JobRole object from dictionary."""
        from src.models.job_role import SkillRequirement
        
        # Convert skill lists to SkillRequirement objects
        required_skills = [
            SkillRequirement(
                skill=skill if isinstance(skill, str) else skill.get('name', ''),
                required=True,
                importance=skill.get('importance', 1.0) if isinstance(skill, dict) else 1.0,
                description=skill.get('description') if isinstance(skill, dict) else None,
            )
            for skill in data.get('required_skills', [])
        ]
        
        preferred_skills = [
            SkillRequirement(
                skill=skill if isinstance(skill, str) else skill.get('name', ''),
                required=False,
                importance=skill.get('importance', 0.7) if isinstance(skill, dict) else 0.7,
                description=skill.get('description') if isinstance(skill, dict) else None,
            )
            for skill in data.get('preferred_skills', [])
        ]
        
        return JobRole(
            name=data.get('name', ''),
            description=data.get('description', ''),
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            min_years_experience=data.get('min_years_experience', 0.0),
            preferred_years_experience=data.get('preferred_years_experience', 2.0),
            required_degrees=data.get('required_degrees', []),
            preferred_degrees=data.get('preferred_degrees', []),
            certifications=data.get('certifications', []),
            preferred_certifications=data.get('preferred_certifications', []),
        )
    
    def _get_default_job_roles(self) -> List[JobRole]:
        """Get default job roles if none are loaded."""
        from src.models.job_role import SkillRequirement
        
        # Simple default roles - users should create proper YAML files
        ml_engineer = JobRole(
            name="ML Engineer",
            description="Machine Learning Engineer responsible for building and deploying ML models",
            required_skills=[
                SkillRequirement("Python", required=True, importance=1.0),
                SkillRequirement("Machine Learning", required=True, importance=1.0),
                SkillRequirement("Deep Learning", required=True, importance=0.9),
            ],
            preferred_skills=[
                SkillRequirement("TensorFlow", required=False, importance=0.8),
                SkillRequirement("PyTorch", required=False, importance=0.8),
                SkillRequirement("AWS", required=False, importance=0.7),
            ],
            min_years_experience=2.0,
            preferred_years_experience=3.0,
        )
        
        return [ml_engineer]
    
    def analyze(
        self,
        resume_text: str,
        target_roles: Optional[List[str]] = None
    ) -> AnalysisResult:
        """
        Analyze resume and generate comprehensive results.
        
        Args:
            resume_text: Raw resume text
            target_roles: List of target job role names (if None, uses all available roles)
            
        Returns:
            AnalysisResult object with complete analysis
        """
        # Parse resume
        resume = self.resume_parser.parse(resume_text)
        
        # Extract skills
        extracted_skills = self.skill_extractor.extract_skills(resume)
        resume.technical_skills = extracted_skills
        resume.skills = extracted_skills
        
        # Filter job roles if target_roles specified
        roles_to_analyze = self.job_roles
        if target_roles:
            roles_to_analyze = [r for r in self.job_roles if r.name in target_roles]
        
        if not roles_to_analyze:
            roles_to_analyze = self.job_roles
        
        # Analyze against each role
        result = AnalysisResult(resume_name=resume.name)
        resume_skills = resume.get_all_skills()
        
        for job_role in roles_to_analyze:
            # Match skills
            skill_match_result = self.skill_matcher.match_skills(resume_skills, job_role)
            
            # Calculate score
            score_result = self.score_calculator.calculate_score(
                resume, job_role, skill_match_result
            )
            
            # Analyze skill gaps
            skill_gaps = self.skill_gap_analyzer.analyze_gaps(resume_skills, job_role)
            result.skill_gaps[job_role.name] = skill_gaps
            
            # Generate roadmap
            roadmap = self.roadmap_generator.generate_roadmap(skill_gaps)
            result.roadmaps[job_role.name] = roadmap
            
            # Create role score object
            role_score = RoleScore(
                role_name=job_role.name,
                overall_score=score_result['overall_score'],
                breakdown=score_result['breakdown'],
                explanation=generate_score_explanation(
                    RoleScore(
                        role_name=job_role.name,
                        overall_score=score_result['overall_score'],
                        breakdown=score_result['breakdown'],
                        explanation="",
                        matched_skills=skill_match_result['matched_required'] + skill_match_result['matched_preferred'],
                        missing_skills=skill_gaps,
                    )
                ),
                matched_skills=skill_match_result['matched_required'] + skill_match_result['matched_preferred'],
                missing_skills=skill_gaps,
                experience_score=score_result['breakdown']['experience'],
                education_score=score_result['breakdown']['education'],
                skill_score=(score_result['breakdown']['required_skills'] + score_result['breakdown']['preferred_skills']) / 2,
            )
            
            result.scores[job_role.name] = role_score
        
        # Get top roles
        job_matches = self.job_matcher.match_roles(
            resume,
            roles_to_analyze,
            top_n=self.config.get('output', {}).get('top_n_roles', 5)
        )
        result.top_roles = [match['role_name'] for match in job_matches]
        
        # Predict additional roles
        result.predicted_roles = self.role_predictor.predict_roles(
            resume,
            self.job_roles,
            top_n=3
        )
        
        # Generate summary
        result.summary = self._generate_summary(result)
        
        return result
    
    def _generate_summary(self, result: AnalysisResult) -> str:
        """Generate summary text for analysis result."""
        if not result.top_roles:
            return "No suitable roles found."
        
        top_role = result.top_roles[0]
        top_score = result.get_role_score(top_role) or 0.0
        
        summary = f"Top Recommendation: {top_role} (Score: {top_score:.1f}/100)\n\n"
        
        if len(result.top_roles) > 1:
            summary += f"Other suitable roles: {', '.join(result.top_roles[1:3])}\n\n"
        
        if result.predicted_roles:
            summary += f"Consider exploring: {', '.join(result.predicted_roles[:2])}\n"
        
        return summary

