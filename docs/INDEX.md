# Project Index - Quick Navigation

## 📚 Documentation Files

### Getting Started
- **[README.md](README.md)** - Main project overview and architecture
- **[QUICKSTART.md](QUICKSTART.md)** - Installation and quick start guide
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Simple English explanation of everything

### Detailed Documentation
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - High-level system architecture
- **[docs/architecture.md](docs/architecture.md)** - Detailed technical architecture
- **[docs/api_reference.md](docs/api_reference.md)** - Complete API documentation
- **[docs/user_guide.md](docs/user_guide.md)** - User guide and best practices

## 🗂️ Project Structure

```
ai-career-analyzer/
│
├── 📄 Configuration
│   ├── config.yaml              # Main configuration file
│   └── requirements.txt         # Python dependencies
│
├── 📁 Source Code (src/)
│   ├── core/                    # Core processing modules
│   │   ├── resume_parser.py     # Parse resume text
│   │   ├── skill_extractor.py   # Extract skills
│   │   ├── skill_matcher.py     # Match skills
│   │   └── score_calculator.py  # Calculate scores
│   │
│   ├── models/                  # Data models
│   │   ├── resume.py            # Resume data structure
│   │   ├── job_role.py          # Job role definition
│   │   └── analysis_result.py   # Analysis results
│   │
│   ├── matcher/                 # Job matching
│   │   ├── job_matcher.py       # Match to multiple roles
│   │   └── role_predictor.py    # Predict suitable roles
│   │
│   ├── roadmap/                 # Learning roadmaps
│   │   ├── skill_gaps.py        # Identify gaps
│   │   └── roadmap_generator.py # Generate learning paths
│   │
│   ├── analyzer/                # Main orchestrator
│   │   └── career_analyzer.py   # Main application class
│   │
│   └── utils/                   # Utilities
│       ├── text_processor.py    # Text processing
│       └── explainer.py         # Generate explanations
│
├── 📁 Data (data/)
│   ├── job_roles/               # Job role definitions (YAML)
│   │   ├── ml_engineer.yaml
│   │   └── data_scientist.yaml
│   │
│   ├── skills/                  # Skill data
│   │   ├── skill_taxonomy.json  # Skill categories
│   │   └── skill_synonyms.json  # Skill synonyms
│   │
│   └── examples/                # Example resumes
│       └── sample_resume.txt
│
├── 📁 Examples (examples/)
│   └── analyze_resume.py        # Example usage script
│
├── 📁 Tests (tests/)
│   └── (Unit tests go here)
│
└── 📁 Documentation (docs/)
    ├── architecture.md
    ├── api_reference.md
    └── user_guide.md
```

## 🚀 Quick Start

1. **Read First**: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Understand what it does
2. **Install**: [QUICKSTART.md](QUICKSTART.md) - Setup instructions
3. **Run**: `python examples/analyze_resume.py` - Try it out
4. **Customize**: Edit config.yaml and add job roles

## 📖 Learning Path

### For Understanding
1. Start with [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Simple overview
2. Read [README.md](README.md) - Architecture overview
3. Check [docs/architecture.md](docs/architecture.md) - Detailed technical details

### For Using
1. Follow [QUICKSTART.md](QUICKSTART.md) - Installation
2. Read [docs/user_guide.md](docs/user_guide.md) - How to use
3. Check [docs/api_reference.md](docs/api_reference.md) - API details

### For Development
1. Review [ARCHITECTURE.md](ARCHITECTURE.md) - System design
2. Study source code in `src/` - Implementation details
3. Check examples in `examples/` - Usage patterns

## 🎯 Key Concepts

### Core Modules
- **Resume Parser**: Extracts information from resume text
- **Skill Extractor**: Identifies skills from text
- **Skill Matcher**: Compares resume skills with job requirements
- **Score Calculator**: Calculates readiness scores (0-100)
- **Job Matcher**: Ranks job roles by suitability
- **Roadmap Generator**: Creates learning paths

### Data Flow
```
Resume Text → Parse → Extract Skills → Match → Score → Roadmap → Results
```

### Scoring Components
- Required Skills (40%)
- Preferred Skills (20%)
- Experience (20%)
- Education (10%)
- Certifications (10%)

## 🔧 Configuration

Main config: `config.yaml`
- Scoring weights
- Matching thresholds
- Data paths
- Output settings

## 📝 Example Usage

```python
from src.analyzer.career_analyzer import CareerAnalyzer

analyzer = CareerAnalyzer()
result = analyzer.analyze(resume_text, target_roles=["ML Engineer"])

print(f"Score: {result.get_role_score('ML Engineer')}")
print(f"Missing: {result.skill_gaps['ML Engineer']}")
```

## 📦 Key Files to Know

### For Users
- `config.yaml` - Configure scoring and behavior
- `examples/analyze_resume.py` - Example usage
- `data/job_roles/*.yaml` - Add/modify job roles

### For Developers
- `src/analyzer/career_analyzer.py` - Main entry point
- `src/core/` - Core processing logic
- `src/models/` - Data structures

### For Understanding
- `PROJECT_SUMMARY.md` - Start here!
- `README.md` - Overview
- `ARCHITECTURE.md` - Design decisions

## 🎓 Project Features

✅ Resume parsing and analysis
✅ Skill extraction and matching
✅ Job readiness scoring (0-100)
✅ Skill gap identification
✅ Learning roadmap generation
✅ Multiple job role analysis
✅ Role prediction
✅ Explainable results

## 🛠️ Customization

### Easy Customizations
- Add job roles: Create YAML files in `data/job_roles/`
- Adjust scoring: Edit weights in `config.yaml`
- Add skills: Update `data/skills/skill_taxonomy.json`
- Add synonyms: Edit `data/skills/skill_synonyms.json`

### Advanced Customizations
- Modify scoring algorithm: Edit `src/core/score_calculator.py`
- Enhance skill matching: Edit `src/core/skill_matcher.py`
- Add learning resources: Edit `src/roadmap/roadmap_generator.py`

## 📊 Output Structure

```
AnalysisResult
├── scores: {role_name: RoleScore}
│   ├── overall_score: 0-100
│   ├── breakdown: {category: score}
│   └── explanation: str
├── skill_gaps: {role_name: [SkillGap]}
├── roadmaps: {role_name: [LearningPath]}
├── top_roles: [str]
└── predicted_roles: [str]
```

## 🔍 Troubleshooting

- **Setup issues**: Check `QUICKSTART.md`
- **Low scores**: Verify skills in taxonomy, check synonyms
- **Import errors**: Run `pip install -r requirements.txt`
- **Model errors**: Run `python -m spacy download en_core_web_sm`

## 📞 Next Steps

1. ✅ Read PROJECT_SUMMARY.md
2. ✅ Install dependencies (QUICKSTART.md)
3. ✅ Run example script
4. ✅ Analyze your own resume
5. ✅ Customize job roles and skills
6. ✅ Extend functionality as needed

---

**Start with**: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for a simple explanation!
**Then read**: [QUICKSTART.md](QUICKSTART.md) to get started!

