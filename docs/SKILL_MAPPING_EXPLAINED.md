# Job Role Skill Mapping Explained

## Overview

Skill mapping is a system that defines what skills are needed for different job roles. We then compare a person's resume skills against these requirements to determine job readiness.

## What is Skill Mapping?

**Skill Mapping** = A database that lists:
- **Required Skills**: Must-have skills for a job role
- **Optional Skills**: Nice-to-have skills that improve candidacy

**Example**:
```
ML Engineer:
  Required: Python, Machine Learning, Statistics
  Optional: TensorFlow, AWS, Docker
```

## How We Store Skill Mappings

We use **JSON format** because it's:
- Human-readable (easy to edit)
- Programmatically accessible (easy to process)
- Structured (organized data)

**Structure**:
```json
{
  "job_roles": {
    "ML Engineer": {
      "description": "...",
      "required_skills": ["Python", "Machine Learning", ...],
      "optional_skills": ["TensorFlow", "AWS", ...]
    },
    "Data Scientist": {
      ...
    }
  }
}
```

## Why Skill Mapping is Important

1. **Standardization**: Defines clear requirements for each role
2. **Comparison**: Enables automated skill matching
3. **Gap Analysis**: Identifies what skills are missing
4. **Career Planning**: Shows what to learn for target roles

## How Skill Comparison Works

### Step-by-Step Process

#### Step 1: Normalize Skills

**Problem**: Skills can be written differently:
- "Python" vs "python" vs "Python Programming"
- "Machine Learning" vs "ML" vs "machine-learning"

**Solution**: Normalize all skill names for comparison.

```python
def normalize_skill(skill):
    return skill.lower().strip().replace(' ', '').replace('-', '')
```

**Example**:
- "Python" → "python"
- "Machine Learning" → "machinelearning"
- "ML" → "ml"

#### Step 2: Match Required Skills

**Process**:
1. For each required skill in job role
2. Check if it exists in resume skills (after normalization)
3. Use substring matching (handles variations)

**Example**:
```
Job Role Required: ["Python", "Machine Learning"]
Resume Skills: ["Python Programming", "ML", "SQL"]

Normalized Job: ["python", "machinelearning"]
Normalized Resume: ["pythonprogramming", "ml", "sql"]

Matching:
- "python" in "pythonprogramming" → ✅ Match!
- "machinelearning" in "ml" → ❌ No match (but could improve)
```

**Result**: Found 1/2 required skills → 50% match

#### Step 3: Match Optional Skills

Same process as required skills, but these are "nice-to-have".

**Example**:
```
Job Role Optional: ["TensorFlow", "AWS", "Docker"]
Resume Skills: ["Python", "AWS", "SQL"]

Matching:
- "TensorFlow" → ❌ Not found
- "AWS" → ✅ Match!
- "Docker" → ❌ Not found
```

**Result**: Found 1/3 optional skills → 33% match

#### Step 4: Calculate Match Percentages

**Required Skills Match**:
```
Match % = (Matched Required Skills / Total Required Skills) × 100
```

**Optional Skills Match**:
```
Match % = (Matched Optional Skills / Total Optional Skills) × 100
```

**Overall Match** (weighted):
```
Overall % = (Required Match × 70%) + (Optional Match × 30%)
```

Why 70/30? Required skills are more important!

**Example**:
```
Required: 2/5 matched = 40%
Optional: 3/10 matched = 30%

Overall = (40% × 0.7) + (30% × 0.3) = 28% + 9% = 37%
```

#### Step 5: Identify Missing Skills

**Missing Required Skills**: Required skills not found in resume
**Missing Optional Skills**: Optional skills not found in resume

**Example**:
```
Required: ["Python", "Machine Learning", "SQL"]
Resume: ["Python", "Data Analysis"]

Missing Required: ["Machine Learning", "SQL"]
```

## How Skill Mapping is Used

### 1. Resume Analysis

Compare resume skills against job requirements:

```python
comparator = SkillMappingComparator()
result = comparator.compare_skills(resume_skills, "ML Engineer")

print(f"Match: {result['overall_match_percentage']}%")
print(f"Missing: {result['missing_required']}")
```

### 2. Job Readiness Scoring

Calculate how ready someone is for a role:

```
Score = Overall Match Percentage

80-100%: Well-qualified
60-79%:  Good fit, minor gaps
40-59%:  Moderate fit, needs improvement
0-39%:   Poor fit, significant gaps
```

### 3. Skill Gap Analysis

Identify what to learn:

```
Missing Required Skills = Learning Priorities
```

### 4. Role Comparison

Compare against multiple roles:

```python
results = comparator.compare_all_roles(resume_skills)
# Returns list sorted by match percentage
```

**Use Case**: "Which roles am I best suited for?"

## Example: Complete Workflow

### Input
```json
Resume Skills: ["Python", "SQL", "Pandas", "Git"]
Target Role: "Data Scientist"
```

### Skill Mapping for Data Scientist
```json
{
  "required_skills": ["Python", "Data Analysis", "Statistics", "SQL", "Pandas"],
  "optional_skills": ["NumPy", "Matplotlib", "Machine Learning", "Jupyter"]
}
```

### Comparison Process

1. **Normalize**:
   - Resume: ["python", "sql", "pandas", "git"]
   - Required: ["python", "dataanalysis", "statistics", "sql", "pandas"]

2. **Match Required**:
   - "Python" → ✅ Found
   - "Data Analysis" → ❌ Not found
   - "Statistics" → ❌ Not found
   - "SQL" → ✅ Found
   - "Pandas" → ✅ Found
   
   Result: 3/5 matched = 60%

3. **Match Optional**:
   - "NumPy" → ❌ Not found
   - "Matplotlib" → ❌ Not found
   - "Machine Learning" → ❌ Not found
   - "Jupyter" → ❌ Not found
   
   Result: 0/4 matched = 0%

4. **Calculate Overall**:
   - Overall = (60% × 0.7) + (0% × 0.3) = 42%

5. **Identify Missing**:
   - Missing Required: ["Data Analysis", "Statistics"]
   - Missing Optional: ["NumPy", "Matplotlib", "Machine Learning", "Jupyter"]

### Output
```json
{
  "role_name": "Data Scientist",
  "overall_match_percentage": 42.0,
  "required_match_percentage": 60.0,
  "optional_match_percentage": 0.0,
  "matched_required": ["Python", "SQL", "Pandas"],
  "missing_required": ["Data Analysis", "Statistics"],
  "matched_optional": [],
  "missing_optional": ["NumPy", "Matplotlib", "Machine Learning", "Jupyter"]
}
```

### Interpretation

- **42% overall match**: Moderate fit, needs improvement
- **Missing critical skills**: Data Analysis, Statistics (must learn!)
- **Action items**: Focus on learning missing required skills first

## Benefits of Skill Mapping System

1. **Objective Assessment**: No bias, data-driven evaluation
2. **Clear Requirements**: Know exactly what's needed
3. **Gap Identification**: Understand what to improve
4. **Career Guidance**: See which roles you're closest to
5. **Learning Roadmap**: Prioritize what to learn

## Customizing Skill Mappings

### Add New Roles

Edit `data/job_roles/skill_mapping.json`:

```json
{
  "job_roles": {
    "New Role": {
      "description": "Role description",
      "required_skills": ["Skill1", "Skill2"],
      "optional_skills": ["Skill3", "Skill4"]
    }
  }
}
```

### Update Existing Roles

Modify the skills arrays in the JSON file:

```json
"ML Engineer": {
  "required_skills": ["Python", "New Skill"],  // Added "New Skill"
  "optional_skills": [...]
}
```

### Best Practices

1. **Be Specific**: Use standard skill names (e.g., "Python" not "python programming")
2. **Prioritize**: Required skills should be truly essential
3. **Keep Updated**: Add emerging technologies
4. **Validate**: Test with real resumes

## Summary

Skill mapping is a systematic way to:
- Define job requirements
- Compare candidate skills
- Identify gaps
- Guide career development

The comparison process:
1. Normalizes skill names
2. Matches resume skills with requirements
3. Calculates percentages
4. Identifies missing skills
5. Provides actionable insights

This enables data-driven career analysis and skill development planning!

