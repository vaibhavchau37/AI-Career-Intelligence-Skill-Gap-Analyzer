# PDF Resume Parsing & Skill Mapping Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Parse a PDF Resume

```bash
python examples/parse_pdf_resume.py your_resume.pdf
```

This will:
- Extract text from PDF
- Parse skills, education, experience, projects
- Save structured JSON output

### 3. Compare Skills with Job Roles

```bash
python examples/skill_mapping_comparison.py
```

### 4. Complete Analysis (PDF + Comparison)

```bash
python examples/complete_analysis_pdf.py your_resume.pdf
```

## What's Included

### 📄 PDF Resume Parser (`src/core/pdf_resume_parser.py`)

**Features**:
- Extracts text from PDF files (uses free pdfplumber library)
- Parses skills, education, experience, projects
- Uses spaCy for NLP entity extraction
- Outputs structured JSON

**Usage**:
```python
from src.core.pdf_resume_parser import PDFResumeParser

parser = PDFResumeParser()
result = parser.parse_pdf("resume.pdf")

print(result['skills'])      # List of skills
print(result['education'])   # List of education entries
print(result['experience'])  # List of work experience
print(result['projects'])    # List of projects

# Save as JSON
json_output = parser.parse_to_json("resume.pdf", "output.json")
```

### 🎯 Skill Mapping System (`data/job_roles/skill_mapping.json`)

**Job Roles Included**:
- ML Engineer
- Data Scientist
- Data Analyst
- AI Engineer
- Python Developer

Each role has:
- **Required Skills**: Must-have skills
- **Optional Skills**: Nice-to-have skills

**Usage**:
```python
from examples.skill_mapping_comparison import SkillMappingComparator

comparator = SkillMappingComparator()

# Compare resume skills with a role
result = comparator.compare_skills(
    resume_skills=["Python", "Machine Learning", "SQL"],
    role_name="ML Engineer"
)

print(f"Match: {result['overall_match_percentage']}%")
print(f"Missing: {result['missing_required']}")

# Compare with all roles
results = comparator.compare_all_roles(resume_skills)
```

## How It Works

### PDF Parsing Process

1. **Text Extraction**: Uses pdfplumber to extract text from PDF
2. **Section Detection**: Finds sections using keywords (Skills, Education, etc.)
3. **Pattern Matching**: Uses regex to extract structured data
4. **NLP Processing**: Uses spaCy to identify entities (companies, dates, etc.)
5. **Data Assembly**: Combines all extracted information into JSON

**See**: `docs/RESUME_PARSING_EXPLAINED.md` for detailed explanation

### Skill Mapping Comparison

1. **Normalize Skills**: Converts all skills to lowercase for comparison
2. **Match Required Skills**: Checks if resume has required skills
3. **Match Optional Skills**: Checks optional skills
4. **Calculate Percentages**: Computes match percentages
5. **Identify Gaps**: Lists missing skills

**See**: `docs/SKILL_MAPPING_EXPLAINED.md` for detailed explanation

## Example Output

### Parsed Resume JSON
```json
{
  "name": "John Doe",
  "email": "john@email.com",
  "skills": ["Python", "Machine Learning", "SQL"],
  "education": [
    {
      "degree": "BS",
      "institution": "State University",
      "year": "2020"
    }
  ],
  "experience": [
    {
      "title": "Software Engineer",
      "company": "Tech Corp",
      "dates": "2020-2022"
    }
  ],
  "projects": [
    "ML Model for Predictions",
    "E-commerce Website"
  ]
}
```

### Skill Comparison Result
```json
{
  "role_name": "ML Engineer",
  "overall_match_percentage": 65.0,
  "required_match_percentage": 75.0,
  "matched_required": ["Python", "Machine Learning", "SQL"],
  "missing_required": ["Deep Learning", "Statistics"],
  "missing_optional": ["TensorFlow", "AWS"]
}
```

## Customization

### Add New Job Role

Edit `data/job_roles/skill_mapping.json`:

```json
{
  "job_roles": {
    "Your Role": {
      "description": "Role description",
      "required_skills": ["Skill1", "Skill2"],
      "optional_skills": ["Skill3", "Skill4"]
    }
  }
}
```

### Modify Skill Extraction

Edit `src/core/pdf_resume_parser.py`:
- Update `_extract_skills()` method
- Add new patterns in `technical_patterns`
- Enhance NLP processing

## Troubleshooting

### PDF Parsing Issues

**Problem**: Cannot extract text from PDF
- **Solution**: Ensure PDF contains text (not scanned images)
- For scanned PDFs, use OCR first (e.g., Tesseract)

**Problem**: spaCy model not found
- **Solution**: Run `python -m spacy download en_core_web_sm`

**Problem**: pdfplumber not installed
- **Solution**: `pip install pdfplumber`

### Skill Matching Issues

**Problem**: Skills not matching
- **Solution**: Check skill names match (case-insensitive)
- Add synonyms to skill mapping if needed
- Improve normalization in `_normalize_skill()` method

**Problem**: Low match percentages
- **Solution**: Ensure resume lists skills clearly
- Check if skill names are standard (use mapping file as reference)

## Next Steps

1. **Try Examples**: Run the example scripts
2. **Parse Your Resume**: Use your own PDF resume
3. **Customize Roles**: Add/modify job roles
4. **Improve Extraction**: Enhance parsing logic for your needs
5. **Integrate**: Use in your career analysis system

## Files Reference

- **PDF Parser**: `src/core/pdf_resume_parser.py`
- **Skill Mapping**: `data/job_roles/skill_mapping.json`
- **Parser Example**: `examples/parse_pdf_resume.py`
- **Comparison Example**: `examples/skill_mapping_comparison.py`
- **Complete Example**: `examples/complete_analysis_pdf.py`
- **Documentation**: `docs/RESUME_PARSING_EXPLAINED.md`, `docs/SKILL_MAPPING_EXPLAINED.md`

## Support

For detailed explanations:
- Resume Parsing: See `docs/RESUME_PARSING_EXPLAINED.md`
- Skill Mapping: See `docs/SKILL_MAPPING_EXPLAINED.md`
- General: See `README.md` and `QUICKSTART.md`

