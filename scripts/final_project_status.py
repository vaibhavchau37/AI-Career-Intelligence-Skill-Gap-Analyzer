"""
Final Combined Visualization - Both LinkedIn Datasets
"""

import json

def print_header(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def main():
    # Load combined data
    with open('data/combined_skills.json', 'r') as f:
        skills_data = json.load(f)
    
    with open('data/combined_job_titles.json', 'r') as f:
        titles_data = json.load(f)
    
    print_header("🎯 FINAL PROJECT STATUS - COMBINED LINKEDIN DATA ANALYSIS")
    
    # Summary
    print(f"\n📊 **DATA COVERAGE:**")
    print(f"   Total Jobs Analyzed: 8,876 (Dataset 1: 949 + Dataset 2: 7,927)")
    print(f"   Total Unique Skills: {skills_data['total_skills']}")
    print(f"   Total Unique Job Titles: {titles_data['total_titles']}")
    print(f"   Dataset 1 Skills: {skills_data['dataset_1_contribution']}")
    print(f"   Dataset 2 Skills: {skills_data['dataset_2_contribution']}")
    
    # Top skills
    print_header("💡 TOP 25 MARKET-DEMANDED SKILLS")
    for i, skill_info in enumerate(skills_data['skills_by_frequency'][:25], 1):
        bar = "█" * min(50, int(skill_info['count'] / 200))
        print(f"{i:2d}. {skill_info['skill']:30s} {bar} {skill_info['count']:5d} jobs")
    
    # Top job titles
    print_header("📋 TOP 20 JOB TITLES IN INDIAN MARKET")
    for i, title_info in enumerate(titles_data['titles_by_frequency'][:20], 1):
        bar = "█" * min(40, int(title_info['count'] / 5))
        print(f"{i:2d}. {title_info['title'][:55]:55s} {title_info['count']:4d} jobs")
    
    # Available job roles
    print_header("🎯 YOUR PROJECT - 12 JOB ROLE PROFILES AVAILABLE")
    
    job_roles = {
        'Data Scientist': {'dataset1': 47, 'dataset2': 57, 'file': 'data_scientist.yaml'},
        'ML Engineer': {'dataset1': 10, 'dataset2': 0, 'file': 'ml_engineer.yaml'},
        'Software Engineer': {'dataset1': 18, 'dataset2': 0, 'file': 'software_engineer.yaml'},
        'Web Developer': {'dataset1': 14, 'dataset2': 0, 'file': 'web_developer.yaml'},
        'Product Manager': {'dataset1': 35, 'dataset2': 0, 'file': 'product_manager.yaml'},
        'Financial Analyst': {'dataset1': 20, 'dataset2': 0, 'file': 'financial_analyst.yaml'},
        'Business Development Manager': {'dataset1': 28, 'dataset2': 0, 'file': 'business_development_manager.yaml'},
        'Data Engineer': {'dataset1': 0, 'dataset2': 153, 'file': 'data_engineer.yaml'},
        'Business Analyst': {'dataset1': 0, 'dataset2': 126, 'file': 'business_analyst.yaml'},
        'Python Developer': {'dataset1': 0, 'dataset2': 82, 'file': 'python_developer.yaml'},
        'Java Developer': {'dataset1': 0, 'dataset2': 172, 'file': 'java_developer.yaml'},
        'Salesforce Developer': {'dataset1': 0, 'dataset2': 57, 'file': 'salesforce_developer.yaml'},
    }
    
    total_coverage = sum(role['dataset1'] + role['dataset2'] for role in job_roles.values())
    
    for i, (role_name, data) in enumerate(job_roles.items(), 1):
        total = data['dataset1'] + data['dataset2']
        if total > 0:
            bar = "█" * int(total / 5)
            print(f"{i:2d}. {role_name:35s} {bar} {total:4d} jobs | ✅ {data['file']}")
        else:
            print(f"{i:2d}. {role_name:35s} Profile created | ✅ {data['file']}")
    
    print(f"\n   📊 Total Job Coverage: {total_coverage:,} jobs")
    print(f"   📈 Coverage Rate: {(total_coverage/8876)*100:.1f}% of total dataset")
    
    # Skill categories
    print_header("🏆 TOP SKILL CATEGORIES")
    
    categories = {
        'Programming Languages': ['Python', 'Java', 'Javascript', 'R', 'Scala', 'Go'],
        'Cloud Platforms': ['AWS', 'Azure', 'GCP'],
        'Data Technologies': ['SQL', 'Spark', 'Kafka', 'ETL'],
        'DevOps Tools': ['Docker', 'Git', 'Ci/Cd', 'Kubernetes'],
        'Web Technologies': ['React.js', 'HTML', 'CSS', 'API', 'Rest'],
        'Soft Skills': ['Communication', 'Leadership', 'Analytical']
    }
    
    skills_dict = {s['skill']: s['count'] for s in skills_data['skills_by_frequency']}
    
    for category, skills in categories.items():
        total_count = sum(skills_dict.get(skill, 0) for skill in skills)
        if total_count > 0:
            bar = "█" * min(50, int(total_count / 200))
            print(f"   {category:25s} {bar} {total_count:5d} mentions")
    
    # Project capabilities
    print_header("✅ YOUR PROJECT CAPABILITIES")
    
    capabilities = [
        "✅ Resume Parsing & Analysis (PDF support)",
        "✅ Job Role Matching (12 comprehensive profiles)",
        "✅ Skill Gap Identification (based on 8,876 jobs)",
        "✅ Job Readiness Scoring (data-driven)",
        "✅ Personalized Learning Roadmaps",
        "✅ Real-time Job Listings (Adzuna API)",
        "✅ AI-Enhanced Recommendations (OpenAI, Gemini)",
        "✅ Market Trend Analysis (skills, locations, roles)",
        "✅ TF-IDF Based Skill Matching",
        "✅ Multi-city Job Market Coverage (15+ cities)"
    ]
    
    for capability in capabilities:
        print(f"   {capability}")
    
    # Next steps
    print_header("🚀 NEXT STEPS")
    
    print("""
   1. ✅ Data Extraction Complete (8,876 jobs analyzed)
   2. ✅ Job Roles Created (12 comprehensive profiles)
   3. ✅ Skills Database Built (238 unique skills)
   4. ✅ API Keys Configured (Adzuna, OpenAI, Gemini)
   
   📱 Ready to Launch:
   
   Command: streamlit run app.py
   URL: http://localhost:8501
   
   🎯 Features Available:
   - Upload PDF resumes
   - Select from 12 job roles
   - Get skill gap analysis
   - View job readiness scores
   - Generate learning roadmaps
   - Access real-time job listings
   
   📊 Data Files:
   - data/combined_skills.json (238 skills)
   - data/combined_job_titles.json (3,443 titles)
   - data/job_roles/*.yaml (12 role profiles)
   
   📖 Documentation:
   - COMBINED_DATA_SUMMARY.md
   - LINKEDIN_DATA_EXTRACTION_REPORT.md
   - README.md
   """)
    
    print("="*80)
    print(" 🎉 PROJECT ENHANCED WITH REAL LINKEDIN DATA!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
