# User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Analyzing a Resume](#analyzing-a-resume)
4. [Understanding Results](#understanding-results)
5. [Customization](#customization)
6. [Best Practices](#best-practices)

## Introduction

The AI Career Intelligence & Skill Gap Analyzer helps you:
- Understand your readiness for different job roles
- Identify skill gaps
- Get personalized learning roadmaps
- Discover suitable career paths

## Getting Started

### Installation

See `QUICKSTART.md` for detailed installation instructions.

### Basic Workflow

1. Prepare your resume in text format
2. Run the analyzer
3. Review scores and recommendations
4. Explore skill gaps
5. Follow the learning roadmap

## Analyzing a Resume

### Input Format

Your resume should be in plain text format (.txt). The parser can handle various formats but works best with clear sections:

```
Name
Contact Information

PROFESSIONAL SUMMARY
...

EXPERIENCE
...

EDUCATION
...

SKILLS
...

PROJECTS
...
```

### Running Analysis

```python
from src.analyzer.career_analyzer import CareerAnalyzer

analyzer = CareerAnalyzer()
result = analyzer.analyze(resume_text, target_roles=["ML Engineer"])
```

## Understanding Results

### Score Breakdown

Each role receives a score from 0-100 based on:

- **Required Skills (40%)**: How many required skills you have
- **Preferred Skills (20%)**: How many preferred skills you have
- **Experience (20%)**: Years of experience vs. requirements
- **Education (10%)**: Degree alignment
- **Certifications (10%)**: Relevant certifications

### Score Interpretation

- **80-100**: Excellent fit, you're well-qualified
- **65-79**: Good fit, minor gaps to address
- **50-64**: Moderate fit, needs improvement
- **35-49**: Poor fit, significant gaps
- **0-34**: Very poor fit, consider different roles or major upskilling

### Skill Gaps

Gaps are categorized as:
- **Required**: Must-have skills you're missing (critical)
- **Preferred**: Nice-to-have skills (less critical)

Gaps are sorted by importance, with required skills first.

### Learning Roadmaps

Roadmaps include:
- Skills to learn (prioritized)
- Estimated time to learn each skill
- Learning resources
- Prerequisites

## Customization

### Adding Job Roles

1. Create a YAML file in `data/job_roles/`
2. Define required and preferred skills
3. Set experience and education requirements
4. Restart the analyzer

See `data/job_roles/ml_engineer.yaml` for an example.

### Adjusting Scoring

Edit `config.yaml` to change scoring weights:

```yaml
scoring:
  required_skills: 50  # Increase emphasis on required skills
  experience: 30       # Increase emphasis on experience
  # ... other weights
```

### Extending Skills

Add skills to `data/skills/skill_taxonomy.json`:

```json
{
  "your_category": ["Skill1", "Skill2"]
}
```

Add synonyms to help matching:

```json
{
  "TensorFlow": ["tf", "tensorflow", "tensor flow"]
}
```

## Best Practices

### Resume Formatting

1. **Clear sections**: Use standard section headers (Experience, Education, Skills)
2. **Skill list**: Include a dedicated Skills section
3. **Quantify experience**: Mention years (e.g., "2 years of Python")
4. **Be specific**: List specific technologies and tools
5. **Include projects**: Mention relevant projects

### Interpreting Results

1. **Focus on top roles**: Start with highest-scoring roles
2. **Prioritize gaps**: Address required skills first
3. **Check explanations**: Read score explanations for context
4. **Consider roadmaps**: Use learning paths as guidance
5. **Compare roles**: Analyze multiple roles to find best fit

### Skill Matching

1. **Use standard names**: Match skill names in taxonomy when possible
2. **Add synonyms**: If skills have different names, add to synonyms file
3. **Be comprehensive**: Include all relevant skills in resume
4. **Update taxonomy**: Add missing skills to taxonomy

### Scoring

1. **Understand weights**: Know what each component contributes
2. **Adjust if needed**: Modify weights to match your priorities
3. **Compare fairly**: Compare scores within same configuration
4. **Consider context**: Scores are relative, not absolute

## Common Questions

### Q: Why is my score low?

A: Check:
- Are your skills listed in the resume?
- Do skill names match the taxonomy?
- Are required skills present?
- Is experience mentioned clearly?

### Q: How accurate is the scoring?

A: The scoring is rule-based and transparent. It reflects:
- Skill matching accuracy
- How well your profile matches job requirements
- The weights you've configured

Accuracy improves with:
- Better skill taxonomy
- More complete resume information
- Properly configured job roles

### Q: Can I add my own scoring logic?

A: Yes! Modify `src/core/score_calculator.py` to customize scoring algorithms.

### Q: How do I add learning resources?

A: Edit `src/roadmap/roadmap_generator.py` and modify the `_get_learning_resources()` method.

### Q: Can I use this with multiple resumes?

A: Yes, run the analyzer multiple times with different resume texts. For batch processing, create a script that loops through multiple resumes.

## Tips for Best Results

1. **Keep resume updated**: Ensure all recent skills and experience are included
2. **Be thorough**: Include all relevant skills, even if minor
3. **Update job roles**: Add roles you're specifically targeting
4. **Refine taxonomy**: Continuously improve skill taxonomy based on results
5. **Iterate**: Re-analyze after updating resume or skills

## Getting Help

- Check `ARCHITECTURE.md` for technical details
- See `QUICKSTART.md` for setup help
- Review example code in `examples/`
- Examine sample data in `data/`

