# Detailed Architecture Documentation

## System Overview

The AI Career Intelligence & Skill Gap Analyzer is a lightweight, modular Python application designed to analyze resumes against job roles and generate personalized recommendations.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      INPUT LAYER                             │
│                   (Resume Text File)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  PROCESSING LAYER                            │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │ Resume       │─────▶│ Skill        │                    │
│  │ Parser       │      │ Extractor    │                    │
│  └──────┬───────┘      └──────┬───────┘                    │
│         │                     │                             │
│         ▼                     ▼                             │
│  ┌──────────────────────────────────────┐                  │
│  │      Structured Resume Data          │                  │
│  └──────────────────────────────────────┘                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  ANALYSIS LAYER                              │
│                                                              │
│  For each Job Role:                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Skill        │─▶│ Score        │─▶│ Gap          │     │
│  │ Matcher      │  │ Calculator   │  │ Analyzer     │     │
│  └──────────────┘  └──────────────┘  └──────┬───────┘     │
│                                               │             │
│                                               ▼             │
│                                     ┌──────────────┐       │
│                                     │ Roadmap      │       │
│                                     │ Generator    │       │
│                                     └──────────────┘       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  OUTPUT LAYER                                │
│                                                              │
│  • Job Readiness Scores (0-100)                             │
│  • Skill Gap Analysis                                       │
│  • Learning Roadmaps                                        │
│  • Role Recommendations                                     │
│  • Detailed Explanations                                    │
└─────────────────────────────────────────────────────────────┘
```

## Module Interactions

### Sequence Diagram

```
User → CareerAnalyzer → ResumeParser → Resume Object
                              ↓
                    SkillExtractor → Skill List
                              ↓
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   SkillMatcher        ScoreCalculator      SkillGapAnalyzer
        │                     │                     │
        └──────────┬──────────┴──────────┬──────────┘
                   │                     │
                   ▼                     ▼
              JobMatcher         RoadmapGenerator
                   │                     │
                   └──────────┬──────────┘
                              ▼
                        AnalysisResult
```

## Component Details

### 1. Data Models

#### Resume Model
```python
Resume:
  - Basic Info: name, email, phone
  - Skills: technical_skills, soft_skills
  - Experience: years_of_experience, experience_items
  - Education: degrees, certifications
  - Sections: List[ResumeSection]
```

#### JobRole Model
```python
JobRole:
  - Metadata: name, description
  - Requirements:
    - required_skills: List[SkillRequirement]
    - preferred_skills: List[SkillRequirement]
    - min_years_experience: float
    - required_degrees: List[str]
  - Certifications: List[str]
```

#### AnalysisResult Model
```python
AnalysisResult:
  - scores: Dict[str, RoleScore]
  - skill_gaps: Dict[str, List[SkillGap]]
  - roadmaps: Dict[str, List[LearningPath]]
  - top_roles: List[str]
  - predicted_roles: List[str]
  - summary: str
```

### 2. Core Processing Modules

#### ResumeParser
**Input**: Raw resume text (string)
**Output**: Resume object
**Algorithm**:
1. Section detection (regex-based)
2. Entity extraction (spaCy or regex)
3. Information extraction (email, phone, dates)
4. Structured data assembly

#### SkillExtractor
**Input**: Resume object
**Output**: List of canonical skill names
**Algorithm**:
1. Load skill taxonomy
2. Normalize skill names
3. Match against taxonomy
4. Resolve synonyms
5. Return unique skills

#### SkillMatcher
**Input**: Resume skills, JobRole requirements
**Output**: Matching results (matched/missing)
**Algorithm**:
1. Normalize all skill names
2. Exact matching
3. Fuzzy matching (Levenshtein distance)
4. Optional: Semantic similarity (embeddings)
5. Categorize (matched/missing)

#### ScoreCalculator
**Input**: Resume, JobRole, Skill match results
**Output**: Score breakdown (0-100)
**Algorithm**:
1. Calculate component scores:
   - Required skills: (matched / total) × 100
   - Preferred skills: (matched / total) × 100
   - Experience: Linear scaling based on years
   - Education: Boolean + preference matching
   - Certifications: Percentage matching
2. Apply weights
3. Sum to get overall score

### 3. Matching & Prediction

#### JobMatcher
**Algorithm**:
1. Score resume against each role
2. Sort by score (descending)
3. Return top N matches

#### RolePredictor
**Algorithm**:
1. Calculate skill overlap for each role
2. Score = (overlap_ratio × 0.7) + (matched_count_factor × 0.3)
3. Sort and return top N

### 4. Roadmap Generation

#### SkillGapAnalyzer
**Algorithm**:
1. Identify missing skills from match results
2. Categorize (required vs preferred)
3. Sort by importance

#### RoadmapGenerator
**Algorithm**:
1. Prioritize gaps (required first)
2. Estimate learning time per skill
3. Map skills to resources
4. Identify prerequisites
5. Create timeline

## Data Flow Example

### Input
```
Resume Text:
"John Doe
Software Engineer with 2 years Python experience.
Skills: Python, SQL, Machine Learning
Education: BS Computer Science"
```

### Processing Steps

1. **Parse**:
   ```
   Resume {
     name: "John Doe"
     years_of_experience: 2.0
     skills: ["Python", "SQL", "Machine Learning"]
     degrees: ["BS"]
   }
   ```

2. **Extract Skills**:
   ```
   Skills: ["Python", "SQL", "Machine Learning"]
   ```

3. **Match Against ML Engineer Role**:
   ```
   Required: ["Python", "Machine Learning", "Deep Learning", ...]
   Matched: ["Python", "Machine Learning"]
   Missing: ["Deep Learning", "Statistics", ...]
   ```

4. **Calculate Score**:
   ```
   Required Skills: 2/5 = 40%
   Preferred Skills: ...
   Experience: 2 years / 3 preferred = 67%
   Overall: (40×0.4) + ... = 58/100
   ```

5. **Generate Roadmap**:
   ```
   1. Deep Learning (14 days)
   2. Statistics (14 days)
   ...
   ```

### Output
```json
{
  "top_roles": ["ML Engineer"],
  "scores": {
    "ML Engineer": {
      "overall_score": 58.0,
      "breakdown": {...},
      "missing_skills": ["Deep Learning", "Statistics"]
    }
  },
  "roadmaps": {
    "ML Engineer": [
      {"skill": "Deep Learning", "days": 14, ...}
    ]
  }
}
```

## Configuration System

Configuration is hierarchical:

```yaml
scoring:              # Scoring weights
skill_matching:       # Matching parameters
job_roles:           # Role data paths
skills:              # Skill taxonomy paths
roadmap:             # Roadmap settings
nlp:                 # NLP settings
output:              # Output settings
```

## Extensibility Points

1. **Job Roles**: Add YAML files to `data/job_roles/`
2. **Skills**: Extend `skill_taxonomy.json`
3. **Scoring**: Modify `ScoreCalculator` or weights in config
4. **Matching**: Enhance `SkillMatcher` with better algorithms
5. **Roadmaps**: Extend `RoadmapGenerator` with more resources

## Performance Characteristics

- **Resume Parsing**: ~100-200ms
- **Skill Extraction**: ~50-100ms
- **Role Analysis**: ~50-100ms per role
- **Total**: < 1 second for typical resume + 2-3 roles

## Error Handling Strategy

1. **Missing Dependencies**: Graceful degradation
2. **Invalid Input**: Validation and clear error messages
3. **Missing Data**: Default values and warnings
4. **Processing Errors**: Try-except with logging

## Testing Strategy

- **Unit Tests**: Each module tested independently
- **Integration Tests**: Full workflow testing
- **Data Tests**: Validate with various resume formats
- **Edge Cases**: Empty resumes, missing sections, etc.

## Future Enhancements

1. ML-based skill matching (optional)
2. Web UI with Streamlit
3. Batch processing API
4. Database integration
5. A/B testing framework
6. Custom scoring functions
7. Resume parsing from PDF/DOCX
8. Real-time learning resource updates

