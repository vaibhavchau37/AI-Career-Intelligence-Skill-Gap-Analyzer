# AI Career Intelligence & Skill Gap Analyzer

An intelligent career analysis platform that evaluates resumes against job requirements, identifies skill gaps, and generates personalized learning roadmaps.

## Features

### Core Capabilities
- **Resume Parsing** - Extracts skills, experience, education, and certifications from PDF resumes
- **Skill Gap Analysis** - Compares your skills against job role requirements using TF-IDF and cosine similarity
- **Job Readiness Scoring** - Calculates match scores (0-100) with detailed breakdown
- **Role Suitability Prediction** - Ranks best-fit job roles based on your profile
- **Personalized Roadmaps** - Generates learning plans with timelines and resources

### Advanced Features
- **AI-Powered Interview Practice** - Mock interviews with OpenAI/Gemini/SambaNova integration
- **Live Job Market Analysis** - Real-time job postings via Adzuna API
- **Progress Tracking** - Track your skill development over time
- **User Authentication** - Secure login/signup with JWT authentication

## Tech Stack

| Category | Technologies |
|----------|-------------|
| **Frontend** | Streamlit |
| **Backend** | FastAPI, Uvicorn |
| **NLP** | spaCy, Sentence Transformers |
| **ML** | scikit-learn (TF-IDF, Cosine Similarity) |
| **PDF Processing** | pdfplumber, PyPDF2 |
| **Database** | SQLite |
| **AI Integration** | OpenAI, Google Gemini, SambaNova |
| **Authentication** | JWT, bcrypt |

## Installation

### Prerequisites
- Python 3.10+
- pip

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/vaibhavchau37/AI-Career-Intelligence-Skill-Gap-Analyzer.git
   cd AI-Career-Intelligence-Skill-Gap-Analyzer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

## Configuration

### Environment Variables (.env)
```env
OPENAI_API_KEY=your_openai_key
GOOGLE_GEMINI_API_KEY=your_gemini_key
SAMBANOVA_API_KEY=your_sambanova_key
ADZUNA_APP_ID=your_adzuna_id
ADZUNA_API_KEY=your_adzuna_key
JWT_SECRET_KEY=your_secret_key
```

### Scoring Weights (config.yaml)
```yaml
scoring:
  required_skills: 40      # Required skills match
  preferred_skills: 20     # Preferred skills match
  experience: 20           # Years of experience
  education: 10            # Education alignment
  certifications: 10       # Certifications/projects
```

## Project Structure

```
├── app.py                 # Main Streamlit application
├── backend.py             # FastAPI backend server
├── config.yaml            # Configuration settings
├── requirements.txt       # Python dependencies
├── src/
│   ├── core/              # Core processing modules
│   │   ├── pdf_resume_parser.py
│   │   ├── skill_extractor.py
│   │   ├── skill_gap_analyzer_tfidf.py
│   │   └── job_readiness_scorer.py
│   ├── matcher/           # Job matching logic
│   │   ├── job_matcher.py
│   │   └── role_suitability_predictor.py
│   ├── roadmap/           # Learning roadmap generation
│   │   └── personalized_roadmap_generator.py
│   ├── api/               # External API integrations
│   │   ├── interview_ai.py
│   │   └── job_market_analyzer.py
│   ├── auth/              # Authentication system
│   └── utils/             # Helper utilities
├── data/
│   ├── job_roles/         # Job role definitions (YAML)
│   └── skills/            # Skill taxonomy and synonyms
├── docs/                  # Documentation
├── examples/              # Example scripts
└── tests/                 # Unit tests
```

## Usage

### Web Interface
```bash
streamlit run app.py
```
Access at `http://localhost:8501`

### Python API
```python
from src.analyzer.career_analyzer import CareerAnalyzer

analyzer = CareerAnalyzer()
result = analyzer.analyze("Your resume text here...")

print(f"Best role: {result.top_roles[0]}")
print(f"Score: {result.get_role_score(result.top_roles[0])}")
```

## Supported Job Roles

- Data Scientist
- ML Engineer
- Data Engineer
- Software Engineer
- Web Developer
- Python Developer
- Java Developer
- Salesforce Developer
- Business Analyst
- Product Manager
- Financial Analyst
- Business Development Manager

## How It Works

```
Resume (PDF/Text)
       ↓
[Resume Parser] → Extracts skills, experience, education
       ↓
[Skill Extractor] → Identifies technical & soft skills
       ↓
[Skill Gap Analyzer] → Compares against job requirements
       ↓
[Score Calculator] → Generates readiness score (0-100)
       ↓
[Roadmap Generator] → Creates personalized learning plan
       ↓
Final Report: Scores, Gaps, Learning Roadmap
```

## Documentation

Detailed documentation available in the `docs/` folder:
- [Quick Start Guide](docs/QUICKSTART.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Reference](docs/api_reference.md)
- [User Guide](docs/user_guide.md)
- [Authentication Guide](docs/AUTHENTICATION_GUIDE.md)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -m 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

This project is developed for educational purposes.

## Author

**Vaibhav Chaudhari**
- GitHub: [@vaibhavchau37](https://github.com/vaibhavchau37)
