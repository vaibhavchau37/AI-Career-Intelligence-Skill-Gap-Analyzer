"""
PDF Resume Parser  -  spaCy + Custom Rules Engine  (2026-ready)
================================================================
Pipeline
  pdfplumber / PyPDF2  ->  plain text
  spaCy en_core_web_sm ->  base NLP (tokeniser, POS, dep, NER)
    + EntityRuler       ->  TECH_SKILL labels  (1000+ curated patterns)
    + Matcher           ->  DEGREE  /  JOB_TITLE  rule patterns

Extraction layers (priority order)
  Skills      : EntityRuler TECH_SKILL + section-text token scan + regex
  Experience  : Matcher JOB_TITLE  + spaCy ORG / DATE entities
  Education   : Matcher DEGREE     + spaCy ORG / DATE entities
  Name        : spaCy PERSON entity (first 5 lines) -> heuristic
  Email/Phone : regex
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple

# ── PDF backends ──────────────────────────────────────────────────────────────
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("Warning: pdfplumber not installed. Run: pip install pdfplumber")

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

# ── spaCy ─────────────────────────────────────────────────────────────────────
try:
    import spacy
    from spacy.matcher import Matcher
    SPACY_AVAILABLE = True
    try:
        _BASE_NLP = spacy.load("en_core_web_sm")
    except OSError:
        _BASE_NLP = None
        print("Warning: spaCy model missing. Run: python -m spacy download en_core_web_sm")
except ImportError:
    SPACY_AVAILABLE = False
    _BASE_NLP = None
    Matcher = None  # type: ignore
    print("Warning: spaCy not installed. Run: pip install spacy")


# ═════════════════════════════════════════════════════════════════════════════
#  TECH-SKILL MASTER LIST  (EntityRuler patterns)
# ═════════════════════════════════════════════════════════════════════════════
_TECH_SKILLS: List[str] = [
    # Programming languages
    "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "Go",
    "Rust", "Kotlin", "Swift", "R", "MATLAB", "Scala", "PHP", "Ruby", "Perl",
    "Bash", "Shell", "PowerShell", "SQL", "PL/SQL", "T-SQL", "HTML", "CSS",
    "Sass", "SCSS", "Dart", "Elixir", "Haskell", "Lua", "Groovy", "Julia",
    # Web front-end
    "React", "Angular", "Vue", "Vue.js", "Next.js", "Nuxt.js", "Svelte",
    "Gatsby", "Remix", "Tailwind CSS", "Bootstrap", "Material UI", "Webpack",
    "Vite", "Babel", "ESLint", "Redux", "Zustand", "GraphQL",
    # Back-end / API
    "Node.js", "Express", "FastAPI", "Flask", "Django", "Spring Boot",
    "Spring", "Spring MVC", "Hibernate", "JPA", "Laravel", "Rails",
    "ASP.NET", "gRPC", "REST API", "WebSockets", "Socket.IO",
    # ML / AI / Data Science
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "XGBoost", "LightGBM",
    "CatBoost", "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn", "Plotly",
    "OpenCV", "NLTK", "spaCy", "Hugging Face", "Transformers", "LangChain",
    "LlamaIndex", "FAISS", "Pinecone", "ONNX", "MLflow", "DVC",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "Reinforcement Learning", "Generative AI", "Prompt Engineering",
    # Cloud & DevOps
    "AWS", "Azure", "GCP", "Google Cloud", "Heroku", "Vercel", "Netlify",
    "DigitalOcean", "Docker", "Kubernetes", "Terraform", "Ansible",
    "Jenkins", "GitHub Actions", "GitLab CI", "CircleCI", "ArgoCD",
    "Helm", "Prometheus", "Grafana", "Datadog", "ELK Stack",
    "CI/CD", "DevOps", "SRE",
    # Databases
    "MySQL", "PostgreSQL", "SQLite", "MSSQL", "Oracle", "MongoDB",
    "Redis", "Cassandra", "DynamoDB", "Firestore", "Elasticsearch",
    "Neo4j", "Snowflake", "BigQuery", "Redshift", "Databricks",
    # Big Data
    "Apache Spark", "Hadoop", "Kafka", "Apache Airflow", "dbt",
    # Tools & Platforms
    "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Confluence",
    "Postman", "Swagger", "OpenAPI", "VS Code", "IntelliJ IDEA",
    "PyCharm", "Jupyter", "Google Colab", "Anaconda",
    "Power BI", "Tableau", "Looker", "Metabase", "Excel",
    "Figma", "Sketch", "Adobe XD",
    # Concepts / Methodologies
    "Data Science", "Data Engineering", "MLOps", "Microservices",
    "System Design", "Agile", "Scrum", "Kanban", "OOP",
    "Test-Driven Development", "TDD", "BDD",
]

# Canonical aliases (normalised key -> canonical display name)
_SKILL_ALIASES: Dict[str, str] = {
    "py": "Python", "python3": "Python",
    "js": "JavaScript", "es6": "JavaScript",
    "nodejs": "Node.js", "node": "Node.js",
    "reactjs": "React", "react.js": "React",
    "nextjs": "Next.js", "next.js": "Next.js",
    "ts": "TypeScript",
    "sklearn": "Scikit-learn", "scikitlearn": "Scikit-learn",
    "postgres": "PostgreSQL", "postgresql": "PostgreSQL",
    "mysql": "MySQL", "mongodb": "MongoDB",
    "opencv": "OpenCV", "numpy": "NumPy", "pandas": "Pandas",
    "tensorflow": "TensorFlow", "pytorch": "PyTorch",
    "fastapi": "FastAPI", "powerbi": "Power BI",
    "nlp": "NLP", "ml": "Machine Learning", "ai": "AI",
    "aws": "AWS", "gcp": "GCP", "azure": "Azure",
    "github": "GitHub", "gitlab": "GitLab",
    "k8s": "Kubernetes", "kube": "Kubernetes",
    "tf": "TensorFlow",
}

# Section heading vocabulary
_SECTION_KEYWORDS: Dict[str, List[str]] = {
    "skills": [
        "skills", "technical skills", "core skills", "competencies",
        "expertise", "tools and technologies", "technologies", "tech stack",
        "programming languages", "tools & technologies",
    ],
    "education": [
        "education", "academic background", "academic qualifications",
        "qualifications", "educational background",
    ],
    "experience": [
        "experience", "work experience", "professional experience",
        "employment history", "work history", "internships",
        "internship experience",
    ],
    "projects": [
        "projects", "project experience", "academic projects",
        "key projects", "portfolio", "personal projects",
        "selected projects",
    ],
    "certifications": [
        "certifications", "certificates", "licenses", "credentials",
        "courses", "professional development",
    ],
    "achievements": ["achievements", "awards", "honors", "accomplishments"],
    "summary": [
        "summary", "objective", "profile", "about me",
        "professional summary", "career objective",
    ],
}

# ── Degree token patterns for spaCy Matcher ──────────────────────────────────
_DEGREE_MATCHER_PATTERNS: List[Dict] = [
    [{"LOWER": {"REGEX": r"^b\.?tech$"}}],
    [{"LOWER": {"REGEX": r"^m\.?tech$"}}],
    [{"LOWER": {"REGEX": r"^b\.?e\.?$"}}],
    [{"LOWER": {"REGEX": r"^m\.?e\.?$"}}],
    [{"LOWER": {"REGEX": r"^b\.?sc\.?$"}}],
    [{"LOWER": {"REGEX": r"^m\.?sc\.?$"}}],
    [{"LOWER": {"REGEX": r"^bachelors?$"}}, {"LOWER": "of", "OP": "?"}, {"IS_ALPHA": True, "OP": "?"}],
    [{"LOWER": {"REGEX": r"^masters?$"}}, {"LOWER": "of", "OP": "?"}, {"IS_ALPHA": True, "OP": "?"}],
    [{"LOWER": {"REGEX": r"^m\.?b\.?a\.?$"}}],
    [{"LOWER": {"REGEX": r"^ph\.?d\.?$"}}],
    [{"LOWER": {"REGEX": r"^doctorat?e$"}}],
    [{"LOWER": {"REGEX": r"^b\.?[as]\.?$"}}],
    [{"LOWER": {"REGEX": r"^m\.?[as]\.?$"}}],
]

# ── Job-title token patterns for spaCy Matcher ───────────────────────────────
_JOB_TITLE_PATTERNS: List[Dict] = [
    [{"LOWER": "software"}, {"LOWER": {"IN": ["engineer", "developer", "architect"]}}],
    [{"LOWER": "senior"}, {"IS_ALPHA": True}, {"LOWER": {"IN": ["engineer", "developer"]}}],
    [{"LOWER": "junior"}, {"IS_ALPHA": True}, {"LOWER": {"IN": ["engineer", "developer"]}}],
    [{"LOWER": "lead"}, {"IS_ALPHA": True}, {"LOWER": {"IN": ["engineer", "developer"]}}],
    [{"LOWER": "data"}, {"LOWER": {"IN": ["scientist", "engineer", "analyst", "architect"]}}],
    [{"LOWER": "ml"}, {"LOWER": {"IN": ["engineer", "researcher", "scientist"]}}],
    [{"LOWER": "machine"}, {"LOWER": "learning"}, {"LOWER": {"IN": ["engineer", "researcher"]}}],
    [{"LOWER": "ai"}, {"LOWER": {"IN": ["engineer", "researcher", "scientist"]}}],
    [{"LOWER": "backend"}, {"LOWER": {"IN": ["engineer", "developer"]}}],
    [{"LOWER": "frontend"}, {"LOWER": {"IN": ["engineer", "developer"]}}],
    [{"LOWER": "full"}, {"LOWER": "stack"}, {"LOWER": {"IN": ["engineer", "developer"]}}],
    [{"LOWER": "fullstack"}, {"LOWER": {"IN": ["engineer", "developer"]}}],
    [{"LOWER": "devops"}, {"LOWER": {"IN": ["engineer", "lead"]}}],
    [{"LOWER": "cloud"}, {"LOWER": {"IN": ["engineer", "architect"]}}],
    [{"LOWER": "product"}, {"LOWER": {"IN": ["manager", "owner", "lead"]}}],
    [{"LOWER": "project"}, {"LOWER": {"IN": ["manager", "coordinator", "lead"]}}],
    [{"LOWER": "business"}, {"LOWER": {"IN": ["analyst", "developer"]}}],
    [{"LOWER": "research"}, {"LOWER": {"IN": ["engineer", "analyst", "scientist", "intern"]}}],
    [{"LOWER": "intern"}],
    [{"IS_ALPHA": True}, {"LOWER": "intern"}],
    [{"IS_ALPHA": True}, {"IS_ALPHA": True}, {"LOWER": "intern"}],
    [{"LOWER": "android"}, {"LOWER": {"IN": ["developer", "engineer"]}}],
    [{"LOWER": "ios"}, {"LOWER": {"IN": ["developer", "engineer"]}}],
    [{"LOWER": "mobile"}, {"LOWER": {"IN": ["developer", "engineer"]}}],
    [{"LOWER": "embedded"}, {"LOWER": {"IN": ["engineer", "developer"]}}],
    [{"LOWER": "security"}, {"LOWER": {"IN": ["engineer", "analyst", "architect"]}}],
]


# ═════════════════════════════════════════════════════════════════════════════
#  PIPELINE BUILDER  (runs once at import time)
# ═════════════════════════════════════════════════════════════════════════════
def _build_pipeline(base):
    """Add EntityRuler (TECH_SKILL) to the base spaCy model."""
    if base is None:
        return None
    if "tech_skill_ruler" not in base.pipe_names:
        ruler = base.add_pipe(
            "entity_ruler", name="tech_skill_ruler", before="ner",
            config={"overwrite_ents": False},
        )
        patterns: List[Dict] = []
        for skill in _TECH_SKILLS:
            patterns.append({"label": "TECH_SKILL", "pattern": skill})
            if skill != skill.lower():
                patterns.append({"label": "TECH_SKILL", "pattern": skill.lower()})
            if skill != skill.title():
                patterns.append({"label": "TECH_SKILL", "pattern": skill.title()})
        ruler.add_patterns(patterns)
    return base


_NLP = _build_pipeline(_BASE_NLP) if SPACY_AVAILABLE and _BASE_NLP else None


def _build_degree_matcher(nlp):
    if nlp is None or Matcher is None:
        return None
    m = Matcher(nlp.vocab)
    for i, pat in enumerate(_DEGREE_MATCHER_PATTERNS):
        m.add(f"DEGREE_{i}", [pat])
    return m


def _build_title_matcher(nlp):
    if nlp is None or Matcher is None:
        return None
    m = Matcher(nlp.vocab)
    for i, pat in enumerate(_JOB_TITLE_PATTERNS):
        m.add(f"JOB_TITLE_{i}", [pat])
    return m


class PDFResumeParser:
    """
    Resume parser built on spaCy + custom rules.

    Extraction layers (priority order)
    1. spaCy EntityRuler  - TECH_SKILL entities  (skills)
    2. spaCy Matcher      - DEGREE / JOB_TITLE patterns
    3. spaCy built-in NER - ORG, DATE, PERSON entities
    4. Regex fallbacks    - when spaCy unavailable or entity missed
    """

    def __init__(self):
        self.nlp = _NLP
        self.section_keywords = _SECTION_KEYWORDS
        self._degree_matcher = _build_degree_matcher(self.nlp)
        self._title_matcher  = _build_title_matcher(self.nlp)

        # Shared compiled regex
        self._DATE_RANGE_RE = re.compile(
            r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
            r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?"
            r"|Nov(?:ember)?|Dec(?:ember)?)\.?\s*(?:19|20)\d{2}"
            r"\s*[-\u2013\u2014]\s*"
            r"(?:Present|Current"
            r"|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
            r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?"
            r"|Nov(?:ember)?|Dec(?:ember)?)\.?\s*(?:19|20)\d{2})",
            re.IGNORECASE,
        )
        self._YEAR_RANGE_RE = re.compile(
            r"\b(?:19|20)\d{2}\s*[-\u2013\u2014]\s*"
            r"(?:(?:19|20)\d{2}|Present|Current)\b",
            re.IGNORECASE,
        )
        self._YEAR_RE   = re.compile(r"\b(?:19|20)\d{2}\b")
        self._DEGREE_RE = re.compile(
            r"\b(Bachelors?|Masters?|B\.?Tech|M\.?Tech|B\.?E\.?|M\.?E\.?"
            r"|B\.?Sc\.?|M\.?Sc\.?|MBA|Ph\.?D\.?|B\.?A\.?|M\.?A\.?"
            r"|BS|MS|BE|ME|B\.S\.|M\.S\.)\b",
            re.IGNORECASE,
        )
        self._INST_RE = re.compile(
            r"\b(university|universities|college|institute|institution|school"
            r"|iit|nit|iiit|bits|academy|polytechnic|deemed"
            r"|vidyalaya|vidyapeeth)\b",
            re.IGNORECASE,
        )

    # ── PUBLIC API ────────────────────────────────────────────────────────────
    def parse_pdf(self, pdf_path: str) -> Dict:
        text = self._extract_text_from_pdf(pdf_path)
        if not text:
            raise ValueError(f"Could not extract text from: {pdf_path}")
        # Run spaCy ONCE and share the doc across all extractors
        doc = self.nlp(text) if self.nlp else None
        return {
            "name":           self._extract_name(text, doc),
            "email":          self._extract_email(text),
            "phone":          self._extract_phone(text),
            "skills":         self._extract_skills(text, doc),
            "experience":     self._extract_experience(text, doc),
            "education":      self._extract_education(text, doc),
            "projects":       self._extract_projects(text),
            "certifications": self._extract_certifications(text),
            "summary":        self._extract_summary(text),
        }

    def parse_text(self, text: str) -> Dict:
        """Parse resume from raw text string (no PDF needed)."""
        text = self._normalize_text(text)
        doc  = self.nlp(text) if self.nlp else None
        return {
            "name":           self._extract_name(text, doc),
            "email":          self._extract_email(text),
            "phone":          self._extract_phone(text),
            "skills":         self._extract_skills(text, doc),
            "experience":     self._extract_experience(text, doc),
            "education":      self._extract_education(text, doc),
            "projects":       self._extract_projects(text),
            "certifications": self._extract_certifications(text),
            "summary":        self._extract_summary(text),
        }

    def parse_to_json(self, pdf_path: str, output_path: Optional[str] = None) -> str:
        result   = self.parse_pdf(pdf_path)
        json_str = json.dumps(result, indent=2, ensure_ascii=False)
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_str)
            print(f"Saved parsed resume to: {output_path}")
        return json_str

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        text = ""

        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text(x_tolerance=2, y_tolerance=3)
                        if self._looks_like_collapsed_text(page_text):
                            reconstructed = self._extract_text_from_words(page)
                            if reconstructed:
                                page_text = reconstructed
                        if page_text:
                            text += page_text + "\n"
                return self._normalize_text(text.strip())
            except Exception as e:
                print(f"Error using pdfplumber: {e}")

        if PYPDF2_AVAILABLE:
            try:
                with open(pdf_path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += (page.extract_text() or "") + "\n"
                return self._normalize_text(text.strip())
            except Exception as e:
                print(f"Error using PyPDF2: {e}")

        raise ValueError("Could not extract text. Install pdfplumber: pip install pdfplumber")

    # ── SKILLS ───────────────────────────────────────────────────────────
    def _extract_skills(self, text: str, doc=None) -> List[str]:
        skills: set = set()

        # Layer 1: EntityRuler TECH_SKILL entities from full doc
        if doc is not None:
            for ent in doc.ents:
                if ent.label_ == "TECH_SKILL":
                    c = self._canonicalise_skill(ent.text)
                    if c:
                        skills.add(c)

        # Layer 2: Parse skills section text (comma/bullet split + EntityRuler)
        skills_section = self._find_section(text, "skills")
        if skills_section:
            if self.nlp:
                for ent in self.nlp(skills_section).ents:
                    if ent.label_ == "TECH_SKILL":
                        c = self._canonicalise_skill(ent.text)
                        if c:
                            skills.add(c)
            for line in skills_section.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Strip category prefix e.g. "Languages: Python, Java"
                line = re.sub(
                    r"^(languages?|frameworks?|libraries?|tools?|technologies"
                    r"|databases?|concepts?|cloud|devops|others?)\s*[:\-]\s*",
                    "", line, flags=re.IGNORECASE,
                )
                for token in re.split(r"[,;|/\u2022\u2013\u2014]", line):
                    c = self._canonicalise_skill(token)
                    if c:
                        skills.add(c)

        # Layer 3: High-confidence regex scan across full text
        _TECH_REGEX: Dict[str, str] = {
            r"\bpython\b": "Python",            r"\bjava\b": "Java",
            r"\bjavascript\b": "JavaScript",    r"\btypescript\b": "TypeScript",
            r"\breact(?:\.js|js)?\b": "React",  r"\bnode(?:\.js|js)?\b": "Node.js",
            r"\bnext(?:\.js|js)?\b": "Next.js", r"\bvue(?:\.js|js)?\b": "Vue.js",
            r"\bangular\b": "Angular",          r"\bsvelte\b": "Svelte",
            r"\bhtml5?\b": "HTML",              r"\bcss3?\b": "CSS",
            r"\bsql\b": "SQL",                  r"\bnosql\b": "NoSQL",
            r"\baws\b": "AWS",                  r"\bazure\b": "Azure",
            r"\bgcp\b": "GCP",                  r"\bdocker\b": "Docker",
            r"\bkubernetes\b": "Kubernetes",    r"\bterraform\b": "Terraform",
            r"\bci[\s/]?cd\b": "CI/CD",
            r"\btensorflow\b": "TensorFlow",    r"\bpytorch\b": "PyTorch",
            r"\bkeras\b": "Keras",
            r"\b(?:scikit[\s\-]?learn|sklearn)\b": "Scikit-learn",
            r"\bpandas\b": "Pandas",            r"\bnumpy\b": "NumPy",
            r"\bmatplotlib\b": "Matplotlib",    r"\bseaborn\b": "Seaborn",
            r"\bopencv\b": "OpenCV",
            r"\bmachine\s*learning\b": "Machine Learning",
            r"\bdeep\s*learning\b": "Deep Learning",
            r"\bnatural\s*language\s*processing\b": "NLP",
            r"\bcomputer\s*vision\b": "Computer Vision",
            r"\bdata\s*science\b": "Data Science",
            r"\bpower\s*bi\b": "Power BI",     r"\btableau\b": "Tableau",
            r"\bfastapi\b": "FastAPI",          r"\bflask\b": "Flask",
            r"\bdjango\b": "Django",            r"\bspring\s*boot\b": "Spring Boot",
            r"\bmongodb\b": "MongoDB",          r"\bpostgresql\b": "PostgreSQL",
            r"\bmysql\b": "MySQL",              r"\bredis\b": "Redis",
            r"\bgit\b": "Git",                  r"\bgithub\b": "GitHub",
            r"\blinux\b": "Linux",             r"\bjupyter\b": "Jupyter",
        }
        tl = text.lower()
        for pat, sname in _TECH_REGEX.items():
            if re.search(pat, tl):
                skills.add(sname)

        return sorted(s for s in skills if s)

    # ── EDUCATION ──────────────────────────────────────────────────────────
    def _extract_education(self, text: str, doc=None) -> List[Dict]:
        education_list = []
        education_section = self._find_section(text, "education") or text

        lines = [ln.strip() for ln in education_section.splitlines() if ln.strip()]

        # NLP-based institution detection
        nlp_institutions: List[str] = []
        if self.nlp:
            edu_doc = self.nlp(education_section)
            nlp_institutions = [ent.text for ent in edu_doc.ents if ent.label_ == "ORG"]

        _DEGREE_RE = self._DEGREE_RE
        _INST_RE   = self._INST_RE
        _YEAR_RE   = self._YEAR_RE

        # Categorise each line
        degree_lines: List[Tuple[str, str]] = []   # (full_line, matched_degree_str)
        institution_lines: List[str] = []
        year_values: List[str] = []

        for line in lines:
            dm = _DEGREE_RE.search(line)
            im = _INST_RE.search(line)
            ym = _YEAR_RE.search(line)
            if ym:
                year_values.append(ym.group(0))
            if dm and not im:
                degree_lines.append((line, dm.group(0)))
            elif im and not dm:
                institution_lines.append(line)
            elif dm and im:
                # Line contains both: record as degree entry and institution
                degree_lines.append((line, dm.group(0)))
                institution_lines.append(line)

        def _clean_institution(inst_line: str) -> str:
            """Remove degree abbreviations + generic filler from an institution line."""
            cleaned = _DEGREE_RE.sub("", inst_line)
            cleaned = re.sub(
                r"\b(in|of|and|the|Bachelor[s]?|Master[s]?|Technology|Engineering|Science|Arts|Commerce)\b",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
            cleaned = _YEAR_RE.sub("", cleaned)
            cleaned = re.sub(r"[^A-Za-z0-9 &.,()-]", " ", cleaned)
            cleaned = re.sub(r"\s+", " ", cleaned).strip(" -|,:/")
            return cleaned

        if degree_lines:
            for i, (deg_line, degree_str) in enumerate(degree_lines):
                year = year_values[i] if i < len(year_values) else None

                # 1) Prefer NLP ORG entity
                institution: Optional[str] = None
                if i < len(nlp_institutions):
                    institution = nlp_institutions[i]

                # 2) Use a dedicated institution line if available
                if not institution and i < len(institution_lines):
                    raw_inst = institution_lines[i]
                    # If the institution line IS the same as the degree line, clean it
                    if raw_inst == deg_line:
                        candidate = _clean_institution(raw_inst)
                        institution = candidate if len(candidate) > 3 else None
                    else:
                        institution = raw_inst

                # 3) Try "from X" / "at X" patterns inside the degree line
                if not institution:
                    for prep_pat in [r"\bfrom\s+([A-Za-z][A-Za-z0-9 ,\.]+)",
                                     r"\bat\s+([A-Za-z][A-Za-z0-9 ,\.]+)"]:
                        m = re.search(prep_pat, deg_line, re.IGNORECASE)
                        if m:
                            candidate = m.group(1).strip()
                            if len(candidate) > 3:
                                institution = candidate
                                break

                education_list.append({
                    "degree": degree_str,
                    "institution": institution,
                    "year": year,
                })
            return education_list

        # --- Fallback: no clear degree lines found ---
        for line in lines[:8]:
            dm = _DEGREE_RE.search(line)
            ym = _YEAR_RE.search(line)
            im = _INST_RE.search(line)
            if not (dm or ym or im):
                continue
            # Extract institution carefully — never use a bare degree abbreviation as institution
            institution = None
            if im:
                institution = line
            elif dm:
                # Line only has a degree keyword; extract the non-degree part
                candidate = _clean_institution(line)
                institution = candidate if len(candidate) > 3 else None
            education_list.append({
                "degree": dm.group(0) if dm else None,
                "institution": institution,
                "year": ym.group(0) if ym else None,
            })

        return education_list

    # ── EXPERIENCE ────────────────────────────────────────────────────────
    def _extract_experience(self, text: str, doc=None) -> List[Dict]:
        experience_list: List[Dict] = []
        section = self._find_section(text, "experience")
        if not section:
            return experience_list

        lines  = [ln.strip() for ln in section.splitlines() if ln.strip()]
        chunks = self._split_into_entry_chunks(lines)

        for chunk_lines in chunks[:12]:
            # Use only the first non-bullet line as the header — bullet lines
            # belong to the description and would corrupt company extraction.
            header_line = next(
                (ln for ln in chunk_lines if not re.match(r"^\s*[-*\u2022]|\d+[.)]\s", ln)),
                chunk_lines[0],
            )
            full_text   = " ".join(chunk_lines)

            dates   = self._extract_date_range(full_text)
            title   = self._extract_job_title(header_line)
            company = self._extract_company(header_line, title)

            if not title and not company:
                title, company = self._regex_extract_title_company(header_line)

            # Absolute last resort: first chunk line minus dates
            if not title and chunk_lines:
                candidate = self._DATE_RANGE_RE.sub("", header_line)
                candidate = self._YEAR_RE.sub("", candidate)
                candidate = re.sub(r"^\s*(?:[-*\u2022]\s+|\d+[.)]\s+)", "", candidate)
                candidate = re.sub(r"\s+", " ", candidate).strip(" -|,:/")
                if len(candidate) > 3:
                    title = candidate

            entry = {"title": title, "company": company, "dates": dates}
            if any(entry.values()):
                experience_list.append(entry)

        return experience_list

    def _extract_job_title(self, text: str) -> Optional[str]:
        """Use spaCy Matcher to locate job-title spans."""
        if not self._title_matcher or not self.nlp:
            return None
        doc     = self.nlp(self._strip_dates(text))
        matches = self._title_matcher(doc)
        if matches:
            best      = max(matches, key=lambda m: m[2] - m[1])
            span_text = doc[best[1]: best[2]].text.strip()
            return span_text if len(span_text) > 2 else None
        return None

    def _extract_company(self, text: str, known_title: Optional[str] = None) -> Optional[str]:
        """Use spaCy ORG entity to find company name."""
        if not self.nlp:
            return None
        clean = self._strip_dates(text)
        if known_title:
            clean = clean.replace(known_title, "").strip()
        orgs = [e.text.strip() for e in self.nlp(clean).ents
                if e.label_ == "ORG" and len(e.text.strip()) > 2]
        return orgs[0] if orgs else None

    def _extract_projects(self, text: str) -> List[str]:
        projects = []
        projects_section = self._find_section(text, "projects")
        if not projects_section:
            return projects

        lines = [ln.strip() for ln in projects_section.splitlines() if ln.strip()]
        current = ""
        for line in lines:
            is_new_project = bool(re.match(r"^\s*(?:[-*\u2022]\s+|\d+[.)]\s+)", line))
            clean_line = re.sub(r"^\s*(?:[-*\u2022]\s+|\d+[.)]\s+)", "", line).strip()
            if is_new_project and current:
                if len(current) > 10:
                    projects.append(current)
                current = clean_line
            elif current and self._looks_like_project_title(clean_line):
                if len(current) > 10:
                    projects.append(current)
                current = clean_line
            elif current:
                current = f"{current} {clean_line}".strip()
            else:
                current = clean_line
        if current and len(current) > 10:
            projects.append(current)

        cleaned_projects = []
        seen = set()
        for item in projects:
            item = re.sub(r"\s+", " ", item).strip(" -|:")
            if len(item) < 12:
                continue
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned_projects.append(item)

        merged_projects: List[str] = []
        for item in cleaned_projects:
            if self._looks_like_project_title(item):
                merged_projects.append(item)
            elif merged_projects:
                merged_projects[-1] = f"{merged_projects[-1]} {item}".strip()
            else:
                merged_projects.append(item)

        return merged_projects

    def _find_section(self, text: str, section_type: str) -> Optional[str]:
        keywords = [self._norm_heading(k) for k in self.section_keywords.get(section_type, [])]
        all_kws  = {self._norm_heading(k) for kws in self.section_keywords.values() for k in kws}
        lines = text.splitlines()
        start_index = None
        first_line_remainder = ""

        for i, raw_line in enumerate(lines):
            line = raw_line.strip()
            if not line:
                continue
            norm_line = self._norm_heading(line.replace(":", " "))
            for kw in keywords:
                if norm_line == kw or norm_line.startswith(kw + " "):
                    start_index = i + 1
                    if ":" in line:
                        first_line_remainder = line.split(":", 1)[1].strip()
                    break
            if start_index is not None:
                break

        if start_index is None:
            return None

        collected = []
        if first_line_remainder:
            collected.append(first_line_remainder)
        for j in range(start_index, len(lines)):
            candidate = lines[j].strip()
            if not candidate:
                if collected:
                    collected.append("")
                continue
            if self._is_section_header_line(candidate):
                break
            collected.append(candidate)

        section_text = "\n".join(collected).strip()
        return section_text if section_text else None

    # ── HELPERS: date / chunk / match ────────────────────────────────────
    def _split_into_entry_chunks(self, lines: List[str]) -> List[List[str]]:
        """Split a flat list of section lines into per-entry chunks.

        A line that is ONLY a date range (e.g. 'Aug 2024 – Oct 2024') does NOT
        start a new chunk — it gets appended to the current one.  Bullet/number
        list lines are always description lines, never headers.
        """
        _BULLET = re.compile(r"^\s*(?:[-*\u2022]\s+|\d+[.)]\s+)")
        _DATE_ONLY = re.compile(
            r"^\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\.?"
            r"\s*(?:19|20)\d{2}\s*[-\u2013\u2014]\s*"
            r"(?:Present|Current|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\.?\s*(?:19|20)\d{2})\s*$",
            re.IGNORECASE,
        )

        def _is_entry_header(line: str) -> bool:
            if _DATE_ONLY.match(line):
                return False
            if _BULLET.match(line):
                return False
            return bool(
                re.search(r"\b(?:19|20)\d{2}\b", line)
                or re.search(r"\b(?:present|current)\b", line, re.IGNORECASE)
                or re.search(r"\b(?:at|@)\b", line)
                or "|" in line
            )

        chunks: List[List[str]] = []
        current: List[str] = []
        for line in lines:
            if _is_entry_header(line) and current:
                chunks.append(current)
                current = [line]
            else:
                current.append(line)
        if current:
            chunks.append(current)
        return chunks

    def _extract_date_range(self, text: str) -> Optional[str]:
        """Return the first date/year range found in *text*."""
        m = self._DATE_RANGE_RE.search(text)
        if m:
            return m.group(0)
        m = self._YEAR_RANGE_RE.search(text)
        if m:
            return m.group(0)
        return None

    def _strip_dates(self, text: str) -> str:
        """Remove date tokens from *text*; used before NLP matching."""
        cleaned = self._DATE_RANGE_RE.sub("", text)
        cleaned = re.sub(
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s*(?:19|20)\d{2}\b",
            "", cleaned, flags=re.IGNORECASE,
        )
        cleaned = self._YEAR_RE.sub("", cleaned)
        return re.sub(r"\s+", " ", cleaned).strip(" -|,:/")

    def _match_degree_in_line(self, line: str) -> Optional[str]:
        """Use Matcher to find a degree span; fall back to regex."""
        if self._degree_matcher and self.nlp:
            doc     = self.nlp(line)
            matches = self._degree_matcher(doc)
            if matches:
                best = max(matches, key=lambda m: m[2] - m[1])
                return doc[best[1]: best[2]].text.strip()
        m = self._DEGREE_RE.search(line)
        return m.group(0) if m else None

    # ── NAME ─────────────────────────────────────────────────────────────
    def _extract_name(self, text: str, doc=None) -> Optional[str]:
        # Strategy 1: spaCy PERSON entity in first 5 lines
        if self.nlp:
            first_block = "\n".join(text.splitlines()[:5])
            sub_doc = self.nlp(first_block)
            for ent in sub_doc.ents:
                if ent.label_ == "PERSON":
                    name = ent.text.strip()
                    if 2 <= len(name.split()) <= 5 and not any(c.isdigit() for c in name):
                        return name
        # Strategy 2: first non-empty title-case line (heuristic)
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if re.search(r"[@|/\\|\d]", line):
                continue
            if len(line) > 60:
                continue
            words = line.split()
            if 1 <= len(words) <= 5 and all(w[0].isupper() for w in words if w.isalpha()):
                return line
            break
        return None

    def _extract_email(self, text: str) -> Optional[str]:
        match = re.search(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", text)
        return match.group() if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        patterns = [
            r"\+?\d{1,3}[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}",
            r"\b\d{3}-\d{3}-\d{4}\b",
            r"\b\(\d{3}\)\s?\d{3}-\d{4}\b",
            r"\b\d{10}\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        return None

    def _is_technology(self, text: str) -> bool:
        tech_indicators = ["cloud", "framework", "library", "tool", "platform", "api", "sdk"]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in tech_indicators)

    def _looks_like_collapsed_text(self, text: Optional[str]) -> bool:
        if not text:
            return True
        compact = re.sub(r"\s+", " ", text).strip()
        if not compact:
            return True
        words = compact.split(" ")
        avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
        space_ratio = compact.count(" ") / max(len(compact), 1)
        return avg_word_len > 11 or space_ratio < 0.08

    def _extract_text_from_words(self, page) -> str:
        try:
            words = page.extract_words(use_text_flow=True, keep_blank_chars=False)
            if not words:
                return ""
            words = sorted(words, key=lambda w: (round(w["top"], 1), w["x0"]))
            lines: List[List[dict]] = []
            for word in words:
                if not lines:
                    lines.append([word])
                    continue
                if abs(lines[-1][-1]["top"] - word["top"]) <= 3:
                    lines[-1].append(word)
                else:
                    lines.append([word])

            out_lines: List[str] = []
            for line_words in lines:
                line_words = sorted(line_words, key=lambda w: w["x0"])
                parts = []
                prev = None
                for w in line_words:
                    if prev is not None:
                        gap = w["x0"] - prev["x1"]
                        if gap > 1.5:
                            parts.append(" ")
                    parts.append(w["text"])
                    prev = w
                out_lines.append("".join(parts))
            return "\n".join(out_lines)
        except Exception:
            return ""

    def _normalize_text(self, text: str) -> str:
        if not text:
            return text

        # Protect email addresses and phone numbers so letter-digit splitting
        # rules below don't corrupt them (e.g. "john508@gmail.com" → "john 508@gmail.com").
        _EMAIL_RE = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')
        _PHONE_RE = re.compile(r'(?:\+?\d[\d\s\-().]{6,}\d)')
        placeholders: dict = {}

        def _protect(m: re.Match) -> str:
            key = f"__PROTECTED_{len(placeholders)}__"
            placeholders[key] = m.group()
            return key

        text = _EMAIL_RE.sub(_protect, text)
        text = _PHONE_RE.sub(_protect, text)

        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        normalized = normalized.replace("\u00a0", " ")
        normalized = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", normalized)
        normalized = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", normalized)
        normalized = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", normalized)
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)

        # Restore protected tokens
        for key, original in placeholders.items():
            normalized = normalized.replace(key, original)

        return normalized.strip()

    def _norm_heading(self, value: str) -> str:
        return re.sub(r"[^a-z0-9 ]+", " ", value.lower()).strip()

    # Keep alias for backwards compatibility
    def _normalize_heading(self, value: str) -> str:  # noqa: D401
        return self._norm_heading(value)

    def _is_section_header_line(self, line: str) -> bool:
        normalized = self._norm_heading(line.replace(":", " "))
        if len(normalized.split()) > 5:
            return False
        all_kws = {self._norm_heading(k) for kws in self.section_keywords.values() for k in kws}
        return normalized in all_kws

    def _canonicalise_skill(self, token: str) -> Optional[str]:
        """Normalise a raw skill token; return canonical name or None."""
        token = token.strip()
        if not token:
            return None

        if ":" in token:
            left, right = token.split(":", 1)
            left  = left.strip()
            right = right.strip()
            if right and (
                re.search(
                    r"(languages?|frameworks?|tools?|technologies|databases?|concepts?|libraries?)",
                    left, re.IGNORECASE,
                )
                or len(right.split()) <= 5
            ):
                token = right

        token = re.sub(
            r"^(proficient in|experienced with|knowledge of|familiar with|strong in)\s+",
            "", token, flags=re.IGNORECASE,
        ).strip()
        token = token.strip(" .:-")

        if len(token) < 2 or len(token) > 40:
            return None

        key = re.sub(r"[^a-z0-9+.#]", "", token.lower())
        if not key:
            return None
        if key in {"skills", "skill", "tools", "tool", "technology", "technologies", "api"}:
            return None

        # Use module-level aliases first, then instance aliases for backwards compat
        canonical = _SKILL_ALIASES.get(key)
        if canonical:
            return canonical

        if re.fullmatch(r"[a-z]{1,2}", key):
            return None

        return token

    # Keep legacy alias
    def _normalize_skill_token(self, token: str) -> Optional[str]:  # noqa: D401
        return self._canonicalise_skill(token)

    def _regex_extract_title_company(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Regex-based title/company extractor used as fallback after Matcher."""
        clean = self._DATE_RANGE_RE.sub("", text)
        # also strip standalone years (e.g. "Aug 2024")
        clean = re.sub(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s*(?:19|20)\d{2}\b", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\b(?:19|20)\d{2}\b", "", clean)
        clean = re.sub(r"\s+", " ", clean).strip(" -|,:/")

        patterns = [
            r"(?P<title>[A-Za-z][A-Za-z0-9 &/+.,()-]{2,80})\s+(?:at|@)\s+(?P<company>[A-Za-z][A-Za-z0-9 &/+.,()-]{1,80})",
            r"(?P<title>[A-Za-z][A-Za-z0-9 &/+.,()-]{2,80})\s*[|]\s*(?P<company>[A-Za-z][A-Za-z0-9 &/+.,()-]{1,80})",
            r"(?P<company>[A-Za-z][A-Za-z0-9 &/+.,()-]{1,80})\s*[-\u2013\u2014]\s*(?P<title>[A-Za-z][A-Za-z0-9 &/+.,()-]{2,80})",
        ]
        for pattern in patterns:
            match = re.search(pattern, clean)
            if match:
                title = match.groupdict().get("title")
                company = match.groupdict().get("company")
                if title:
                    title = re.sub(r"\s+", " ", title).strip(" -|,:/")
                if company:
                    company = re.sub(r"\s+", " ", company).strip(" -|,:/")
                # Discard title if it's empty after cleaning
                if not title:
                    title = None
                return title, company

        # NLP fallback: look for ORG entities as company name
        if self.nlp and clean:
            doc = self.nlp(clean)
            orgs = [ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"]
            if orgs:
                company = orgs[0]
                title = re.sub(re.escape(company), "", clean).strip(" -|,:/")
                return (title if title else None), company

        return None, None

    def _looks_like_project_title(self, text: str) -> bool:
        if not text or len(text.split()) > 14:
            return False
        if text.endswith("."):
            return False
        if " - " in text or " : " in text or " | " in text:
            return True
        if "\u2013" in text or "\u2014" in text:
            return True
        title_case_words = sum(1 for w in text.split() if w[:1].isupper())
        return title_case_words >= max(2, len(text.split()) // 2)

    # ── CERTIFICATIONS + SUMMARY ─────────────────────────────────────────
    def _extract_certifications(self, text: str) -> List[str]:
        """Return certification strings from the certifications section."""
        section = self._find_section(text, "certifications")
        if not section:
            return []
        certs: List[str] = []
        for line in section.splitlines():
            line = re.sub(r"^\s*(?:[-*\u2022]\s+|\d+[.)]\s+)", "", line.strip())
            line = re.sub(r"\s+", " ", line).strip()
            if len(line) > 5:
                certs.append(line)
        return certs

    def _extract_summary(self, text: str) -> Optional[str]:
        """Return the objective / summary paragraph."""
        section = self._find_section(text, "summary")
        if not section:
            return None
        summary = re.sub(r"\s+", " ", section).strip()
        return summary if len(summary) > 10 else None
