"""
Extract Skills and Job Titles from Second LinkedIn Dataset
Combines with existing extracted data
"""

import pandas as pd
import json
import re
from collections import Counter

def extract_skills_from_job_details(job_details):
    """Extract skills from job details using keyword matching"""
    skills = set()
    
    if pd.isna(job_details):
        return skills
    
    job_details_lower = job_details.lower()
    
    # Common skill keywords to search for
    skill_patterns = {
        # Programming Languages
        'python', 'java', 'javascript', 'c++', 'c#', 'golang', 'go', 'ruby', 'php', 
        'scala', 'kotlin', 'swift', 'typescript', 'r', 'sql', 'pl/sql', 'html', 'html5', 'css', 'css3',
        
        # Frameworks & Libraries
        'react', 'angular', 'vue', 'node.js', 'nodejs', 'django', 'flask', 'spring', 
        'spring boot', 'tensorflow', 'pytorch', 'keras', 'pandas', 'numpy', 'pyspark',
        'spark', 'jquery', 'bootstrap', 'express', 'lwc', 'lightning', 'aura',
        
        # Databases
        'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle', 
        'sql server', 'dynamodb', 'cassandra', 'snowflake', 'bigquery', 'redshift',
        
        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'jenkins', 
        'git', 'github', 'gitlab', 'ci/cd', 'terraform', 'ansible',
        
        # Data & Analytics
        'tableau', 'power bi', 'powerbi', 'etl', 'data warehousing', 'data pipeline',
        'apache kafka', 'kafka', 'hadoop', 'hive', 'databricks', 'dataflow',
        
        # Platforms & Tools
        'salesforce', 'shopify', 'quickbase', 'vlocity', 'omnistudio', 'zoho',
        'sap', 'stibo', 'odi', 'spotfire', 'jira', 'confluence',
        
        # Concepts & Methodologies
        'agile', 'scrum', 'devops', 'rest api', 'rest', 'soap', 'microservices',
        'machine learning', 'deep learning', 'ai', 'nlp', 'data science',
        'oop', 'mvc', 'api', 'json', 'xml', 'ajax',
        
        # Soft Skills
        'communication', 'problem solving', 'analytical', 'teamwork', 'leadership'
    }
    
    for skill in skill_patterns:
        if skill in job_details_lower:
            # Capitalize properly
            if skill == 'python':
                skills.add('Python')
            elif skill in ['java', 'javascript']:
                skills.add(skill.capitalize())
            elif skill in ['sql', 'html', 'css', 'xml', 'api', 'etl', 'nlp', 'mvc', 'oop', 'aws', 'gcp']:
                skills.add(skill.upper())
            elif skill == 'html5':
                skills.add('HTML5')
            elif skill == 'css3':
                skills.add('CSS3')
            elif skill == 'node.js' or skill == 'nodejs':
                skills.add('Node.js')
            elif skill == 'react':
                skills.add('React.js')
            elif skill == 'angular':
                skills.add('Angular')
            elif skill == 'power bi' or skill == 'powerbi':
                skills.add('Power BI')
            elif skill == 'spring boot':
                skills.add('Spring Boot')
            else:
                skills.add(skill.title())
    
    return skills

def clean_job_title(title):
    """Clean job title"""
    if pd.isna(title):
        return None
    return title.strip()

def main():
    print("="*80)
    print(" EXTRACTING DATA FROM SECOND LINKEDIN DATASET")
    print("="*80)
    
    # Read the second CSV
    print("\n📊 Reading linkdin_Job_data.csv...")
    df = pd.read_csv('linkdin_Job_data.csv')
    
    print(f"Total jobs: {len(df)}")
    
    # Extract skills from job_details column
    all_skills = set()
    skill_counter = Counter()
    
    for job_details in df['job_details']:
        skills = extract_skills_from_job_details(job_details)
        all_skills.update(skills)
        for skill in skills:
            skill_counter[skill] += 1
    
    # Extract job titles from 'job' column
    all_titles = set()
    title_counter = Counter()
    
    for title in df['job']:
        clean_title = clean_job_title(title)
        if clean_title:
            all_titles.add(clean_title)
            title_counter[clean_title] += 1
    
    # Sort by frequency
    sorted_skills = sorted(skill_counter.items(), key=lambda x: x[1], reverse=True)
    sorted_titles = sorted(title_counter.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n{'='*80}")
    print(f"EXTRACTION RESULTS - Dataset 2")
    print(f"{'='*80}")
    print(f"Total Unique Skills: {len(all_skills)}")
    print(f"Total Unique Job Titles: {len(all_titles)}")
    
    # Top 30 skills
    print(f"\n{'='*80}")
    print(f"TOP 30 SKILLS (by frequency)")
    print(f"{'='*80}")
    for i, (skill, count) in enumerate(sorted_skills[:30], 1):
        print(f"{i:2d}. {skill:40s} - {count:3d} jobs")
    
    # Top 20 job titles
    print(f"\n{'='*80}")
    print(f"TOP 20 JOB TITLES (by frequency)")
    print(f"{'='*80}")
    for i, (title, count) in enumerate(sorted_titles[:20], 1):
        print(f"{i:2d}. {title:60s} - {count:3d} jobs")
    
    # Load existing data from first dataset
    print(f"\n{'='*80}")
    print(f"MERGING WITH EXISTING DATA")
    print(f"{'='*80}")
    
    try:
        with open('data/extracted_skills.json', 'r') as f:
            existing_skills_data = json.load(f)
        
        with open('data/extracted_job_titles.json', 'r') as f:
            existing_titles_data = json.load(f)
        
        # Merge skills
        existing_skills_dict = {item['skill']: item['count'] for item in existing_skills_data['skills_by_frequency']}
        
        for skill, count in sorted_skills:
            if skill in existing_skills_dict:
                existing_skills_dict[skill] += count
            else:
                existing_skills_dict[skill] = count
        
        # Merge titles
        existing_titles_dict = {item['title']: item['count'] for item in existing_titles_data['titles_by_frequency']}
        
        for title, count in sorted_titles:
            if title in existing_titles_dict:
                existing_titles_dict[title] += count
            else:
                existing_titles_dict[title] = count
        
        # Sort merged data
        merged_skills = sorted(existing_skills_dict.items(), key=lambda x: x[1], reverse=True)
        merged_titles = sorted(existing_titles_dict.items(), key=lambda x: x[1], reverse=True)
        
        print(f"✓ Merged Skills: {len(merged_skills)} total (added {len(all_skills)} from dataset 2)")
        print(f"✓ Merged Titles: {len(merged_titles)} total (added {len(all_titles)} from dataset 2)")
        
        # Save combined data
        combined_skills = {
            'total_skills': len(merged_skills),
            'dataset_1_contribution': existing_skills_data['total_skills'],
            'dataset_2_contribution': len(all_skills),
            'skills_by_frequency': [{'skill': skill, 'count': count} for skill, count in merged_skills],
            'all_skills': sorted(list(set([s for s, c in merged_skills])))
        }
        
        combined_titles = {
            'total_titles': len(merged_titles),
            'dataset_1_contribution': existing_titles_data['total_titles'],
            'dataset_2_contribution': len(all_titles),
            'titles_by_frequency': [{'title': title, 'count': count} for title, count in merged_titles],
            'all_titles': sorted(list(set([t for t, c in merged_titles])))
        }
        
        with open('data/combined_skills.json', 'w') as f:
            json.dump(combined_skills, f, indent=2)
        
        with open('data/combined_job_titles.json', 'w') as f:
            json.dump(combined_titles, f, indent=2)
        
        print(f"\n✓ Saved: data/combined_skills.json")
        print(f"✓ Saved: data/combined_job_titles.json")
        
    except FileNotFoundError:
        print("⚠ Existing data not found, saving dataset 2 data only")
        
        with open('data/dataset2_skills.json', 'w') as f:
            json.dump({
                'total_skills': len(all_skills),
                'skills_by_frequency': [{'skill': skill, 'count': count} for skill, count in sorted_skills],
                'all_skills': sorted(list(all_skills))
            }, f, indent=2)
        
        with open('data/dataset2_job_titles.json', 'w') as f:
            json.dump({
                'total_titles': len(all_titles),
                'titles_by_frequency': [{'title': title, 'count': count} for title, count in sorted_titles],
                'all_titles': sorted(list(all_titles))
            }, f, indent=2)
    
    # Analyze locations
    print(f"\n{'='*80}")
    print(f"TOP LOCATIONS (Dataset 2)")
    print(f"{'='*80}")
    location_counts = df['location'].value_counts().head(15)
    for i, (location, count) in enumerate(location_counts.items(), 1):
        if pd.notna(location):
            print(f"{i:2d}. {location:50s} - {count:3d} jobs")
    
    # Analyze work types
    print(f"\n{'='*80}")
    print(f"WORK TYPE DISTRIBUTION (Dataset 2)")
    print(f"{'='*80}")
    work_type_counts = df['work_type'].value_counts()
    for work_type, count in work_type_counts.items():
        if pd.notna(work_type):
            percentage = (count / len(df)) * 100
            print(f"   {work_type:20s} - {count:3d} jobs ({percentage:5.1f}%)")
    
    print(f"\n{'='*80}")
    print(f"✅ EXTRACTION COMPLETE!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
