# AI Career Intelligence & Skill Gap Analyzer

## 🎯 Project Overview

A lightweight, Python-based system that analyzes resumes, compares them with target job roles, identifies skill gaps, calculates job readiness scores, and generates personalized learning roadmaps.

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│  (CLI / Web API / Streamlit Dashboard - Optional)            │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Application Layer                           │
│  (CareerAnalyzer - Main Orchestrator)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌───▼─────┐ ┌───▼──────────┐
│ Resume       │ │ Job     │ │ Learning     │
│ Analyzer     │ │ Matcher │ │ Roadmap      │
│              │ │         │ │ Generator    │
└───────┬──────┘ └───┬─────┘ └───┬──────────┘
        │            │            │
        └────────────┼────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Core Processing Layer                       │
│  • Resume Parser     • Skill Extractor                       │
│  • Skill Matcher     • Score Calculator                      │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Data Layer                                  │
│  • Job Role Database  • Skill Taxonomy  • Resume Data        │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Lightweight**: Uses pre-trained models (spaCy, transformers) or rule-based matching
2. **No Heavy Training**: Leverages existing NLP models, no custom training required
3. **Modular**: Each component is independent and testable
4. **Explainable**: Every score and recommendation has clear reasoning
5. **Extensible**: Easy to add new job roles or skill categories

## 📁 Folder Structure

```
ai-career-analyzer/
│
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── config.yaml                 # Configuration file
│
├── src/                        # Source code
│   ├── __init__.py
│   │
│   ├── core/                   # Core processing modules
│   │   ├── __init__.py
│   │   ├── resume_parser.py    # Parse and extract resume data
│   │   ├── skill_extractor.py  # Extract skills from resume text
│   │   ├── skill_matcher.py    # Match skills with job requirements
│   │   └── score_calculator.py # Calculate readiness scores
│   │
│   ├── models/                 # Data models and schemas
│   │   ├── __init__.py
│   │   ├── resume.py           # Resume data structure
│   │   ├── job_role.py         # Job role definition
│   │   └── analysis_result.py  # Analysis result structure
│   │
│   ├── matcher/                # Job matching logic
│   │   ├── __init__.py
│   │   ├── job_matcher.py      # Match resume to job roles
│   │   └── role_predictor.py   # Predict suitable roles
│   │
│   ├── roadmap/                # Learning roadmap generation
│   │   ├── __init__.py
│   │   ├── roadmap_generator.py # Generate learning paths
│   │   └── skill_gaps.py        # Identify missing skills
│   │
│   ├── analyzer/               # Main analyzer orchestrator
│   │   ├── __init__.py
│   │   └── career_analyzer.py  # Main application class
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── text_processor.py   # Text cleaning and preprocessing
│       └── explainer.py        # Generate explanations for scores
│
├── data/                       # Data files
│   ├── job_roles/              # Job role definitions
│   │   ├── ml_engineer.yaml
│   │   ├── data_scientist.yaml
│   │   └── ai_researcher.yaml
│   │
│   ├── skills/                 # Skill taxonomy and mappings
│   │   ├── skill_taxonomy.json
│   │   └── skill_synonyms.json
│   │
│   └── examples/               # Example resumes
│       └── sample_resume.txt
│
├── tests/                      # Unit tests
│   ├── __init__.py
│   ├── test_resume_parser.py
│   ├── test_skill_extractor.py
│   └── test_score_calculator.py
│
├── examples/                   # Example usage scripts
│   ├── analyze_resume.py
│   └── batch_analysis.py
│
└── docs/                       # Documentation
    ├── architecture.md         # Detailed architecture
    ├── api_reference.md        # API documentation
    └── user_guide.md           # User guide
```

## 🔧 Core Modules Explained

### 1. Resume Parser (`resume_parser.py`)
**Purpose**: Extract structured information from resume text
- Parses resume into sections (education, experience, skills, etc.)
- Extracts key information (degrees, years of experience, certifications)
- Uses regex and NLP for extraction
- **No heavy training** - uses rule-based parsing with spaCy for entity recognition

### 2. Skill Extractor (`skill_extractor.py`)
**Purpose**: Identify all skills mentioned in resume
- Extracts technical skills (Python, TensorFlow, etc.)
- Extracts soft skills (leadership, communication, etc.)
- Uses keyword matching with skill taxonomy
- Handles synonyms and variations

### 3. Skill Matcher (`skill_matcher.py`)
**Purpose**: Compare resume skills with job role requirements
- Matches skills using similarity (fuzzy matching, embeddings)
- Categorizes skills (must-have, nice-to-have)
- Identifies missing skills
- Uses lightweight embeddings (sentence-transformers) if needed

### 4. Score Calculator (`score_calculator.py`)
**Purpose**: Calculate job readiness score (0-100)
- Weighted scoring based on:
  - Required skills match (40%)
  - Preferred skills match (20%)
  - Years of experience (20%)
  - Education alignment (10%)
  - Certifications/Projects (10%)
- Provides breakdown and explanation

### 5. Job Matcher (`job_matcher.py`)
**Purpose**: Match resume to multiple job roles
- Scores resume against each job role
- Ranks roles by suitability
- Provides top N recommendations

### 6. Role Predictor (`role_predictor.py`)
**Purpose**: Predict suitable job roles based on skills
- Uses skill profiles to suggest roles
- Can recommend roles user might not have considered
- Based on skill similarity patterns

### 7. Roadmap Generator (`roadmap_generator.py`)
**Purpose**: Create personalized learning roadmap
- Identifies skill gaps
- Suggests learning resources (courses, tutorials)
- Prioritizes skills by importance
- Creates timeline (3-month, 6-month plans)

### 8. Career Analyzer (`career_analyzer.py`)
**Purpose**: Main orchestrator class
- Coordinates all modules
- Provides simple API for analysis
- Returns comprehensive results

## 📊 Data Flow

```
1. User Input (Resume Text)
   │
   ▼
2. Resume Parser → Structured Resume Data
   │
   ▼
3. Skill Extractor → List of Skills
   │
   ▼
4. For each Job Role:
   │
   ├─→ Skill Matcher → Matched/Missing Skills
   │
   ├─→ Score Calculator → Readiness Score (0-100)
   │
   └─→ Explanations → Why this score?
   │
5. Job Matcher → Ranked Job Roles
   │
6. Role Predictor → Suggested Roles
   │
7. Roadmap Generator → Learning Roadmap
   │
8. Complete Analysis Report
```

## 🚀 Technology Stack

- **Python 3.8+**: Core language
- **spaCy**: NLP and entity recognition (lightweight)
- **pandas**: Data manipulation
- **pyyaml**: Configuration files
- **sentence-transformers** (optional): For semantic skill matching
- **fuzzywuzzy**: Fuzzy string matching
- **streamlit** (optional): Web UI

## 💡 Key Features

1. **Explainable Scoring**: Every score comes with clear reasoning
2. **Multiple Job Roles**: Analyze against multiple roles simultaneously
3. **Skill Gap Analysis**: Detailed breakdown of missing skills
4. **Learning Roadmap**: Actionable steps to improve readiness
5. **Role Prediction**: Discover new suitable roles
6. **Batch Processing**: Analyze multiple resumes at once

## 🚀 Quick Start

### Web App (Recommended)

```bash
# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Run Streamlit app
streamlit run app.py
```

The web app provides a clean, interactive interface with:
- 📄 Resume upload (PDF)
- 🎯 Role selection
- 📊 Skill gap analysis
- ⭐ Readiness scoring
- 🔍 Role suitability prediction
- 🗺️ Personalized learning roadmap

### Python API

```python
from src.analyzer.career_analyzer import CareerAnalyzer

# Initialize analyzer
analyzer = CareerAnalyzer()

# Analyze resume
result = analyzer.analyze(
    resume_text="...",
    target_roles=["ML Engineer", "Data Scientist"]
)

# Get results
print(f"ML Engineer Score: {result.scores['ML Engineer']}")
print(f"Missing Skills: {result.skill_gaps['ML Engineer']}")
print(f"Learning Roadmap: {result.roadmap['ML Engineer']}")
```

## 🎓 College & Placement Ready

- Well-documented code
- Type hints for clarity
- Unit tests included
- Example scripts provided
- Clear architecture for presentation
- Extensible design

## 📚 Next Steps

1. Implement core modules
2. Create job role definitions
3. Build skill taxonomy
4. Add example usage scripts
5. Write unit tests
6. Create simple UI (optional)

"# AI-Career-Intelligence-Skill-Gap-Analyzer" 
