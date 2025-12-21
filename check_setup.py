"""Check if all dependencies are installed and app can run."""

import sys

print("Checking dependencies...")
print("=" * 50)

missing = []

# Check critical dependencies
dependencies = [
    ("streamlit", "Streamlit web framework"),
    ("pdfplumber", "PDF parsing"),
    ("spacy", "NLP processing"),
    ("sklearn", "TF-IDF and cosine similarity"),
    ("fuzzywuzzy", "Fuzzy string matching"),
    ("pandas", "Data processing"),
    ("numpy", "Numerical computing"),
    ("yaml", "YAML file handling"),
]

for module_name, description in dependencies:
    try:
        if module_name == "yaml":
            __import__("yaml")
        elif module_name == "sklearn":
            __import__("sklearn")
        else:
            __import__(module_name)
        print(f"✅ {module_name:15} - {description}")
    except ImportError:
        print(f"❌ {module_name:15} - {description} - MISSING")
        missing.append(module_name)

print("=" * 50)

if missing:
    print(f"\n❌ Missing {len(missing)} dependencies:")
    for m in missing:
        print(f"   - {m}")
    print("\nTo install, run:")
    print("   pip install -r requirements.txt")
    print("\nFor spaCy model:")
    print("   python -m spacy download en_core_web_sm")
    sys.exit(1)
else:
    print("\n✅ All dependencies installed!")
    
    # Test imports
    print("\nTesting imports...")
    try:
        from src.core.pdf_resume_parser import PDFResumeParser
        from src.core.skill_gap_analyzer_tfidf import SkillGapAnalyzerTFIDF
        from src.core.job_readiness_scorer import JobReadinessScorer
        print("✅ All imports successful!")
        print("\n🚀 Ready to run! Use:")
        print("   streamlit run app.py")
    except Exception as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)

