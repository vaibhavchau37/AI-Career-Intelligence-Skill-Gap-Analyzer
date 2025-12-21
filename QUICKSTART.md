# Quick Start Guide

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install spaCy Language Model (Optional but Recommended)

```bash
python -m spacy download en_core_web_sm
```

**Note**: If you skip this step, the system will work but with limited NLP capabilities (entity extraction will be disabled).

## Basic Usage

### Using the Example Script

The easiest way to get started is using the provided example script:

```bash
python examples/analyze_resume.py
```

This will analyze the sample resume in `data/examples/sample_resume.txt` against available job roles.

### Using in Your Code

```python
from src.analyzer.career_analyzer import CareerAnalyzer

# Initialize analyzer
analyzer = CareerAnalyzer()

# Analyze resume
with open("your_resume.txt", "r") as f:
    resume_text = f.read()

result = analyzer.analyze(
    resume_text=resume_text,
    target_roles=["ML Engineer", "Data Scientist"]  # Optional
)

# Access results
print(f"Top Role: {result.top_roles[0]}")
print(f"Score: {result.get_role_score(result.top_roles[0])}")

# Get skill gaps
for role_name, gaps in result.skill_gaps.items():
    print(f"\n{role_name} - Missing Skills:")
    for gap in gaps:
        print(f"  - {gap.skill} ({gap.category})")

# Get learning roadmap
for role_name, roadmap in result.roadmaps.items():
    print(f"\n{role_name} - Learning Path:")
    for item in roadmap[:5]:  # Top 5
        print(f"  {item.skill}: {item.estimated_days} days")
```

## Adding Custom Job Roles

1. Create a YAML file in `data/job_roles/` directory
2. Follow this structure:

```yaml
name: Your Job Role Name
description: Brief description of the role

required_skills:
  - name: Skill Name
    importance: 1.0
    description: Optional description

preferred_skills:
  - name: Skill Name
    importance: 0.8

min_years_experience: 2.0
preferred_years_experience: 3.0

required_degrees:
  - BS
  - Bachelor

preferred_degrees:
  - MS
  - Master
```

3. The analyzer will automatically load it on next run

## Customizing Scoring

Edit `config.yaml` to adjust scoring weights:

```yaml
scoring:
  required_skills: 40      # Increase to emphasize required skills
  preferred_skills: 20
  experience: 20
  education: 10
  certifications: 10
```

**Note**: Weights should ideally sum to 100, but the system normalizes them automatically.

## Extending Skill Taxonomy

Edit `data/skills/skill_taxonomy.json` to add new skills:

```json
{
  "your_category": [
    "Skill 1",
    "Skill 2"
  ]
}
```

Add synonyms in `data/skills/skill_synonyms.json`:

```json
{
  "Skill Name": ["synonym1", "synonym2", "alternative name"]
}
```

## Troubleshooting

### "spaCy model not found"
- Run: `python -m spacy download en_core_web_sm`
- Or continue without it (some features will be disabled)

### "No job roles found"
- Check that `data/job_roles/` contains YAML files
- System will use default ML Engineer role if none found

### Low scores
- Check if skills in resume match skill taxonomy
- Add synonyms if skills are named differently
- Adjust scoring weights in config.yaml

## Next Steps

1. **Analyze your own resume**: Replace sample resume with yours
2. **Add more job roles**: Create YAML files for roles you're interested in
3. **Customize skill taxonomy**: Add skills relevant to your field
4. **Adjust scoring**: Modify weights to match your priorities
5. **Extend the system**: Add custom modules or features

For detailed architecture information, see `ARCHITECTURE.md`.

