"""
Example script: Analyze a resume against job roles.

This script demonstrates how to use the CareerAnalyzer to analyze a resume.
"""

from pathlib import Path
from src.analyzer.career_analyzer import CareerAnalyzer


def main():
    """Main function to analyze a resume."""
    
    print("=" * 60)
    print("AI Career Intelligence & Skill Gap Analyzer")
    print("=" * 60)
    print()
    
    # Initialize analyzer
    print("Initializing analyzer...")
    analyzer = CareerAnalyzer()
    
    # Load sample resume
    resume_path = Path("data/examples/sample_resume.txt")
    if not resume_path.exists():
        print(f"Error: Sample resume not found at {resume_path}")
        print("Please provide a resume text file.")
        return
    
    with open(resume_path, 'r', encoding='utf-8') as f:
        resume_text = f.read()
    
    print(f"Loaded resume: {resume_path}")
    print()
    
    # Analyze resume
    print("Analyzing resume...")
    print("-" * 60)
    
    # You can specify target roles, or analyze against all roles
    target_roles = ["ML Engineer", "Data Scientist"]  # Optional
    
    result = analyzer.analyze(
        resume_text=resume_text,
        target_roles=target_roles  # None to analyze all roles
    )
    
    # Display results
    print("\nANALYSIS RESULTS")
    print("=" * 60)
    print()
    
    # Summary
    print("SUMMARY")
    print("-" * 60)
    print(result.summary)
    print()
    
    # Top roles
    print("TOP RECOMMENDED ROLES")
    print("-" * 60)
    for i, role_name in enumerate(result.top_roles, 1):
        score = result.get_role_score(role_name)
        print(f"{i}. {role_name}: {score:.1f}/100")
    print()
    
    # Detailed scores
    print("DETAILED SCORES")
    print("-" * 60)
    for role_name, role_score in result.scores.items():
        print(f"\n{role_name}:")
        print(f"  Overall Score: {role_score.overall_score:.1f}/100")
        print(f"  Breakdown:")
        for category, score in role_score.breakdown.items():
            print(f"    - {category.replace('_', ' ').title()}: {score:.1f}/100")
        
        print(f"\n  Matched Skills ({len(role_score.matched_skills)}):")
        if role_score.matched_skills:
            print(f"    {', '.join(role_score.matched_skills[:10])}")
            if len(role_score.matched_skills) > 10:
                print(f"    ... and {len(role_score.matched_skills) - 10} more")
        
        print(f"\n  Missing Skills ({len(role_score.missing_skills)}):")
        if role_score.missing_skills:
            for gap in role_score.missing_skills[:5]:
                print(f"    - {gap.skill} ({gap.category})")
            if len(role_score.missing_skills) > 5:
                print(f"    ... and {len(role_score.missing_skills) - 5} more")
        
        # Explanation
        print(f"\n  Explanation:")
        print(f"  {role_score.explanation}")
    
    # Learning roadmaps
    print("\n" + "=" * 60)
    print("LEARNING ROADMAPS")
    print("=" * 60)
    
    for role_name, roadmap in result.roadmaps.items():
        if roadmap:
            print(f"\n{role_name} - Learning Roadmap:")
            print("-" * 60)
            total_days = sum(item.estimated_days for item in roadmap)
            print(f"Total estimated time: {total_days} days (~{total_days/30:.1f} months)\n")
            
            for i, path_item in enumerate(roadmap[:10], 1):  # Show top 10
                print(f"{i}. {path_item.skill} (Priority: {path_item.priority})")
                print(f"   Estimated: {path_item.estimated_days} days")
                if path_item.resources:
                    print(f"   Resources: {path_item.resources[0]}")
                if path_item.prerequisites:
                    print(f"   Prerequisites: {', '.join(path_item.prerequisites)}")
                print()
    
    print("=" * 60)
    print("Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

