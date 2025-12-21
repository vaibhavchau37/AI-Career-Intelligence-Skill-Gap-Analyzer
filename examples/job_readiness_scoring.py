"""
Example: Job Readiness Scoring System

This script demonstrates how to calculate job readiness scores
with transparent, explainable logic.

Usage:
    python examples/job_readiness_scoring.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.skill_gap_analyzer_tfidf import SkillGapAnalyzerTFIDF
from src.core.job_readiness_scorer import JobReadinessScorer


def main():
    """
    Demonstrate job readiness scoring.
    """
    print("=" * 70)
    print("Job Readiness Scoring System")
    print("=" * 70)
    print()
    
    # Step 1: Example data
    resume_skills = [
        "Python",
        "Machine Learning",
        "SQL",
        "Pandas",
        "NumPy",
        "Git",
        "Data Analysis"
    ]
    
    job_required_skills = [
        "Python",
        "Machine Learning",
        "Deep Learning",
        "Statistics",
        "SQL",
        "TensorFlow"
    ]
    
    job_preferred_skills = [
        "PyTorch",
        "AWS",
        "Docker"
    ]
    
    experience_years = 2.5
    projects = [
        "ML Model for Customer Prediction",
        "Data Pipeline for E-commerce",
        "Automated Reporting Dashboard"
    ]
    job_required_experience = 2.0
    
    print("📄 INPUT DATA:")
    print("-" * 70)
    print(f"Resume Skills: {len(resume_skills)} skills")
    print(f"Job Required Skills: {len(job_required_skills)} skills")
    print(f"Experience: {experience_years} years")
    print(f"Projects: {len(projects)} projects")
    print(f"Job Required Experience: {job_required_experience} years")
    print()
    
    # Step 2: Perform skill gap analysis
    print("🔍 Step 1: Analyzing Skill Gaps...")
    print("-" * 70)
    
    gap_analyzer = SkillGapAnalyzerTFIDF(similarity_threshold=0.3)
    skill_gap_results = gap_analyzer.analyze_gaps(
        resume_skills=resume_skills,
        job_role_skills=job_required_skills + job_preferred_skills,
        required_skills=job_required_skills,
        preferred_skills=job_preferred_skills
    )
    
    print(f"✓ Skill gap analysis complete")
    print(f"  Matched: {skill_gap_results['match_details']['matched_count']} skills")
    print(f"  Missing Required: {len(skill_gap_results['missing_required'])} skills")
    print(f"  Missing Preferred: {len(skill_gap_results['missing_preferred'])} skills")
    print()
    
    # Step 3: Calculate readiness score
    print("📊 Step 2: Calculating Job Readiness Score...")
    print("-" * 70)
    
    scorer = JobReadinessScorer(
        skill_weight=0.60,
        experience_weight=0.25,
        project_weight=0.15
    )
    
    score_results = scorer.calculate_score(
        skill_gap_results=skill_gap_results,
        experience_years=experience_years,
        projects=projects,
        job_required_experience=job_required_experience
    )
    
    # Step 4: Display results
    print("\n" + "=" * 70)
    print("🎯 JOB READINESS SCORE")
    print("=" * 70)
    print()
    
    overall_score = score_results['overall_score']
    breakdown = score_results['breakdown']
    
    # Visual score display
    score_bar_length = 50
    filled = int((overall_score / 100) * score_bar_length)
    bar = "█" * filled + "░" * (score_bar_length - filled)
    
    print(f"Overall Score: {overall_score:.1f}/100")
    print(f"[{bar}]")
    print()
    
    # Score breakdown
    print("SCORE BREAKDOWN:")
    print("-" * 70)
    
    print(f"\n1. SKILLS: {breakdown['skills']:.1f}/100 (60% weight)")
    calc_steps = score_results['calculation_steps']['skill_score']
    print(f"   Contribution: {calc_steps['contribution']:.1f} points")
    print(f"   {calc_steps['explanation']}")
    
    print(f"\n2. EXPERIENCE: {breakdown['experience']:.1f}/100 (25% weight)")
    calc_steps = score_results['calculation_steps']['experience_score']
    print(f"   Contribution: {calc_steps['contribution']:.1f} points")
    print(f"   {calc_steps['explanation']}")
    
    print(f"\n3. PROJECTS: {breakdown['projects']:.1f}/100 (15% weight)")
    calc_steps = score_results['calculation_steps']['project_score']
    print(f"   Contribution: {calc_steps['contribution']:.1f} points")
    print(f"   {calc_steps['explanation']}")
    
    print()
    
    # Detailed calculation
    print("DETAILED CALCULATION:")
    print("-" * 70)
    calc = score_results['calculation_steps']['overall_calculation']
    print(f"Formula: {calc['formula']}")
    print(f"Result: {calc['result']:.1f}/100")
    print()
    
    # Full explanation
    print("=" * 70)
    print("📝 FULL EXPLANATION")
    print("=" * 70)
    print()
    print(score_results['explanation'])
    print()
    
    # Step 5: Show methodology
    print("=" * 70)
    print("📚 SCORING METHODOLOGY")
    print("=" * 70)
    print()
    print(scorer.explain_scoring_methodology())
    print()
    
    # Step 6: Show improvement suggestions
    print("=" * 70)
    print("💡 IMPROVEMENT SUGGESTIONS")
    print("=" * 70)
    print()
    
    if breakdown['skills'] < 70:
        print("Skills Component:")
        print(f"  Current: {breakdown['skills']:.1f}/100")
        if skill_gap_results['missing_required']:
            print(f"  Action: Learn {len(skill_gap_results['missing_required'])} missing required skills:")
            for skill in skill_gap_results['missing_required'][:5]:
                print(f"    • {skill}")
        print()
    
    if breakdown['experience'] < 70:
        print("Experience Component:")
        print(f"  Current: {breakdown['experience']:.1f}/100 ({experience_years} years)")
        print(f"  Action: Gain more experience (target: {job_required_experience}+ years)")
        print()
    
    if breakdown['projects'] < 70:
        print("Projects Component:")
        print(f"  Current: {breakdown['projects']:.1f}/100 ({len(projects)} projects)")
        print(f"  Action: Add more projects (target: 3+ projects)")
        print()
    
    if all(score >= 70 for score in breakdown.values()):
        print("All components are strong! Continue building experience and skills.")
        print()
    
    print("=" * 70)
    print("✅ Analysis Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

