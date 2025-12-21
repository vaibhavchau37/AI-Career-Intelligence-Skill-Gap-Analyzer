"""
Example: Job Role Skill Mapping and Comparison

This script demonstrates how to use the job role skill mapping system
to compare resume skills against job role requirements.

Usage:
    python examples/skill_mapping_comparison.py
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))


class SkillMappingComparator:
    """
    Compares resume skills against job role requirements.
    
    How it works:
    1. Loads job role skill mappings from JSON
    2. Compares resume skills with required and optional skills
    3. Calculates match percentages
    4. Identifies missing skills
    """
    
    def __init__(self, mapping_file: str = "data/job_roles/skill_mapping.json"):
        """
        Initialize the comparator with job role mappings.
        
        Args:
            mapping_file: Path to JSON file with job role skill mappings
        """
        self.mapping_file = mapping_file
        self.job_roles = self._load_mappings()
    
    def _load_mappings(self) -> Dict:
        """
        Load job role skill mappings from JSON file.
        
        Returns:
            Dictionary with job role mappings
        """
        mapping_path = Path(self.mapping_file)
        
        if not mapping_path.exists():
            raise FileNotFoundError(f"Skill mapping file not found: {self.mapping_file}")
        
        with open(mapping_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get('job_roles', {})
    
    def compare_skills(self, resume_skills: List[str], role_name: str) -> Dict:
        """
        Compare resume skills with a specific job role requirements.
        
        How it works:
        1. Normalizes skill names (lowercase, remove spaces)
        2. Matches resume skills with required skills
        3. Matches resume skills with optional skills
        4. Identifies missing skills
        5. Calculates match percentages
        
        Args:
            resume_skills: List of skills from resume
            role_name: Name of the job role to compare against
            
        Returns:
            Dictionary with comparison results:
            {
                "matched_required": [],
                "matched_optional": [],
                "missing_required": [],
                "missing_optional": [],
                "required_match_percentage": float,
                "optional_match_percentage": float,
                "overall_match_percentage": float
            }
        """
        # Check if role exists
        if role_name not in self.job_roles:
            raise ValueError(f"Job role not found: {role_name}. Available roles: {list(self.job_roles.keys())}")
        
        role_data = self.job_roles[role_name]
        required_skills = role_data.get('required_skills', [])
        optional_skills = role_data.get('optional_skills', [])
        
        # Normalize all skills for comparison (case-insensitive)
        resume_skills_normalized = [self._normalize_skill(skill) for skill in resume_skills]
        required_skills_normalized = [self._normalize_skill(skill) for skill in required_skills]
        optional_skills_normalized = [self._normalize_skill(skill) for skill in optional_skills]
        
        # Find matched required skills
        matched_required = []
        for i, req_skill in enumerate(required_skills_normalized):
            for res_skill in resume_skills_normalized:
                if req_skill in res_skill or res_skill in req_skill:
                    matched_required.append(required_skills[i])  # Use original name
                    break
        
        # Find matched optional skills
        matched_optional = []
        for i, opt_skill in enumerate(optional_skills_normalized):
            for res_skill in resume_skills_normalized:
                if opt_skill in res_skill or res_skill in opt_skill:
                    matched_optional.append(optional_skills[i])  # Use original name
                    break
        
        # Find missing required skills
        matched_required_normalized = [self._normalize_skill(s) for s in matched_required]
        missing_required = [
            skill for skill in required_skills
            if self._normalize_skill(skill) not in matched_required_normalized
        ]
        
        # Find missing optional skills
        matched_optional_normalized = [self._normalize_skill(s) for s in matched_optional]
        missing_optional = [
            skill for skill in optional_skills
            if self._normalize_skill(skill) not in matched_optional_normalized
        ]
        
        # Calculate match percentages
        required_match_pct = (len(matched_required) / len(required_skills) * 100) if required_skills else 100
        optional_match_pct = (len(matched_optional) / len(optional_skills) * 100) if optional_skills else 100
        
        # Overall match (weighted: required 70%, optional 30%)
        overall_match_pct = (required_match_pct * 0.7) + (optional_match_pct * 0.3)
        
        return {
            "role_name": role_name,
            "matched_required": matched_required,
            "matched_optional": matched_optional,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "required_match_percentage": round(required_match_pct, 2),
            "optional_match_percentage": round(optional_match_pct, 2),
            "overall_match_percentage": round(overall_match_pct, 2),
            "total_required_skills": len(required_skills),
            "total_optional_skills": len(optional_skills),
        }
    
    def compare_all_roles(self, resume_skills: List[str]) -> List[Dict]:
        """
        Compare resume skills against all available job roles.
        
        Args:
            resume_skills: List of skills from resume
            
        Returns:
            List of comparison results for all roles, sorted by overall match percentage
        """
        results = []
        
        for role_name in self.job_roles.keys():
            comparison = self.compare_skills(resume_skills, role_name)
            results.append(comparison)
        
        # Sort by overall match percentage (descending)
        results.sort(key=lambda x: x['overall_match_percentage'], reverse=True)
        
        return results
    
    def _normalize_skill(self, skill: str) -> str:
        """
        Normalize skill name for comparison.
        
        Removes case sensitivity and extra spaces.
        
        Args:
            skill: Skill name to normalize
            
        Returns:
            Normalized skill name
        """
        return skill.lower().strip().replace(' ', '').replace('-', '').replace('_', '')
    
    def get_role_requirements(self, role_name: str) -> Dict:
        """
        Get requirements for a specific role.
        
        Args:
            role_name: Name of the job role
            
        Returns:
            Dictionary with role requirements
        """
        if role_name not in self.job_roles:
            raise ValueError(f"Job role not found: {role_name}")
        
        return self.job_roles[role_name]


def main():
    """
    Main function to demonstrate skill mapping comparison.
    """
    print("=" * 60)
    print("Job Role Skill Mapping - Comparison Example")
    print("=" * 60)
    print()
    
    # Step 1: Initialize comparator
    print("Loading job role skill mappings...")
    comparator = SkillMappingComparator()
    print(f"✓ Loaded {len(comparator.job_roles)} job roles\n")
    
    # Step 2: Display available roles
    print("Available Job Roles:")
    print("-" * 60)
    for role_name, role_data in comparator.job_roles.items():
        print(f"  • {role_name}")
        print(f"    Description: {role_data.get('description', 'N/A')}")
        print(f"    Required Skills: {len(role_data.get('required_skills', []))}")
        print(f"    Optional Skills: {len(role_data.get('optional_skills', []))}")
        print()
    
    # Step 3: Example resume skills (you can replace this with actual parsed skills)
    example_resume_skills = [
        "Python",
        "Machine Learning",
        "SQL",
        "Pandas",
        "NumPy",
        "Git",
        "Data Analysis",
        "Statistics"
    ]
    
    print("📄 Example Resume Skills:")
    print("-" * 60)
    for skill in example_resume_skills:
        print(f"  • {skill}")
    print()
    
    # Step 4: Compare against all roles
    print("🔍 Comparing against all job roles...")
    print("=" * 60)
    
    results = comparator.compare_all_roles(example_resume_skills)
    
    for result in results:
        print(f"\n📊 {result['role_name']}:")
        print(f"   Overall Match: {result['overall_match_percentage']:.1f}%")
        print(f"   Required Skills Match: {result['required_match_percentage']:.1f}% ({len(result['matched_required'])}/{result['total_required_skills']})")
        print(f"   Optional Skills Match: {result['optional_match_percentage']:.1f}% ({len(result['matched_optional'])}/{result['total_optional_skills']})")
        
        if result['matched_required']:
            print(f"\n   ✅ Matched Required Skills:")
            for skill in result['matched_required']:
                print(f"      • {skill}")
        
        if result['missing_required']:
            print(f"\n   ❌ Missing Required Skills:")
            for skill in result['missing_required']:
                print(f"      • {skill}")
        
        if result['matched_optional']:
            print(f"\n   ✅ Matched Optional Skills:")
            for skill in result['matched_optional'][:5]:  # Show first 5
                print(f"      • {skill}")
            if len(result['matched_optional']) > 5:
                print(f"      ... and {len(result['matched_optional']) - 5} more")
        
        print()
    
    # Step 5: Detailed comparison for top role
    print("=" * 60)
    top_role = results[0]
    print(f"\n🎯 Best Match: {top_role['role_name']}")
    print(f"   Match Score: {top_role['overall_match_percentage']:.1f}%")
    print()
    
    print("📋 Detailed Requirements:")
    print("-" * 60)
    role_req = comparator.get_role_requirements(top_role['role_name'])
    
    print("\nRequired Skills:")
    for skill in role_req['required_skills']:
        status = "✅" if skill in top_role['matched_required'] else "❌"
        print(f"  {status} {skill}")
    
    print("\nOptional Skills (sample):")
    for skill in role_req['optional_skills'][:10]:
        status = "✅" if skill in top_role['matched_optional'] else "○"
        print(f"  {status} {skill}")
    
    print("\n" + "=" * 60)
    print("Comparison complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

