"""
Setup verification script.
Checks if all required dependencies and files are in place.
"""

import os
import sys
from pathlib import Path


def check_file_exists(path: str, name: str) -> bool:
    """Check if a file exists."""
    exists = os.path.exists(path)
    status = "✓" if exists else "✗"
    print(f"{status} {name}: {path}")
    return exists


def check_directory_exists(path: str, name: str) -> bool:
    """Check if a directory exists."""
    exists = os.path.isdir(path)
    status = "✓" if exists else "✗"
    print(f"{status} {name}: {path}")
    return exists


def check_import(module: str) -> bool:
    """Check if a module can be imported."""
    try:
        __import__(module)
        print(f"✓ {module} - Imported successfully")
        return True
    except ImportError as e:
        print(f"✗ {module} - Import failed: {e}")
        return False


def main():
    """Run setup verification."""
    print("=" * 60)
    print("Setup Verification for AI Career Analyzer")
    print("=" * 60)
    print()
    
    all_ok = True
    
    # Check core directories
    print("Directory Structure:")
    print("-" * 60)
    dirs_to_check = [
        ("src", "Source code"),
        ("src/core", "Core modules"),
        ("src/models", "Data models"),
        ("src/matcher", "Matcher modules"),
        ("src/roadmap", "Roadmap modules"),
        ("src/analyzer", "Analyzer module"),
        ("src/utils", "Utilities"),
        ("data", "Data directory"),
        ("data/job_roles", "Job roles"),
        ("data/skills", "Skills"),
        ("examples", "Examples"),
    ]
    
    for dir_path, dir_name in dirs_to_check:
        if not check_directory_exists(dir_path, dir_name):
            all_ok = False
    print()
    
    # Check key files
    print("Key Files:")
    print("-" * 60)
    files_to_check = [
        ("requirements.txt", "Requirements"),
        ("config.yaml", "Configuration"),
        ("README.md", "README"),
        ("src/analyzer/career_analyzer.py", "Main analyzer"),
        ("data/job_roles/ml_engineer.yaml", "ML Engineer role"),
        ("data/skills/skill_taxonomy.json", "Skill taxonomy"),
    ]
    
    for file_path, file_name in files_to_check:
        if not check_file_exists(file_path, file_name):
            all_ok = False
    print()
    
    # Check Python dependencies
    print("Python Dependencies:")
    print("-" * 60)
    
    critical_modules = [
        "yaml",
        "pandas",
        "numpy",
    ]
    
    optional_modules = [
        "spacy",
        "fuzzywuzzy",
        "sentence_transformers",
    ]
    
    print("Critical (required):")
    for module in critical_modules:
        if not check_import(module):
            all_ok = False
    
    print("\nOptional (recommended):")
    for module in optional_modules:
        check_import(module)
    
    # Check spaCy model
    print("\nspaCy Model:")
    print("-" * 60)
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
            print("✓ en_core_web_sm model loaded successfully")
        except OSError:
            print("✗ en_core_web_sm model not found")
            print("  Run: python -m spacy download en_core_web_sm")
            print("  (This is optional but recommended)")
    except ImportError:
        print("✗ spacy not installed")
    
    print()
    print("=" * 60)
    
    if all_ok:
        print("✓ Setup verification PASSED!")
        print("\nYou can now run: python examples/analyze_resume.py")
    else:
        print("✗ Setup verification FAILED!")
        print("\nPlease fix the issues above before proceeding.")
        print("Install dependencies: pip install -r requirements.txt")
    
    print("=" * 60)
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

