"""
Complete Skill Analysis: Gap Analysis + Readiness Scoring

This script demonstrates the complete workflow:
1. Skill gap analysis using TF-IDF + cosine similarity
2. Job readiness scoring with transparent calculations

Usage:
    python examples/complete_skill_analysis.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.skill_gap_analyzer_tfidf import SkillGapAnalyzerTFIDF
from src.core.job_readiness_scorer import JobReadinessScorer


def main():
    """
    Complete skill analysis workflow.
    """
    print("=" * 70)
    print("Complete Skill Analysis: Gap Analysis + Readiness Scoring")
    print("=" * 70)
    print()
    
    # Example data
    resume_skills = [
        "Python",
        "Machine Learning",
        "SQL",
        "Pandas",
        "NumPy",
        "Git",
        "Data Analysis",
        "Jupyter Notebooks"
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
        "Docker",
        "Kubernetes"
    ]
    
    experience_years = 2.5
    projects = [
        "ML Model for Customer Prediction using TensorFlow",
        "Data Pipeline for E-commerce Analytics",
        "Automated Reporting Dashboard with Python"
    ]
    job_required_experience = 2.0
    
    # Display input
    print("📄 INPUT DATA:")
    print("-" * 70)
    print(f"Resume Skills ({len(resume_skills)}): {', '.join(resume_skills[:5])}...")
    print(f"Job Required Skills ({len(job_required_skills)}): {', '.join(job_required_skills[:5])}...")
    print(f"Job Preferred Skills ({len(job_preferred_skills)}): {', '.join(job_preferred_skills)}")
    print(f"Experience: {experience_years} years")
    print(f"Projects: {len(projects)} projects")
    print(f"Job Required Experience: {job_required_experience} years")
    print()
    
    # Step 1: Skill Gap Analysis
    print("=" * 70)
    print("STEP 1: SKILL GAP ANALYSIS (TF-IDF + Cosine Similarity)")
    print("=" * 70)
    print()
    
    gap_analyzer = SkillGapAnalyzerTFIDF(similarity_threshold=0.3)
    skill_gap_results = gap_analyzer.analyze_gaps(
        resume_skills=resume_skills,
        job_role_skills=job_required_skills + job_preferred_skills,
        required_skills=job_required_skills,
        preferred_skills=job_preferred_skills
    )
    
    # Display gap analysis results
    print("✅ Matched Skills:")
    for match in skill_gap_results['matched_skills'][:5]:
        print(f"  '{match['resume_skill']}' ↔ '{match['job_skill']}' (similarity: {match['similarity']:.3f})")
    if len(skill_gap_results['matched_skills']) > 5:
        print(f"  ... and {len(skill_gap_results['matched_skills']) - 5} more")
    print()
    
    print(f"❌ Missing Required Skills ({len(skill_gap_results['missing_required'])}):")
    for skill in skill_gap_results['missing_required']:
        print(f"  • {skill}")
    print()
    
    print(f"⚠️  Missing Preferred Skills ({len(skill_gap_results['missing_preferred'])}):")
    for skill in skill_gap_results['missing_preferred'][:3]:
        print(f"  • {skill}")
    if len(skill_gap_results['missing_preferred']) > 3:
        print(f"  ... and {len(skill_gap_results['missing_preferred']) - 3} more")
    print()
    
    # Step 2: Job Readiness Scoring
    print("=" * 70)
    print("STEP 2: JOB READINESS SCORING")
    print("=" * 70)
    print()
    
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
    
    # Display score
    overall_score = score_results['overall_score']
    breakdown = score_results['breakdown']
    
    print(f"🎯 OVERALL JOB READINESS SCORE: {overall_score:.1f}/100")
    print()
    
    # Score breakdown
    print("Score Breakdown:")
    print("-" * 70)
    print(f"  Skills:      {breakdown['skills']:.1f}/100 (60% weight) → {breakdown['skills'] * 0.60:.1f} points")
    print(f"  Experience:  {breakdown['experience']:.1f}/100 (25% weight) → {breakdown['experience'] * 0.25:.1f} points")
    print(f"  Projects:    {breakdown['projects']:.1f}/100 (15% weight) → {breakdown['projects'] * 0.15:.1f} points")
    print(f"  ──────────────────────────────────────────────")
    print(f"  TOTAL:       {overall_score:.1f}/100")
    print()
    
    # Detailed calculation
    print("Calculation Details:")
    print("-" * 70)
    calc = score_results['calculation_steps']
    
    print("\nSkills Component:")
    print(f"  {calc['skill_score']['explanation']}")
    
    print("\nExperience Component:")
    print(f"  {calc['experience_score']['explanation']}")
    
    print("\nProjects Component:")
    print(f"  {calc['project_score']['explanation']}")
    
    print("\nOverall Formula:")
    print(f"  {calc['overall_calculation']['formula']}")
    print(f"  Result: {calc['overall_calculation']['result']:.1f}/100")
    print()
    
    # Step 3: Recommendations
    print("=" * 70)
    print("💡 RECOMMENDATIONS")
    print("=" * 70)
    print()
    
    if overall_score >= 80:
        print("🎉 Excellent readiness! You're well-prepared for this role.")
    elif overall_score >= 65:
        print("✅ Good readiness. Minor improvements could strengthen your candidacy.")
    elif overall_score >= 50:
        print("⚠️  Moderate readiness. Focus on key improvement areas.")
    else:
        print("📚 Needs improvement. Significant skill gaps to address.")
    
    print()
    
    # Specific recommendations
    recommendations = []
    
    if breakdown['skills'] < 70:
        recommendations.append("SKILLS:")
        recommendations.append(f"  • Learn {len(skill_gap_results['missing_required'])} missing required skills")
        for skill in skill_gap_results['missing_required'][:3]:
            recommendations.append(f"    - {skill}")
        recommendations.append("")
    
    if breakdown['experience'] < 70:
        recommendations.append("EXPERIENCE:")
        recommendations.append(f"  • Current: {experience_years} years")
        recommendations.append(f"  • Target: {job_required_experience}+ years")
        recommendations.append("  • Consider internships, projects, or entry-level roles")
        recommendations.append("")
    
    if breakdown['projects'] < 70:
        recommendations.append("PROJECTS:")
        recommendations.append(f"  • Current: {len(projects)} projects")
        recommendations.append(f"  • Target: 3+ projects")
        recommendations.append("  • Add more projects demonstrating relevant skills")
        recommendations.append("")
    
    if recommendations:
        print("\n".join(recommendations))
    else:
        print("All components are strong! Continue building your portfolio.")
        print()
    
    # Step 4: Summary
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print()
    print(f"Job Readiness Score: {overall_score:.1f}/100")
    print(f"Skills Match: {skill_gap_results['match_details']['match_percentage']:.1f}%")
    print(f"Missing Required Skills: {len(skill_gap_results['missing_required'])}")
    print(f"Experience Level: {experience_years} years ({breakdown['experience']:.1f}/100)")
    print(f"Projects: {len(projects)} ({breakdown['projects']:.1f}/100)")
    print()
    
    print("=" * 70)
    print("✅ Analysis Complete!")
    print("=" * 70)
    print()
    print("For detailed explanations, see:")
    print("  - docs/SIMILARITY_AND_SCORING_EXPLAINED.md")
    print("  - Run: python examples/skill_gap_analysis_tfidf.py")
    print("  - Run: python examples/job_readiness_scoring.py")


if __name__ == "__main__":
    main()

