# Streamlit Web App Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## App Structure

### Screen 1: Resume Upload 📄

**Purpose**: Upload and parse PDF resume

**Features**:
- PDF file upload
- Automatic resume parsing
- Display of extracted information:
  - Basic info (name, email, phone)
  - Skills
  - Experience
  - Projects
  - Education

**Usage**:
1. Click "Browse files" or drag and drop PDF
2. Wait for parsing to complete
3. Review extracted information

### Screen 2: Select Target Role 🎯

**Purpose**: Choose job role to analyze against

**Features**:
- Dropdown list of available roles:
  - ML Engineer
  - Data Scientist
  - Data Analyst
  - AI Engineer
  - Python Developer
- Display role requirements:
  - Required skills
  - Optional skills
  - Role description

**Usage**:
1. Select role from dropdown
2. Review requirements
3. Click "Analyze This Role"

### Screen 3: Skill Gap Analysis 📊

**Purpose**: Analyze skills and identify gaps

**Features**:
- TF-IDF + Cosine Similarity matching
- Display:
  - Matched skills (with similarity scores)
  - Missing required skills
  - Missing preferred skills
  - Explanations for missing skills

**Usage**:
1. Ensure resume is uploaded and role selected
2. View matched and missing skills
3. Review explanations for gaps

### Screen 4: Readiness Score ⭐

**Purpose**: Calculate job readiness score (0-100)

**Features**:
- Overall readiness score
- Component breakdown:
  - Skills (60% weight)
  - Experience (25% weight)
  - Projects (15% weight)
- Detailed explanations
- Calculation steps

**Usage**:
1. Enter years of experience
2. Review projects (auto-filled from resume)
3. Click "Calculate Readiness Score"
4. View score breakdown and explanations

### Screen 5: Role Suitability 🔍

**Purpose**: Predict best-fit roles and identify unsuitable ones

**Features**:
- Analyze all available roles
- Rank roles by suitability
- Best-fit roles with reasons
- Not recommended roles with explanations
- Overall recommendations

**Usage**:
1. Click "Analyze All Roles"
2. Review best-fit roles
3. Check not recommended roles and reasons
4. Read recommendations

### Screen 6: Learning Roadmap 🗺️

**Purpose**: Generate personalized 30-day learning plan

**Features**:
- 30-day (customizable) roadmap
- Skill-wise learning plans
- Day-by-day timeline
- Practical tasks (not long courses)
- Learning resources
- Download roadmap as JSON

**Usage**:
1. Adjust roadmap duration (slider)
2. Click "Generate Learning Roadmap"
3. Review skill-wise plans
4. Check day-by-day timeline
5. Download roadmap if needed

## Navigation

Use the sidebar to navigate between screens. The app maintains state across pages, so you can:
- Upload resume once
- Analyze multiple roles
- Generate different roadmaps

## Features

### Clean UI
- Simple, intuitive interface
- Color-coded results (green for matches, red for missing)
- Clear sections and headers
- Responsive layout

### Presentation Ready
- Professional appearance
- Clear visualizations
- Easy to demonstrate
- Exportable results

### Comprehensive Analysis
- PDF resume parsing
- Skill gap analysis with TF-IDF
- Readiness scoring
- Role suitability prediction
- Personalized roadmaps

## Troubleshooting

### PDF Not Parsing
- Ensure PDF contains text (not just images)
- Try a different PDF format
- Check file size (should be reasonable)

### No Skills Detected
- Resume may not have a clear Skills section
- Try reformatting resume with explicit "Skills" header
- Skills may be embedded in other sections

### Low Scores
- Normal for initial analysis
- Focus on missing required skills
- Use roadmap to improve

### App Not Starting
- Check Streamlit installation: `pip install streamlit`
- Ensure all dependencies installed
- Check Python version (3.8+)

## Tips for Presentations

1. **Prepare Sample Resume**: Have a sample PDF ready
2. **Choose Role**: Select a role relevant to audience
3. **Show Flow**: Walk through each screen sequentially
4. **Highlight Features**: Emphasize TF-IDF, scoring transparency
5. **Demonstrate Roadmap**: Show practical, actionable learning plan

## Customization

### Add More Roles
Edit `data/job_roles/skill_mapping.json` to add roles

### Adjust Scoring Weights
Modify `JobReadinessScorer` initialization in `app.py`

### Change Roadmap Duration
Adjust slider range in roadmap section

### Customize Styling
Modify CSS in `app.py` header section

## File Structure

```
app.py                          # Main Streamlit app
src/
  core/
    pdf_resume_parser.py        # PDF parsing
    skill_gap_analyzer_tfidf.py # Skill gap analysis
    job_readiness_scorer.py     # Readiness scoring
  matcher/
    role_suitability_predictor.py # Role suitability
  roadmap/
    personalized_roadmap_generator.py # Roadmap generation
data/
  job_roles/
    skill_mapping.json          # Job role definitions
```

## Next Steps

1. Run the app: `streamlit run app.py`
2. Upload a sample resume
3. Explore all features
4. Customize for your needs
5. Prepare for presentation!

