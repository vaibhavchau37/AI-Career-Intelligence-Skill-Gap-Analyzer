# System Architecture - Detailed Documentation

## Overview

The AI Career Intelligence & Skill Gap Analyzer is designed as a lightweight, modular Python application that analyzes resumes against job roles without requiring heavy model training.

## Architecture Layers

### 1. Data Layer

**Purpose**: Store and manage data structures and configurations

**Components**:
- **Job Role Definitions** (`data/job_roles/*.yaml`): YAML files defining job requirements
- **Skill Taxonomy** (`data/skills/skill_taxonomy.json`): Hierarchical skill categorization
- **Skill Synonyms** (`data/skills/skill_synonyms.json`): Skill name variations and aliases

**Design Decision**: YAML for job roles (human-readable, easy to edit) and JSON for skill data (structured, programmatic access).

### 2. Core Processing Layer

**Purpose**: Extract, match, and score resume data

#### 2.1 Resume Parser (`src/core/resume_parser.py`)

**Responsibilities**:
- Parse raw resume text into structured format
- Extract sections (Education, Experience, Skills, etc.)
- Extract basic information (name, email, phone)
- Identify years of experience
- Extract degrees and certifications

**Algorithm**:
- Rule-based parsing using regex patterns
- Section detection using keyword matching
- Entity extraction using spaCy (optional, lightweight model)

**Output**: `Resume` object with structured data

#### 2.2 Skill Extractor (`src/core/skill_extractor.py`)

**Responsibilities**:
- Identify skills from resume text
- Match skills against taxonomy
- Handle synonyms and variations
- Categorize skills (technical vs soft)

**Algorithm**:
- Keyword matching against skill taxonomy
- Synonym resolution
- Normalization for fuzzy matching
- Pattern matching for common technical terms

**Output**: List of canonical skill names

#### 2.3 Skill Matcher (`src/core/skill_matcher.py`)

**Responsibilities**:
- Match resume skills with job requirements
- Identify matched and missing skills
- Handle skill name variations

**Algorithm**:
- Exact matching (normalized names)
- Fuzzy string matching (fuzzywuzzy library)
- Optional: Semantic similarity (sentence-transformers, if enabled)

**Output**: Matching results with matched/missing skills

#### 2.4 Score Calculator (`src/core/score_calculator.py`)

**Responsibilities**:
- Calculate job readiness score (0-100)
- Compute component scores (skills, experience, education, etc.)
- Apply weighted scoring

**Algorithm**:
- Weighted sum of component scores
- Normalized percentage calculations
- Linear scaling for experience and education

**Scoring Formula**:
```
Overall Score = 
  (Required Skills Match % × 40%) +
  (Preferred Skills Match % × 20%) +
  (Experience Score × 20%) +
  (Education Score × 10%) +
  (Certifications Score × 10%)
```

**Output**: Score breakdown and overall score

### 3. Matching & Prediction Layer

#### 3.1 Job Matcher (`src/matcher/job_matcher.py`)

**Responsibilities**:
- Match resume against multiple job roles
- Rank roles by suitability
- Provide top N recommendations

**Algorithm**:
- Score resume against each role
- Sort by overall score
- Return ranked list

#### 3.2 Role Predictor (`src/matcher/role_predictor.py`)

**Responsibilities**:
- Predict suitable roles based on skills
- Suggest roles user might not have considered

**Algorithm**:
- Skill overlap analysis
- Similarity scoring based on matched skills
- Ranking by overlap ratio

### 4. Roadmap Generation Layer

#### 4.1 Skill Gap Analyzer (`src/roadmap/skill_gaps.py`)

**Responsibilities**:
- Identify missing skills
- Categorize gaps (required vs preferred)
- Prioritize gaps by importance

**Output**: List of `SkillGap` objects

#### 4.2 Roadmap Generator (`src/roadmap/roadmap_generator.py`)

**Responsibilities**:
- Create learning paths for missing skills
- Estimate learning time
- Suggest learning resources
- Identify prerequisites

**Algorithm**:
- Prioritize gaps (required > preferred)
- Estimate days based on skill complexity
- Map skills to learning resources
- Identify skill dependencies

**Output**: List of `LearningPath` objects

### 5. Application Layer

#### 5.1 Career Analyzer (`src/analyzer/career_analyzer.py`)

**Purpose**: Main orchestrator

**Responsibilities**:
- Coordinate all modules
- Load configurations and data
- Provide simple API
- Generate complete analysis results

**Workflow**:
```
1. Load configuration and job roles
2. Parse resume text → Resume object
3. Extract skills → Skill list
4. For each target role:
   a. Match skills
   b. Calculate score
   c. Analyze gaps
   d. Generate roadmap
5. Rank roles
6. Predict additional roles
7. Generate summary
8. Return AnalysisResult
```

## Data Flow

```
Input: Resume Text
  ↓
[Resume Parser] → Resume Object
  ↓
[Skill Extractor] → Skill List
  ↓
For each Job Role:
  ├─→ [Skill Matcher] → Matched/Missing Skills
  ├─→ [Score Calculator] → Score (0-100)
  ├─→ [Skill Gap Analyzer] → Skill Gaps
  └─→ [Roadmap Generator] → Learning Roadmap
  ↓
[Job Matcher] → Ranked Roles
  ↓
[Role Predictor] → Suggested Roles
  ↓
Output: AnalysisResult
```

## Key Design Decisions

### 1. No Heavy Training
- Uses pre-trained spaCy model (lightweight, ~50MB)
- Rule-based parsing and matching
- Optional semantic similarity (sentence-transformers, but not required)

### 2. Modularity
- Each module is independent and testable
- Clear interfaces between modules
- Easy to swap implementations

### 3. Explainability
- Every score has clear breakdown
- Explanations generated for each recommendation
- Transparent scoring algorithm

### 4. Extensibility
- Easy to add new job roles (just add YAML file)
- Skill taxonomy can be extended
- Scoring weights configurable

### 5. Performance
- Efficient for normal laptop usage
- No GPU required
- Fast processing for single resume (< 1 second)

## Configuration

Configuration is stored in `config.yaml`:

- **Scoring weights**: Adjust importance of different factors
- **Matching thresholds**: Control skill matching sensitivity
- **Roadmap settings**: Timeline and prioritization options
- **Data paths**: Where to find job roles and skill taxonomy

## Error Handling

- Graceful degradation: If spaCy model not installed, falls back to regex
- Default job roles: If no YAML files found, uses built-in defaults
- Missing data: Handles missing sections gracefully

## Future Enhancements

1. **ML-based matching**: Add optional ML model for better skill matching
2. **Web UI**: Add Streamlit interface
3. **Batch processing**: Analyze multiple resumes
4. **Custom scoring**: Allow users to define custom scoring functions
5. **API endpoints**: REST API for integration
6. **Database integration**: Store resumes and results
7. **A/B testing**: Compare different scoring strategies

## Testing Strategy

- Unit tests for each module
- Integration tests for full workflow
- Test with various resume formats
- Validate scoring consistency

