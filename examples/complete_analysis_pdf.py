"""
Complete Analysis: Parse PDF Resume + Compare with Job Roles

This script demonstrates the complete workflow:
1. Parse a PDF resume
2. Extract skills
3. Compare with job role skill mappings
4. Generate analysis report

Usage:
    python examples/complete_analysis_pdf.py path/to/resume.pdf
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.pdf_resume_parser import PDFResumeParser
from examples.skill_mapping_comparison import SkillMappingComparator


def main():
    """
    Complete analysis: Parse PDF and compare with job roles.
    """
    print("=" * 70)
    print("Complete Resume Analysis: PDF Parsing + Job Role Comparison")
    print("=" * 70)
    print()
    
    # Step 1: Get PDF file path
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "data/examples/sample_resume.pdf"
        print(f"No PDF provided. Looking for: {pdf_path}")
        print("Usage: python examples/complete_analysis_pdf.py <path_to_pdf>")
        print()
    
    if not Path(pdf_path).exists():
        print(f"❌ Error: PDF not found: {pdf_path}")
        return
    
    # Step 2: Parse PDF Resume
    print("📄 Step 1: Parsing PDF Resume...")
    print("-" * 70)
    
    try:
        parser = PDFResumeParser()
        resume_data = parser.parse_pdf(pdf_path)
        
        print(f"✓ Resume parsed successfully!")
        print(f"  Name: {resume_data.get('name', 'N/A')}")
        print(f"  Skills Found: {len(resume_data.get('skills', []))}")
        print(f"  Education Entries: {len(resume_data.get('education', []))}")
        print(f"  Experience Entries: {len(resume_data.get('experience', []))}")
        print(f"  Projects: {len(resume_data.get('projects', []))}")
        print()
        
    except Exception as e:
        print(f"❌ Error parsing PDF: {e}")
        return
    
    # Step 3: Extract skills
    resume_skills = resume_data.get('skills', [])
    
    if not resume_skills:
        print("⚠️  Warning: No skills found in resume. Analysis may be limited.")
        print()
    
    # Step 4: Compare with Job Roles
    print("🔍 Step 2: Comparing Skills with Job Roles...")
    print("-" * 70)
    
    try:
        comparator = SkillMappingComparator()
        comparison_results = comparator.compare_all_roles(resume_skills)
        
        print(f"✓ Compared against {len(comparison_results)} job roles")
        print()
        
    except Exception as e:
        print(f"❌ Error comparing skills: {e}")
        return
    
    # Step 5: Display Results
    print("=" * 70)
    print("📊 ANALYSIS RESULTS")
    print("=" * 70)
    print()
    
    # Display resume summary
    print("📄 Resume Summary:")
    print("-" * 70)
    if resume_data.get('name'):
        print(f"Name: {resume_data['name']}")
    if resume_data.get('email'):
        print(f"Email: {resume_data['email']}")
    print(f"Total Skills: {len(resume_skills)}")
    print(f"Skills: {', '.join(resume_skills[:10])}")
    if len(resume_skills) > 10:
        print(f"... and {len(resume_skills) - 10} more")
    print()
    
    # Display job role comparisons
    print("🎯 Job Role Match Scores:")
    print("-" * 70)
    
    for i, result in enumerate(comparison_results, 1):
        role_name = result['role_name']
        overall_match = result['overall_match_percentage']
        required_match = result['required_match_percentage']
        
        # Visual indicator
        if overall_match >= 70:
            indicator = "🟢"
        elif overall_match >= 50:
            indicator = "🟡"
        else:
            indicator = "🔴"
        
        print(f"\n{i}. {indicator} {role_name}")
        print(f"   Overall Match: {overall_match:.1f}%")
        print(f"   Required Skills: {required_match:.1f}% ({len(result['matched_required'])}/{result['total_required_skills']})")
        
        # Show missing required skills (most important!)
        if result['missing_required']:
            print(f"   ⚠️  Missing Required: {', '.join(result['missing_required'][:5])}")
            if len(result['missing_required']) > 5:
                print(f"      ... and {len(result['missing_required']) - 5} more")
    
    # Step 6: Detailed Analysis for Top Match
    print("\n" + "=" * 70)
    top_match = comparison_results[0]
    print(f"🎯 BEST MATCH: {top_match['role_name']}")
    print("=" * 70)
    print()
    
    print(f"Overall Score: {top_match['overall_match_percentage']:.1f}%")
    print(f"Required Skills Match: {top_match['required_match_percentage']:.1f}%")
    print(f"Optional Skills Match: {top_match['optional_match_percentage']:.1f}%")
    print()
    
    # Matched skills
    if top_match['matched_required']:
        print("✅ Matched Required Skills:")
        for skill in top_match['matched_required']:
            print(f"   • {skill}")
        print()
    
    # Missing skills (most important!)
    if top_match['missing_required']:
        print("❌ Missing Required Skills (Priority to Learn):")
        for skill in top_match['missing_required']:
            print(f"   • {skill}")
        print()
    
    if top_match['matched_optional']:
        print("✅ Matched Optional Skills:")
        for skill in top_match['matched_optional'][:5]:
            print(f"   • {skill}")
        if len(top_match['matched_optional']) > 5:
            print(f"   ... and {len(top_match['matched_optional']) - 5} more")
        print()
    
    # Step 7: Save Results
    output_file = Path(pdf_path).stem + "_analysis.json"
    
    output_data = {
        "resume": {
            "name": resume_data.get('name'),
            "email": resume_data.get('email'),
            "skills": resume_skills,
        },
        "comparisons": comparison_results,
        "top_match": {
            "role": top_match['role_name'],
            "score": top_match['overall_match_percentage'],
            "missing_required": top_match['missing_required'],
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("=" * 70)
    print(f"✅ Analysis Complete!")
    print(f"📁 Results saved to: {output_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()

