"""
PDF Resume Parser Module

Extracts structured information from resume PDFs:
- Skills
- Education
- Experience
- Projects
"""

import json
import re
from typing import Dict, List, Optional, Tuple

try:
    import pdfplumber

    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("Warning: pdfplumber not installed. Install with: pip install pdfplumber")

try:
    import PyPDF2

    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import spacy

    SPACY_AVAILABLE = True
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        nlp = None
        print("Warning: spaCy model not loaded. Run: python -m spacy download en_core_web_sm")
except ImportError:
    SPACY_AVAILABLE = False
    nlp = None
    print("Warning: spaCy not installed. Install with: pip install spacy")


class PDFResumeParser:
    """PDF Resume Parser with robust section-based extraction."""

    def __init__(self):
        self.nlp = nlp
        self.section_keywords = {
            "skills": [
                "skills",
                "technical skills",
                "core skills",
                "competencies",
                "expertise",
                "tools and technologies",
                "technologies",
            ],
            "education": [
                "education",
                "academic background",
                "academic qualifications",
                "qualifications",
            ],
            "experience": [
                "experience",
                "work experience",
                "professional experience",
                "employment history",
                "work history",
            ],
            "projects": [
                "projects",
                "project experience",
                "academic projects",
                "key projects",
                "portfolio",
            ],
            "certifications": ["certifications", "certificates", "licenses", "credentials"],
            "achievements": ["achievements", "awards", "honors"],
        }
        self.degree_patterns = [
            r"\b(BS|B\.S\.|Bachelor|BA|B\.A\.|B\.Sc\.|BSc|B\.?Tech|B\.?E)\b",
            r"\b(MS|M\.S\.|Master|MA|M\.A\.|M\.Sc\.|MSc|M\.Tech|MTech|M\.?E|MBA)\b",
            r"\b(PhD|Ph\.D\.|Doctorate|D\.Sc\.)\b",
        ]
        self.skill_aliases = {
            "py": "Python",
            "python3": "Python",
            "js": "JavaScript",
            "nodejs": "Node.js",
            "reactjs": "React",
            "nextjs": "Next.js",
            "ts": "TypeScript",
            "github": "GitHub",
            "gitlab": "GitLab",
            "postgres": "PostgreSQL",
            "postgresql": "PostgreSQL",
            "mysql": "MySQL",
            "mongodb": "MongoDB",
            "scikitlearn": "Scikit-learn",
            "sklearn": "Scikit-learn",
            "opencv": "OpenCV",
            "numpy": "NumPy",
            "tensorflow": "TensorFlow",
            "pytorch": "PyTorch",
            "fastapi": "FastAPI",
            "powerbi": "Power BI",
            "nlp": "NLP",
            "ml": "Machine Learning",
            "ai": "AI",
            "aws": "AWS",
            "gcp": "GCP",
            "azure": "Azure",
        }

    def parse_pdf(self, pdf_path: str) -> Dict:
        resume_text = self._extract_text_from_pdf(pdf_path)
        if not resume_text:
            raise ValueError(f"Could not extract text from PDF: {pdf_path}")

        return {
            "skills": self._extract_skills(resume_text),
            "education": self._extract_education(resume_text),
            "experience": self._extract_experience(resume_text),
            "projects": self._extract_projects(resume_text),
            "name": self._extract_name(resume_text),
            "email": self._extract_email(resume_text),
            "phone": self._extract_phone(resume_text),
        }

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

    def _extract_skills(self, text: str) -> List[str]:
        skills = set()
        skills_section = self._find_section(text, "skills")

        if skills_section:
            for line in skills_section.splitlines():
                clean_line = line.strip()
                if not clean_line:
                    continue
                clean_line = re.sub(
                    r"^(languages?|frameworks?|tools?|technologies|databases?|concepts?)\s*:\s*",
                    "",
                    clean_line,
                    flags=re.IGNORECASE,
                )
                skill_items = re.split(r"[,;|/\u2022]", clean_line)
                for item in skill_items:
                    normalized = self._normalize_skill_token(item)
                    if normalized:
                        skills.add(normalized)

        technical_patterns = {
            r"\bpython\b": "Python",
            r"\bjava\b": "Java",
            r"\bjavascript\b": "JavaScript",
            r"\btypescript\b": "TypeScript",
            r"\breact(?:\.js|js)?\b": "React",
            r"\bnode(?:\.js|js)?\b": "Node.js",
            r"\bnext(?:\.js|js)?\b": "Next.js",
            r"\bsql\b": "SQL",
            r"\bhtml\b": "HTML",
            r"\bcss\b": "CSS",
            r"\baws\b": "AWS",
            r"\bazure\b": "Azure",
            r"\bgcp\b": "GCP",
            r"\bdocker\b": "Docker",
            r"\bkubernetes\b": "Kubernetes",
            r"\btensorflow\b": "TensorFlow",
            r"\bpytorch\b": "PyTorch",
            r"\bkeras\b": "Keras",
            r"\b(?:scikit[\s\-]?learn|sklearn)\b": "Scikit-learn",
            r"\bgit\b": "Git",
            r"\bmachine\s*learning\b": "Machine Learning",
            r"\bdeep\s*learning\b": "Deep Learning",
            r"\bdata\s*science\b": "Data Science",
            r"\bnlp\b": "NLP",
            r"\bpower\s*bi\b": "Power BI",
            r"\btableau\b": "Tableau",
            r"\bfastapi\b": "FastAPI",
            r"\bflask\b": "Flask",
            r"\bdjango\b": "Django",
            r"\bpandas\b": "Pandas",
            r"\bnumpy\b": "NumPy",
        }

        text_lower = text.lower()
        for pattern, skill_name in technical_patterns.items():
            if re.search(pattern, text_lower):
                skills.add(skill_name)

        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PRODUCT"] and self._is_technology(ent.text):
                    normalized = self._normalize_skill_token(ent.text)
                    if normalized:
                        skills.add(normalized)

        return sorted(skills)

    def _extract_education(self, text: str) -> List[Dict]:
        education_list = []
        education_section = self._find_section(text, "education") or text

        degrees_found = []
        for pattern in self.degree_patterns:
            for match in re.finditer(pattern, education_section, re.IGNORECASE):
                degrees_found.append(match.group())

        institutions = []
        if self.nlp:
            doc = self.nlp(education_section)
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    institutions.append(ent.text)

        years = re.findall(r"\b(?:19|20)\d{2}\b", education_section)
        for i, degree in enumerate(degrees_found):
            education_list.append(
                {
                    "degree": degree,
                    "institution": institutions[i] if i < len(institutions) else None,
                    "year": years[i] if i < len(years) else None,
                }
            )

        if not education_list and education_section:
            lines = [ln.strip() for ln in education_section.splitlines() if ln.strip()]
            for line in lines[:8]:
                degree_match = re.search(
                    r"(Bachelor|Master|B\.?Tech|M\.?Tech|B\.?E|M\.?E|B\.?Sc|M\.?Sc|MBA|Ph\.?D)",
                    line,
                    re.IGNORECASE,
                )
                year_match = re.search(
                    r"\b(?:19|20)\d{2}(?:\s*[-\u2013\u2014]\s*(?:19|20)\d{2}|[-\u2013\u2014]\s*(?:Present|Current))?\b",
                    line,
                    re.IGNORECASE,
                )
                if degree_match or year_match or re.search(
                    r"(university|college|institute|school)", line, re.IGNORECASE
                ):
                    education_list.append(
                        {
                            "degree": degree_match.group(0) if degree_match else None,
                            "institution": line,
                            "year": year_match.group(0) if year_match else None,
                        }
                    )

        return education_list

    def _extract_experience(self, text: str) -> List[Dict]:
        experience_list = []
        experience_section = self._find_section(text, "experience")
        if not experience_section:
            return experience_list

        lines = [ln.strip() for ln in experience_section.splitlines() if ln.strip()]
        chunks: List[str] = []
        current: List[str] = []
        for line in lines:
            is_header_like = bool(
                re.search(r"\b(?:19|20)\d{2}\b", line)
                or re.search(r"\b(?:present|current)\b", line, re.IGNORECASE)
                or re.search(r"\b(?:at|@)\b", line)
                or "|" in line
            )
            if is_header_like and current:
                chunks.append(" ".join(current))
                current = [line]
            else:
                current.append(line)
        if current:
            chunks.append(" ".join(current))

        for chunk in chunks[:10]:
            title, company = self._extract_title_company(chunk)
            date_match = re.search(
                r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)?\.?\s*(?:19|20)\d{2}\s*[-\u2013\u2014]\s*(?:Present|Current|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)?\.?\s*(?:19|20)\d{2}))",
                chunk,
                re.IGNORECASE,
            )
            if not date_match:
                date_match = re.search(
                    r"\b(?:19|20)\d{2}\s*[-\u2013\u2014]\s*(?:19|20)\d{2}\b", chunk
                )

            entry = {
                "title": title,
                "company": company,
                "dates": date_match.group(1) if date_match else None,
            }
            if entry["title"] or entry["company"] or entry["dates"]:
                experience_list.append(entry)

        return experience_list

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
        keywords = [self._normalize_heading(k) for k in self.section_keywords.get(section_type, [])]
        lines = text.splitlines()
        start_index = None
        first_line_remainder = ""

        for i, raw_line in enumerate(lines):
            line = raw_line.strip()
            if not line:
                continue
            norm_line = self._normalize_heading(line.replace(":", " "))
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

    def _extract_name(self, text: str) -> Optional[str]:
        lines = text.split("\n")
        if lines:
            first_line = lines[0].strip()
            if len(first_line) < 60 and any(c.isupper() for c in first_line):
                return first_line
        return None

    def _extract_email(self, text: str) -> Optional[str]:
        match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
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
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        normalized = normalized.replace("\u00a0", " ")
        normalized = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", normalized)
        normalized = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", normalized)
        normalized = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", normalized)
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()

    def _normalize_heading(self, value: str) -> str:
        return re.sub(r"[^a-z0-9 ]+", " ", value.lower()).strip()

    def _is_section_header_line(self, line: str) -> bool:
        normalized = self._normalize_heading(line.replace(":", " "))
        if len(normalized.split()) > 5:
            return False
        for kw_list in self.section_keywords.values():
            for kw in kw_list:
                if normalized == self._normalize_heading(kw):
                    return True
        return False

    def _normalize_skill_token(self, token: str) -> Optional[str]:
        token = token.strip()
        if not token:
            return None

        if ":" in token:
            left, right = token.split(":", 1)
            left = left.strip()
            right = right.strip()
            if right and (
                re.search(
                    r"(languages?|frameworks?|tools?|technologies|databases?|concepts?|libraries?)",
                    left,
                    re.IGNORECASE,
                )
                or len(right.split()) <= 5
            ):
                token = right

        token = re.sub(
            r"^(proficient in|experienced with|knowledge of|familiar with|strong in)\s+",
            "",
            token,
            flags=re.IGNORECASE,
        ).strip()
        token = token.strip(" .:-")

        if len(token) < 2 or len(token) > 40:
            return None

        key = re.sub(r"[^a-z0-9+.#]", "", token.lower())
        if not key:
            return None
        if key in {"skills", "skill", "tools", "tool", "technology", "technologies", "api"}:
            return None

        canonical = self.skill_aliases.get(key)
        if canonical:
            return canonical

        if re.fullmatch(r"[a-z]{1,2}", key):
            return None

        return token

    def _extract_title_company(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        patterns = [
            r"(?P<title>[A-Za-z][A-Za-z0-9 &/+.,()-]{2,80})\s+(?:at|@)\s+(?P<company>[A-Za-z][A-Za-z0-9 &/+.,()-]{1,80})",
            r"(?P<title>[A-Za-z][A-Za-z0-9 &/+.,()-]{2,80})\s*[|]\s*(?P<company>[A-Za-z][A-Za-z0-9 &/+.,()-]{1,80})",
            r"(?P<company>[A-Za-z][A-Za-z0-9 &/+.,()-]{1,80})\s*[-\u2013\u2014]\s*(?P<title>[A-Za-z][A-Za-z0-9 &/+.,()-]{2,80})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                title = match.groupdict().get("title")
                company = match.groupdict().get("company")
                if title:
                    title = re.sub(r"\s+", " ", title).strip(" -|")
                    title = re.sub(
                        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)?\.?\s*(?:19|20)\d{2}\b.*$",
                        "",
                        title,
                        flags=re.IGNORECASE,
                    ).strip(" -|")
                if company:
                    company = re.sub(r"\s+", " ", company).strip(" -|")
                return title, company
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

    def parse_to_json(self, pdf_path: str, output_path: Optional[str] = None) -> str:
        result = self.parse_pdf(pdf_path)
        json_str = json.dumps(result, indent=2, ensure_ascii=False)
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_str)
            print(f"Saved parsed resume to: {output_path}")
        return json_str
