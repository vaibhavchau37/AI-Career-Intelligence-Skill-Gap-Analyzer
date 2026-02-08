"""
Demo script to test the enhanced project with extracted LinkedIn data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.pdf_resume_parser import PDFResumeParser
from src.core.skill_gap_analyzer_tfidf import SkillGapAnalyzerTFIDF
from src.core.job_readiness_scorer import JobReadinessScorer
from src.matcher.role_suitability_predictor import RoleSuitabilityPredictor
from src.api.job_market_analyzer import JobMarketAnalyzer
import yaml
import json

def load_job_role(role_name):
    """Load job role from YAML file"""
    role_file = f"data/job_roles/{role_name.lower().replace(' ', '_')}.yaml"
    try:
        with open(role_file, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Job role file not found: {role_file}")
        return None

def demo_analysis():
    print("="*70)
    print(" AI CAREER INTELLIGENCE - DEMO WITH LINKEDIN DATA")
    print("="*70)
    
    # Load extracted data
    print("\n📊 Loading Extracted LinkedIn Data...")
    with open('data/extracted_job_titles.json', 'r') as f:
        job_titles_data = json.load(f)
    
    with open('data/extracted_skills.json', 'r') as f:
        skills_data = json.load(f)
    
    print(f"✓ Loaded {job_titles_data['total_titles']} unique job titles")
    print(f"✓ Loaded {skills_data['total_skills']} unique skills")
    
    # Show top job roles available
    print("\n" + "="*70)
    print("📋 TOP JOB ROLES FROM LINKEDIN DATA:")
    print("="*70)
    for i, title_info in enumerate(job_titles_data['titles_by_frequency'][:10], 1):
        print(f"{i:2d}. {title_info['title']:40s} ({title_info['count']:3d} jobs)")
    
    # Show top skills
    print("\n" + "="*70)
    print("💡 TOP SKILLS FROM LINKEDIN DATA:")
    print("="*70)
    for i, skill_info in enumerate(skills_data['skills_by_frequency'][:15], 1):
        print(f"{i:2d}. {skill_info['skill']:30s} ({skill_info['count']:3d} jobs)")
    
    # Test with available job roles
    available_roles = [
        'data_scientist',
        'ml_engineer',
        'software_engineer',
        'web_developer',
        'product_manager',
        'financial_analyst',
        'business_development_manager'
    ]
    
    print("\n" + "="*70)
    print("🎯 AVAILABLE JOB ROLE PROFILES:")
    print("="*70)
    for i, role in enumerate(available_roles, 1):
        role_data = load_job_role(role)
        if role_data:
            print(f"{i}. {role_data['name']}")
            print(f"   Description: {role_data['description'][:80]}...")
    
    # Sample analysis
    print("\n" + "="*70)
    print("🔍 SAMPLE SKILL GAP ANALYSIS:")
    print("="*70)
    
    # Create sample resume data
    sample_skills = ['Python', 'JavaScript', 'HTML5', 'CSS', 'Git', 'MySQL', 
                     'Problem Solving', 'Data Structures']
    
    print(f"\nSample Resume Skills: {', '.join(sample_skills)}")
    
    # Test against Software Engineer role
    role_data = load_job_role('software_engineer')
    if role_data:
        print(f"\nAnalyzing against: {role_data['name']}")
        
        required_skills = [skill['name'] for skill in role_data['required_skills']]
        preferred_skills = [skill['name'] for skill in role_data['preferred_skills']]
        
        print(f"\nRequired Skills for {role_data['name']}:")
        for skill in required_skills[:5]:
            if skill in sample_skills:
                print(f"  ✓ {skill}")
            else:
                print(f"  ✗ {skill} (Missing)")
    
    # Check API availability
    print("\n" + "="*70)
    print("🔌 API STATUS:")
    print("="*70)
    
    job_market = JobMarketAnalyzer()
    if job_market.api_available:
        print("✓ Adzuna Job API: ACTIVE")
        print("  Can fetch real-time job listings from India")
    else:
        print("✗ Adzuna Job API: Not configured")
    
    print("\n" + "="*70)
    print("✅ DEMO COMPLETE!")
    print("="*70)
    print("\nNext Steps:")
    print("1. Upload your resume in the Streamlit app")
    print("2. Select from 7 available job roles")
    print("3. Get personalized skill gap analysis")
    print("4. View real-time job listings (if API is active)")
    print("\nRun: streamlit run app.py")
    print("="*70)

if __name__ == "__main__":
    demo_analysis()
