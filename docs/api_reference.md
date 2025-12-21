# API Reference

## CareerAnalyzer

Main orchestrator class for career analysis.

### `__init__(config_path: str = "config.yaml")`

Initialize the career analyzer.

**Parameters**:
- `config_path` (str): Path to configuration YAML file

**Example**:
```python
analyzer = CareerAnalyzer("config.yaml")
```

### `analyze(resume_text: str, target_roles: Optional[List[str]] = None) -> AnalysisResult`

Analyze a resume against job roles.

**Parameters**:
- `resume_text` (str): Raw resume text to analyze
- `target_roles` (Optional[List[str]]): List of target role names. If None, analyzes against all available roles.

**Returns**:
- `AnalysisResult`: Complete analysis result object

**Example**:
```python
result = analyzer.analyze(
    resume_text="...",
    target_roles=["ML Engineer", "Data Scientist"]
)
```

## AnalysisResult

Result object containing complete analysis.

### Attributes

- `resume_name` (Optional[str]): Name from resume
- `scores` (Dict[str, RoleScore]): Scores for each role
- `skill_gaps` (Dict[str, List[SkillGap]]): Skill gaps per role
- `roadmaps` (Dict[str, List[LearningPath]]): Learning roadmaps per role
- `predicted_roles` (List[str]): Predicted suitable roles
- `top_roles` (List[str]): Top recommended roles (ranked)
- `summary` (str): Summary text

### Methods

#### `get_top_role() -> Optional[str]`

Get the top recommended role name.

**Returns**: Role name string or None

#### `get_role_score(role_name: str) -> Optional[float]`

Get overall score for a specific role.

**Parameters**:
- `role_name` (str): Name of the role

**Returns**: Score (0-100) or None if role not found

#### `to_dict() -> Dict`

Convert result to dictionary for JSON serialization.

**Returns**: Dictionary representation

## RoleScore

Score breakdown for a specific job role.

### Attributes

- `role_name` (str): Name of the role
- `overall_score` (float): Overall score (0-100)
- `breakdown` (Dict[str, float]): Score breakdown by category
- `explanation` (str): Human-readable explanation
- `matched_skills` (List[str]): List of matched skills
- `missing_skills` (List[SkillGap]): List of missing skills
- `experience_score` (float): Experience component score
- `education_score` (float): Education component score
- `skill_score` (float): Skills component score

## SkillGap

Represents a missing skill.

### Attributes

- `skill` (str): Skill name
- `category` (str): "required" or "preferred"
- `importance` (float): Importance weight (0-1)
- `description` (Optional[str]): Skill description
- `learning_resources` (List[str]): Suggested learning resources

## LearningPath

A learning path item for skill improvement.

### Attributes

- `skill` (str): Skill to learn
- `priority` (int): Priority (1 = highest)
- `estimated_days` (int): Estimated days to learn
- `resources` (List[str]): Learning resources
- `prerequisites` (List[str]): Prerequisite skills

## Resume

Structured resume representation.

### Attributes

- `raw_text` (str): Original resume text
- `name` (Optional[str]): Name from resume
- `email` (Optional[str]): Email address
- `phone` (Optional[str]): Phone number
- `skills` (List[str]): All skills
- `technical_skills` (List[str]): Technical skills
- `soft_skills` (List[str]): Soft skills
- `years_of_experience` (float): Years of experience
- `education` (List[Dict]): Education entries
- `degrees` (List[str]): Degree names
- `certifications` (List[str]): Certifications
- `projects` (List[str]): Projects

### Methods

#### `get_section(name: str) -> Optional[ResumeSection]`

Get a specific section by name.

#### `get_all_skills() -> List[str]`

Get all skills (technical + soft).

#### `to_dict() -> Dict`

Convert to dictionary.

## JobRole

Job role definition.

### Attributes

- `name` (str): Role name
- `description` (str): Role description
- `required_skills` (List[SkillRequirement]): Required skills
- `preferred_skills` (List[SkillRequirement]): Preferred skills
- `min_years_experience` (float): Minimum years
- `preferred_years_experience` (float): Preferred years
- `required_degrees` (List[str]): Required degrees
- `preferred_degrees` (List[str]): Preferred degrees
- `certifications` (List[str]): Certifications
- `preferred_certifications` (List[str]): Preferred certifications

### Methods

#### `get_all_required_skills() -> List[str]`

Get list of required skill names.

#### `get_all_preferred_skills() -> List[str]`

Get list of preferred skill names.

#### `get_all_skills() -> List[str]`

Get all skills (required + preferred).

#### `to_dict() -> Dict`

Convert to dictionary.

## Utility Functions

### Text Processing

#### `clean_text(text: str) -> str`

Clean and normalize text.

#### `normalize_skill_name(skill: str) -> str`

Normalize skill name for matching.

#### `extract_email(text: str) -> Optional[str]`

Extract email address from text.

#### `extract_phone(text: str) -> Optional[str]`

Extract phone number from text.

#### `extract_degrees(text: str) -> List[str]`

Extract degree names from text.

### Explanation Generation

#### `generate_score_explanation(score: RoleScore) -> str`

Generate human-readable explanation for a score.

#### `explain_skill_gap(skill_gap: SkillGap) -> str`

Generate explanation for a skill gap.

