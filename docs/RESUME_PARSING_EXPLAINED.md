# Resume Parsing Explained - How It Works

## Overview

Resume parsing is the process of extracting structured information from an unstructured resume document (PDF or text). This document explains how our PDF resume parser works step by step.

## The Challenge

Resumes come in many formats and styles:
- Different section names (e.g., "Experience" vs "Work History")
- Various layouts and structures
- Mixed content (text, tables, bullet points)
- Inconsistent formatting

We need to extract:
- **Skills**: Technical and soft skills
- **Education**: Degrees, institutions, years
- **Experience**: Job titles, companies, dates
- **Projects**: Project descriptions

## Our Solution: Multi-Step Parsing

### Step 1: Extract Text from PDF

**Problem**: PDFs are not plain text - they contain formatting, layout, and sometimes images.

**Solution**: Use PDF parsing libraries to extract text.

```
PDF File → pdfplumber/PyPDF2 → Raw Text
```

**How it works**:
1. Open the PDF file
2. Read each page
3. Extract text while preserving some structure (line breaks)
4. Combine all pages into one text string

**Code Example**:
```python
with pdfplumber.open("resume.pdf") as pdf:
    text = ""
    for page in pdf.pages:
        text += page.extract_text() + "\n"
```

### Step 2: Find Sections

**Problem**: Need to locate where different information is stored.

**Solution**: Pattern matching to find section headers.

**How it works**:
1. Define keywords for each section type:
   - Skills: "skills", "technical skills", "competencies"
   - Education: "education", "academic", "qualifications"
   - Experience: "experience", "work history", "employment"
   - Projects: "projects", "portfolio"

2. Search for these keywords in the text (case-insensitive)

3. Extract text from the section header until the next section header

**Example**:
```
Resume Text:
...
SKILLS
Python, Java, SQL
Machine Learning
...

EDUCATION
BS Computer Science
...
```

Parser finds "SKILLS" → extracts everything until "EDUCATION"

### Step 3: Extract Skills

**Problem**: Skills can be listed in many ways (commas, bullets, sentences).

**Solution**: Multiple extraction strategies.

**How it works**:

**Strategy 1: Parse Skills Section**
- Split by common separators: commas, semicolons, bullet points (•, -, *)
- Clean each item (remove extra spaces, prefixes like "proficient in")

**Strategy 2: Pattern Matching**
- Search entire text for common technology names
- Use regex patterns: `\bpython\b`, `\bmachine learning\b`, etc.

**Strategy 3: NLP Entity Recognition (spaCy)**
- Use spaCy to identify organizations and products
- Filter to find technology-related entities

**Example**:
```
Skills Section: "Python, Machine Learning, SQL"
→ Split by comma → ["Python", "Machine Learning", "SQL"]
```

### Step 4: Extract Education

**Problem**: Education formats vary widely.

**Solution**: Combine pattern matching with NLP.

**How it works**:

1. **Find Education Section**: Locate using keywords

2. **Extract Degrees**: Use regex patterns
   - `\bBS\b`, `\bMS\b`, `\bPhD\b` (with variations)

3. **Extract Institutions**: Use spaCy to identify organizations (ORG entities)

4. **Extract Years**: Pattern match for years (e.g., "2020", "2019-2023")

5. **Combine**: Match degrees with institutions and years based on proximity

**Example**:
```
Education Section:
BS Computer Science
State University, 2020
→ Degree: "BS Computer Science"
→ Institution: "State University" (from spaCy)
→ Year: "2020" (pattern match)
```

### Step 5: Extract Experience

**Problem**: Experience entries have complex structures (titles, companies, dates, descriptions).

**Solution**: Multi-step extraction with NLP.

**How it works**:

1. **Find Experience Section**: Locate using keywords

2. **Extract Organizations**: Use spaCy to identify company names (ORG entities)

3. **Extract Dates**: Use spaCy DATE entities or regex patterns

4. **Extract Job Titles**: Pattern matching (e.g., "Software Engineer at Company")

5. **Group Information**: Match titles, companies, and dates based on proximity

**Example**:
```
Experience Section:
Software Engineer at Tech Corp (2020-2022)
- Developed applications
- Led team of 5

→ Title: "Software Engineer" (pattern: "...at...")
→ Company: "Tech Corp" (spaCy ORG entity)
→ Dates: "2020-2022" (spaCy DATE entity)
```

### Step 6: Extract Projects

**Problem**: Projects can be listed in various formats.

**Solution**: Simple pattern-based extraction.

**How it works**:

1. **Find Projects Section**: Locate using keywords

2. **Split into Items**: Projects are usually separated by:
   - Bullet points (•, -, *)
   - Numbered lists (1., 2.)
   - Line breaks

3. **Clean Each Project**: Remove prefixes, extra whitespace

**Example**:
```
Projects Section:
• E-commerce Website - Built with React
• ML Model for Predictions - Used TensorFlow

→ Split by bullet points
→ ["E-commerce Website - Built with React", "ML Model for Predictions - Used TensorFlow"]
```

## How spaCy Helps

### What is spaCy?

spaCy is a free, open-source NLP library that can:
- Identify named entities (people, organizations, dates, etc.)
- Understand text structure
- Perform linguistic analysis

### How We Use It

1. **Load Model**: `nlp = spacy.load("en_core_web_sm")`

2. **Process Text**: `doc = nlp(resume_text)`

3. **Extract Entities**:
   - `ORG`: Organizations (companies, universities)
   - `DATE`: Dates and years
   - `PERSON`: Person names (usually the resume owner)

4. **Use in Extraction**: Match entities with extracted patterns

**Example**:
```python
doc = nlp("Software Engineer at Google (2020-2022)")

for ent in doc.ents:
    if ent.label_ == "ORG":
        company = ent.text  # "Google"
    elif ent.label_ == "DATE":
        dates = ent.text    # "2020-2022"
```

## Output: Structured JSON

All extracted information is organized into a JSON structure:

```json
{
  "name": "John Doe",
  "email": "john@email.com",
  "phone": "123-456-7890",
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
    "E-commerce Website - Built with React",
    "ML Model for Predictions"
  ]
}
```

## Limitations and Improvements

### Current Limitations

1. **Format Dependency**: Works best with text-based PDFs (scanned PDFs need OCR)

2. **Structure Assumptions**: Assumes certain section names and formats

3. **NLP Accuracy**: spaCy models may miss some entities

4. **Ambiguity**: Hard to distinguish between similar entities

### Possible Improvements

1. **OCR Support**: Add OCR for scanned PDFs (using Tesseract)

2. **Machine Learning**: Train custom models for better extraction

3. **Multiple Format Support**: Handle DOCX, HTML, plain text

4. **Better Pattern Matching**: More sophisticated regex patterns

5. **Context Understanding**: Use larger language models for better understanding

## Summary

Resume parsing is a multi-step process:

1. **PDF → Text**: Extract raw text from PDF
2. **Section Detection**: Find where information is located
3. **Pattern Matching**: Use regex to find structured data
4. **NLP Processing**: Use spaCy to identify entities
5. **Data Assembly**: Combine all extracted information
6. **JSON Output**: Structure data in a usable format

The key is combining multiple strategies (pattern matching + NLP) to handle the variety of resume formats.

