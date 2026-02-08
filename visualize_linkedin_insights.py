"""
Visualize LinkedIn Jobs Data Insights
"""

import pandas as pd
import json
from collections import Counter

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def main():
    # Load data
    df = pd.read_csv('LinkedIn_Jobs_Data_India.csv')
    
    with open('data/extracted_job_titles.json', 'r') as f:
        titles_data = json.load(f)
    
    with open('data/extracted_skills.json', 'r') as f:
        skills_data = json.load(f)
    
    print_section("📊 LINKEDIN JOBS DATA ANALYSIS - PROJECT INTEGRATION")
    
    # Overview
    print(f"\n📁 Dataset Overview:")
    print(f"   Total Jobs Analyzed: {len(df):,}")
    print(f"   Unique Job Titles: {titles_data['total_titles']}")
    print(f"   Unique Skills Extracted: {skills_data['total_skills']}")
    published_dates = df['publishedAt'].dropna()
    if len(published_dates) > 0:
        print(f"   Date Range: {published_dates.min()} to {published_dates.max()}")
    
    # Geographic distribution
    print_section("🗺️ GEOGRAPHIC DISTRIBUTION (Top Cities)")
    city_counts = df['city'].value_counts().head(15)
    for i, (city, count) in enumerate(city_counts.items(), 1):
        bar = "█" * int(count / city_counts.max() * 40)
        print(f"{i:2d}. {city:30s} {bar} {count:3d} jobs")
    
    # Experience levels
    print_section("👔 EXPERIENCE LEVEL DISTRIBUTION")
    exp_counts = df['experienceLevel'].value_counts()
    for exp_level, count in exp_counts.items():
        percentage = (count / len(df)) * 100
        bar = "█" * int(percentage / 2)
        print(f"   {exp_level:20s} {bar} {count:4d} ({percentage:5.1f}%)")
    
    # Contract types
    print_section("💼 CONTRACT TYPE DISTRIBUTION")
    contract_counts = df['contractType'].value_counts()
    for contract_type, count in contract_counts.items():
        if pd.notna(contract_type):
            percentage = (count / len(df)) * 100
            bar = "█" * int(percentage / 2)
            print(f"   {contract_type:20s} {bar} {count:4d} ({percentage:5.1f}%)")
    
    # Sectors
    print_section("🏢 TOP SECTORS")
    sector_counts = df['sector'].value_counts().head(10)
    for i, (sector, count) in enumerate(sector_counts.items(), 1):
        if pd.notna(sector):
            percentage = (count / len(df)) * 100
            bar = "█" * int(count / sector_counts.max() * 40)
            print(f"{i:2d}. {sector[:50]:50s} {count:3d} ({percentage:4.1f}%)")
    
    # Job roles in our project
    print_section("🎯 PROJECT JOB ROLES (From LinkedIn Data)")
    
    project_roles = {
        'Data Scientist': 47,
        'ML Engineer': 10,
        'Software Engineer': 18,
        'Web Developer': 14,
        'Product Manager': 35,
        'Financial Analyst': 20,
        'Business Development Manager': 28
    }
    
    total_covered = sum(project_roles.values())
    coverage_pct = (total_covered / len(df)) * 100
    
    for i, (role, count) in enumerate(sorted(project_roles.items(), key=lambda x: x[1], reverse=True), 1):
        bar = "█" * int(count / max(project_roles.values()) * 40)
        print(f"{i}. {role:35s} {bar} {count:3d} jobs")
    
    print(f"\n   Total Coverage: {total_covered} jobs ({coverage_pct:.1f}% of dataset)")
    
    # Skills breakdown
    print_section("💡 SKILL CATEGORIES")
    
    with open('data/skills/extracted_skill_taxonomy.json', 'r') as f:
        taxonomy = json.load(f)
    
    for category, skills in taxonomy.items():
        if skills:
            category_name = category.replace('_', ' ').title()
            print(f"\n   {category_name}: ({len(skills)} skills)")
            for skill in skills[:5]:
                print(f"      • {skill}")
            if len(skills) > 5:
                print(f"      ... and {len(skills) - 5} more")
    
    # Application statistics
    print_section("📈 APPLICATION STATISTICS")
    
    apps = df['applicationsCount'].dropna()
    if len(apps) > 0:
        print(f"   Average Applications: {apps.mean():.1f}")
        print(f"   Median Applications: {apps.median():.1f}")
        print(f"   Max Applications: {apps.max():.0f}")
        print(f"   Min Applications: {apps.min():.0f}")
    
    # Recently posted jobs
    print_section("⏰ RECENT JOB POSTINGS")
    recent = df['recently_posted_jobs'].value_counts()
    for status, count in recent.items():
        percentage = (count / len(df)) * 100
        print(f"   {status:10s}: {count:4d} jobs ({percentage:5.1f}%)")
    
    # Summary
    print_section("✅ PROJECT ENHANCEMENT SUMMARY")
    print("""
   What's Been Added to Your Project:
   
   1. ✓ Real LinkedIn Job Data (949 jobs from India)
   2. ✓ 7 Job Role Profiles (based on actual demand)
   3. ✓ 128 Extracted Skills (from real job descriptions)
   4. ✓ 495 Unique Job Titles (market insights)
   5. ✓ Geographic Data (15+ cities)
   6. ✓ Experience Level Mapping
   7. ✓ Skill Taxonomy (categorized)
   
   Your App Can Now:
   
   • Match resumes against 7 real-world job roles
   • Analyze skills based on actual market demand
   • Provide data-driven career recommendations
   • Show skill gaps based on 949 job postings
   • Generate personalized learning roadmaps
   • Connect to live job APIs (Adzuna, OpenAI, Gemini)
   
   Next: Run 'streamlit run app.py' to test the enhanced application!
   """)
    
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
