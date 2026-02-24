"""
Verification script to check if all data and configurations are properly integrated.
"""

import os
import json
import yaml
from pathlib import Path

def check_job_roles():
    """Check if all job role YAML files are present."""
    print("\n" + "="*60)
    print("CHECKING JOB ROLES")
    print("="*60)
    
    yaml_dir = "data/job_roles"
    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith('.yaml')]
    
    print(f"\n✅ Found {len(yaml_files)} job role YAML files:")
    for yaml_file in yaml_files:
        role_name = yaml_file.replace('.yaml', '').replace('_', ' ').title()
        print(f"   • {role_name} ({yaml_file})")
        
        # Load and verify structure
        with open(os.path.join(yaml_dir, yaml_file), 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            required_skills = len(data.get('required_skills', []))
            optional_skills = len(data.get('optional_skills', []))
            print(f"      - Required skills: {required_skills}")
            print(f"      - Optional skills: {optional_skills}")

def check_combined_data():
    """Check if combined skills and titles data are present."""
    print("\n" + "="*60)
    print("CHECKING COMBINED LINKEDIN DATA")
    print("="*60)
    
    # Check combined skills
    skills_file = "data/combined_skills.json"
    if os.path.exists(skills_file):
        with open(skills_file, 'r', encoding='utf-8') as f:
            skills_data = json.load(f)
            print(f"\n✅ Combined Skills Data:")
            print(f"   • Total skills: {skills_data.get('total_skills', 0)}")
            print(f"   • Dataset 1 contribution: {skills_data.get('dataset_1_contribution', 0)}")
            print(f"   • Dataset 2 contribution: {skills_data.get('dataset_2_contribution', 0)}")
            
            # Show top 10 skills
            top_skills = skills_data.get('skills_by_frequency', [])[:10]
            print(f"   • Top 10 skills:")
            for skill in top_skills:
                print(f"      - {skill['skill']}: {skill['count']} jobs")
    else:
        print(f"\n❌ Combined skills file not found: {skills_file}")
    
    # Check combined titles
    titles_file = "data/combined_job_titles.json"
    if os.path.exists(titles_file):
        with open(titles_file, 'r', encoding='utf-8') as f:
            titles_data = json.load(f)
            print(f"\n✅ Combined Job Titles Data:")
            print(f"   • Total titles: {titles_data.get('total_titles', 0)}")
            print(f"   • Dataset 1 contribution: {titles_data.get('dataset_1_contribution', 0)}")
            print(f"   • Dataset 2 contribution: {titles_data.get('dataset_2_contribution', 0)}")
            
            # Show top 10 titles
            top_titles = titles_data.get('titles_by_frequency', [])[:10]
            print(f"   • Top 10 job titles:")
            for title in top_titles:
                print(f"      - {title['title']}: {title['count']} jobs")
    else:
        print(f"\n❌ Combined titles file not found: {titles_file}")

def check_api_config():
    """Check if API configurations are present."""
    print("\n" + "="*60)
    print("CHECKING API CONFIGURATIONS")
    print("="*60)
    
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"\n✅ .env file found")
        
        # Read and check for API keys (without revealing them)
        with open(env_file, 'r') as f:
            content = f.read()
            
        api_keys = [
            'OPENAI_API_KEY',
            'GOOGLE_GEMINI_API_KEY',
            'ADZUNA_APP_ID',
            'ADZUNA_API_KEY',
            'JSEARCH_API_KEY',
            'INDIAN_API_KEY'
        ]
        
        for key in api_keys:
            if key in content:
                print(f"   ✅ {key} configured")
            else:
                print(f"   ⚠️  {key} not found")
    else:
        print(f"\n⚠️  .env file not found")

def check_config_yaml():
    """Check config.yaml for job roles list."""
    print("\n" + "="*60)
    print("CHECKING CONFIG.YAML")
    print("="*60)
    
    config_file = "config.yaml"
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        print(f"\n✅ config.yaml found")
        
        # Check default roles
        default_roles = config.get('job_roles', {}).get('default_roles', [])
        print(f"   • Default roles configured: {len(default_roles)}")
        for role in default_roles:
            print(f"      - {role}")
    else:
        print(f"\n❌ config.yaml not found")

def check_app_structure():
    """Check if main app.py has proper structure."""
    print("\n" + "="*60)
    print("CHECKING APP STRUCTURE")
    print("="*60)
    
    app_file = "app.py"
    if os.path.exists(app_file):
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = {
            'import yaml': 'yaml import',
            'import os': 'os import',
            'def load_job_roles()': 'load_job_roles function',
            'def load_combined_skills()': 'load_combined_skills function',
            'def load_combined_job_titles()': 'load_combined_job_titles function',
            'combined_skills_data = load_combined_skills()': 'load combined skills',
            'combined_titles_data = load_combined_job_titles()': 'load combined titles',
        }
        
        print(f"\n✅ app.py structure checks:")
        for pattern, description in checks.items():
            if pattern in content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} MISSING")
    else:
        print(f"\n❌ app.py not found")

def main():
    """Run all verification checks."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "INTEGRATION VERIFICATION" + " "*19 + "║")
    print("╚" + "="*58 + "╝")
    
    check_job_roles()
    check_combined_data()
    check_api_config()
    check_config_yaml()
    check_app_structure()
    
    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)
    print("\n✅ If all checks passed, the integration is ready!")
    print("🚀 Run 'streamlit run app.py' to start the application\n")

if __name__ == "__main__":
    main()
