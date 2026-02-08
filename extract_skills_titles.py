"""
Extract Skills and Job Titles from LinkedIn Jobs Data
"""

import pandas as pd
import json
import re
from collections import Counter

def extract_skills_from_description(description):
    """Extract skills from job description"""
    skills = set()
    
    # Extract from "Skill:" section at the beginning
    if pd.notna(description) and "Skill:" in description:
        skill_section = description.split("Skill:")[1].split(";")[0]
        skill_list = [s.strip() for s in skill_section.split(",")]
        skills.update(skill_list)
    
    return skills

def clean_job_title(title):
    """Clean job title"""
    if pd.isna(title):
        return None
    # Remove HTML entities
    title = title.replace("&amp;", "&")
    return title.strip()

def main():
    # Read CSV
    print("Reading LinkedIn Jobs Data...")
    df = pd.read_csv('LinkedIn_Jobs_Data_India.csv')
    
    print(f"Total jobs: {len(df)}")
    
    # Extract all skills
    all_skills = set()
    for desc in df['description']:
        skills = extract_skills_from_description(desc)
        all_skills.update(skills)
    
    # Remove empty strings
    all_skills = {s for s in all_skills if s and len(s) > 1}
    
    # Extract all job titles
    all_titles = set()
    for title in df['title']:
        clean_title = clean_job_title(title)
        if clean_title:
            all_titles.add(clean_title)
    
    # Count frequency
    skill_counter = Counter()
    title_counter = Counter()
    
    for desc in df['description']:
        skills = extract_skills_from_description(desc)
        for skill in skills:
            if skill and len(skill) > 1:
                skill_counter[skill] += 1
    
    for title in df['title']:
        clean_title = clean_job_title(title)
        if clean_title:
            title_counter[clean_title] += 1
    
    # Sort by frequency
    sorted_skills = sorted(skill_counter.items(), key=lambda x: x[1], reverse=True)
    sorted_titles = sorted(title_counter.items(), key=lambda x: x[1], reverse=True)
    
    # Print statistics
    print(f"\n{'='*60}")
    print(f"EXTRACTION RESULTS")
    print(f"{'='*60}")
    print(f"Total Unique Skills: {len(all_skills)}")
    print(f"Total Unique Job Titles: {len(all_titles)}")
    
    # Top 30 skills
    print(f"\n{'='*60}")
    print(f"TOP 30 SKILLS (by frequency)")
    print(f"{'='*60}")
    for i, (skill, count) in enumerate(sorted_skills[:30], 1):
        print(f"{i:2d}. {skill:40s} - {count:3d} jobs")
    
    # Top 20 job titles
    print(f"\n{'='*60}")
    print(f"TOP 20 JOB TITLES (by frequency)")
    print(f"{'='*60}")
    for i, (title, count) in enumerate(sorted_titles[:20], 1):
        print(f"{i:2d}. {title:50s} - {count:3d} jobs")
    
    # Save to files
    print(f"\n{'='*60}")
    print(f"SAVING DATA FILES...")
    print(f"{'='*60}")
    
    # Save all skills
    with open('data/extracted_skills.json', 'w') as f:
        json.dump({
            'total_skills': len(all_skills),
            'skills_by_frequency': [{'skill': skill, 'count': count} for skill, count in sorted_skills],
            'all_skills': sorted(list(all_skills))
        }, f, indent=2)
    print("✓ Saved: data/extracted_skills.json")
    
    # Save all job titles
    with open('data/extracted_job_titles.json', 'w') as f:
        json.dump({
            'total_titles': len(all_titles),
            'titles_by_frequency': [{'title': title, 'count': count} for title, count in sorted_titles],
            'all_titles': sorted(list(all_titles))
        }, f, indent=2)
    print("✓ Saved: data/extracted_job_titles.json")
    
    # Update skill taxonomy with new skills
    try:
        with open('data/skills/skill_taxonomy.json', 'r') as f:
            taxonomy = json.load(f)
    except:
        taxonomy = {}
    
    # Categorize extracted skills
    categorized_skills = {
        'programming_languages': [],
        'frameworks_libraries': [],
        'databases': [],
        'tools_technologies': [],
        'concepts_methodologies': [],
        'soft_skills': []
    }
    
    # Common categorizations
    prog_langs = ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'typescript', 'r', 'nodejs']
    frameworks = ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'tensorflow', 'pytorch', 'keras', 'express', 'fastapi', 'hibernate']
    databases = ['mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra', 'dynamodb', 'oracle']
    tools = ['git', 'docker', 'kubernetes', 'jenkins', 'aws', 'azure', 'gcp', 'linux', 'jira', 'github']
    concepts = ['oop', 'rest', 'api', 'microservices', 'agile', 'scrum', 'ci/cd', 'devops', 'machine learning', 'deep learning', 'data structures', 'algorithms']
    soft = ['problem solving', 'communication', 'teamwork', 'leadership', 'analytical']
    
    for skill in all_skills:
        skill_lower = skill.lower()
        if any(lang in skill_lower for lang in prog_langs):
            categorized_skills['programming_languages'].append(skill)
        elif any(fw in skill_lower for fw in frameworks):
            categorized_skills['frameworks_libraries'].append(skill)
        elif any(db in skill_lower for db in databases):
            categorized_skills['databases'].append(skill)
        elif any(tool in skill_lower for tool in tools):
            categorized_skills['tools_technologies'].append(skill)
        elif any(concept in skill_lower for concept in concepts):
            categorized_skills['concepts_methodologies'].append(skill)
        elif any(soft_s in skill_lower for soft_s in soft):
            categorized_skills['soft_skills'].append(skill)
        else:
            categorized_skills['tools_technologies'].append(skill)
    
    # Save categorized skills
    with open('data/skills/extracted_skill_taxonomy.json', 'w') as f:
        json.dump(categorized_skills, f, indent=2)
    print("✓ Saved: data/skills/extracted_skill_taxonomy.json")
    
    print(f"\n{'='*60}")
    print(f"EXTRACTION COMPLETE!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
