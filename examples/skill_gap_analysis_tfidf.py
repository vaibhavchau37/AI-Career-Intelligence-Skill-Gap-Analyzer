"""
Example: Skill Gap Analysis using TF-IDF + Cosine Similarity

This script demonstrates how to use the TF-IDF-based skill gap analyzer
to identify matched, missing, and extra skills.

Usage:
    python examples/skill_gap_analysis_tfidf.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.skill_gap_analyzer_tfidf import SkillGapAnalyzerTFIDF


def main():
    """
    Demonstrate TF-IDF-based skill gap analysis.
    """
    print("=" * 70)
    print("Skill Gap Analysis using TF-IDF + Cosine Similarity")
    print("=" * 70)
    print()
    
    # Step 1: Initialize analyzer
    print("Initializing TF-IDF Skill Gap Analyzer...")
    analyzer = SkillGapAnalyzerTFIDF(similarity_threshold=0.3)
    print("✓ Analyzer initialized")
    print(f"  Similarity Threshold: {analyzer.similarity_threshold}")
    print()
    
    # Step 2: Example data
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
        "Kubernetes",
        "MLOps"
    ]
    
    all_job_skills = job_required_skills + job_preferred_skills
    
    print("📄 INPUT DATA:")
    print("-" * 70)
    print(f"Resume Skills ({len(resume_skills)}):")
    for skill in resume_skills:
        print(f"  • {skill}")
    print()
    
    print(f"Job Required Skills ({len(job_required_skills)}):")
    for skill in job_required_skills:
        print(f"  • {skill}")
    print()
    
    print(f"Job Preferred Skills ({len(job_preferred_skills)}):")
    for skill in job_preferred_skills:
        print(f"  • {skill}")
    print()
    
    # Step 3: Perform analysis
    print("🔍 ANALYZING SKILL GAPS...")
    print("-" * 70)
    
    results = analyzer.analyze_gaps(
        resume_skills=resume_skills,
        job_role_skills=all_job_skills,
        required_skills=job_required_skills,
        preferred_skills=job_preferred_skills
    )
    
    # Step 4: Display results
    print("\n" + "=" * 70)
    print("📊 ANALYSIS RESULTS")
    print("=" * 70)
    print()
    
    # Matched skills
    matched_skills = results['matched_skills']
    print(f"✅ MATCHED SKILLS ({len(matched_skills)}):")
    print("-" * 70)
    if matched_skills:
        for match in matched_skills:
            print(f"  Resume: '{match['resume_skill']}' ↔ Job: '{match['job_skill']}'")
            print(f"    Similarity: {match['similarity']:.3f} {'(HIGH)' if match['similarity'] > 0.7 else '(MEDIUM)' if match['similarity'] > 0.4 else '(LOW)'}")
            print()
    else:
        print("  No skills matched above threshold")
        print()
    
    # Missing required skills
    missing_required = results['missing_required']
    print(f"❌ MISSING REQUIRED SKILLS ({len(missing_required)}):")
    print("-" * 70)
    if missing_required:
        for skill in missing_required:
            print(f"  • {skill}")
            # Show explanation if available
            if skill in results.get('explanations', {}):
                print(f"    → {results['explanations'][skill][:100]}...")
        print()
    else:
        print("  All required skills are matched! 🎉")
        print()
    
    # Missing preferred skills
    missing_preferred = results['missing_preferred']
    print(f"⚠️  MISSING PREFERRED SKILLS ({len(missing_preferred)}):")
    print("-" * 70)
    if missing_preferred:
        for skill in missing_preferred:
            print(f"  • {skill}")
        print()
    else:
        print("  All preferred skills are matched! ✨")
        print()
    
    # Extra skills (in resume but not in job)
    extra_skills = results['extra_skills']
    print(f"➕ EXTRA SKILLS ({len(extra_skills)}):")
    print("-" * 70)
    if extra_skills:
        print("  Skills in resume but not required for job:")
        for skill in extra_skills:
            print(f"  • {skill}")
        print("  (These are bonuses, not requirements)")
        print()
    else:
        print("  No extra skills")
        print()
    
    # Statistics
    match_details = results['match_details']
    print("📈 STATISTICS:")
    print("-" * 70)
    print(f"  Total Resume Skills: {match_details['total_resume_skills']}")
    print(f"  Total Job Skills: {match_details['total_job_skills']}")
    print(f"  Matched: {match_details['matched_count']}")
    print(f"  Missing: {match_details['missing_count']}")
    print(f"  Extra: {match_details['extra_count']}")
    print(f"  Match Percentage: {match_details['match_percentage']:.1f}%")
    print(f"  Average Similarity: {match_details['average_similarity']:.3f}")
    print()
    
    # Step 5: Show similarity examples
    print("=" * 70)
    print("🔬 SIMILARITY EXAMPLES")
    print("=" * 70)
    print()
    
    test_pairs = [
        ("Python", "Python"),
        ("Machine Learning", "ML"),
        ("Machine Learning", "Deep Learning"),
        ("TensorFlow", "PyTorch"),
        ("Python", "Java"),
        ("SQL", "Database"),
    ]
    
    print("Cosine Similarity between skill pairs:")
    print("-" * 70)
    for skill1, skill2 in test_pairs:
        similarity = analyzer.get_similarity_between_skills(skill1, skill2)
        status = "MATCH" if similarity >= analyzer.similarity_threshold else "NO MATCH"
        print(f"  '{skill1}' ↔ '{skill2}': {similarity:.3f} ({status})")
    print()
    
    # Step 6: Explanation
    print("=" * 70)
    print("📚 HOW IT WORKS")
    print("=" * 70)
    print()
    print(analyzer.explain_similarity_calculation())
    print()
    
    print("=" * 70)
    print("✅ Analysis Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

