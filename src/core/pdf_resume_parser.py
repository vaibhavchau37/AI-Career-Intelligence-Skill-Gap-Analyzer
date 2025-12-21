"""
PDF Resume Parser Module

This module parses resume PDFs and extracts structured information including:
- Skills
- Education
- Experience
- Projects

Uses spaCy for NLP-based entity extraction and pdfplumber for PDF text extraction.

Author: AI Career Analyzer
"""

import re
import json
from typing import Dict, List, Optional
from pathlib import Path

# Try to import PDF parsing libraries (both are FREE and open source)
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

# Try to import spaCy for NLP processing
try:
    import spacy
    SPACY_AVAILABLE = True
    try:
        # Try to load the English model
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        # Model not installed - will work but with limited functionality
        nlp = None
        print("Warning: spaCy model not loaded. Run: python -m spacy download en_core_web_sm")
except ImportError:
    SPACY_AVAILABLE = False
    nlp = None
    print("Warning: spaCy not installed. Install with: pip install spacy")


class PDFResumeParser:
    """
    PDF Resume Parser - Extracts structured information from resume PDFs.
    
    How it works:
    1. Extracts text from PDF using pdfplumber
    2. Uses spaCy to identify entities (names, organizations, dates)
    3. Uses regex patterns to extract structured information
    4. Organizes data into JSON format
    """
    
    def __init__(self):
        """
        Initialize the PDF resume parser.
        Sets up NLP model if available.
        """
        self.nlp = nlp  # spaCy model (if available)
        
        # Common section headers to look for in resumes
        # These help identify where different information is located
        self.section_keywords = {
            "skills": ["skills", "technical skills", "competencies", "expertise", "technologies"],
            "education": ["education", "academic", "qualifications", "degree", "university"],
            "experience": ["experience", "work experience", "employment", "work history", "professional experience"],
            "projects": ["projects", "portfolio", "work samples", "key projects"],
            "certifications": ["certifications", "certificates", "licenses", "credentials"],
        }
        
        # Common degree patterns
        self.degree_patterns = [
            r'\b(BS|B\.S\.|Bachelor|BA|B\.A\.|B\.Sc\.|BSc)\b',
            r'\b(MS|M\.S\.|Master|MA|M\.A\.|M\.Sc\.|MSc|M\.Tech|MTech)\b',
            r'\b(PhD|Ph\.D\.|Doctorate|D\.Sc\.)\b',
        ]
    
    def parse_pdf(self, pdf_path: str) -> Dict:
        """
        Main method to parse a PDF resume.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with structured resume data:
            {
                "skills": [],
                "education": [],
                "experience": [],
                "projects": []
            }
        """
        # Step 1: Extract text from PDF
        resume_text = self._extract_text_from_pdf(pdf_path)
        
        if not resume_text:
            raise ValueError(f"Could not extract text from PDF: {pdf_path}")
        
        # Step 2: Extract structured information using multiple methods
        result = {
            "skills": self._extract_skills(resume_text),
            "education": self._extract_education(resume_text),
            "experience": self._extract_experience(resume_text),
            "projects": self._extract_projects(resume_text),
        }
        
        # Step 3: Add basic information if available
        result["name"] = self._extract_name(resume_text)
        result["email"] = self._extract_email(resume_text)
        result["phone"] = self._extract_phone(resume_text)
        
        return result
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract raw text from PDF file.
        
        Uses pdfplumber (preferred) or PyPDF2 (fallback) - both are FREE.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text as string
        """
        text = ""
        
        # Method 1: Try pdfplumber (better text extraction)
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    # Extract text from all pages
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                return text.strip()
            except Exception as e:
                print(f"Error using pdfplumber: {e}")
                # Fall through to PyPDF2
        
        # Method 2: Fallback to PyPDF2
        if PYPDF2_AVAILABLE:
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    # Extract text from all pages
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                return text.strip()
            except Exception as e:
                print(f"Error using PyPDF2: {e}")
        
        raise ValueError("Could not extract text. Install pdfplumber: pip install pdfplumber")
    
    def _extract_skills(self, text: str) -> List[str]:
        """
        Extract skills from resume text.
        
        How it works:
        1. Looks for a "Skills" section
        2. Extracts items from that section (comma/semicolon/bullet separated)
        3. Also scans entire text for common technical terms
        4. Uses spaCy to identify technical entities if available
        
        Args:
            text: Resume text
            
        Returns:
            List of skill names
        """
        skills = set()  # Use set to avoid duplicates
        
        # Step 1: Find the Skills section
        skills_section = self._find_section(text, "skills")
        
        if skills_section:
            # Step 2: Extract skills from the section
            # Skills are often separated by commas, semicolons, or bullet points
            skill_items = re.split(r'[,;•\-\n]', skills_section)
            
            for item in skill_items:
                item = item.strip()
                # Filter out empty strings and very short items
                if item and len(item) > 2 and len(item) < 50:
                    # Remove common prefixes
                    item = re.sub(r'^(proficient in|experienced with|knowledge of)\s+', '', item, flags=re.IGNORECASE)
                    skills.add(item)
        
        # Step 3: Extract common technical skills from entire text using patterns
        # This helps catch skills mentioned elsewhere in the resume
        technical_patterns = {
            r'\bpython\b': 'Python',
            r'\bjava\b': 'Java',
            r'\bjavascript\b': 'JavaScript',
            r'\btypescript\b': 'TypeScript',
            r'\bsql\b': 'SQL',
            r'\bhtml\b': 'HTML',
            r'\bcss\b': 'CSS',
            r'\baws\b': 'AWS',
            r'\bdocker\b': 'Docker',
            r'\bkubernetes\b': 'Kubernetes',
            r'\btensorflow\b': 'TensorFlow',
            r'\bpytorch\b': 'PyTorch',
            r'\bkeras\b': 'Keras',
            r'\bscikit-learn\b': 'Scikit-learn',
            r'\bgit\b': 'Git',
            r'\bmachine learning\b': 'Machine Learning',
            r'\bdeep learning\b': 'Deep Learning',
            r'\bdata science\b': 'Data Science',
        }
        
        text_lower = text.lower()
        for pattern, skill_name in technical_patterns.items():
            if re.search(pattern, text_lower):
                skills.add(skill_name)
        
        # Step 4: Use spaCy to identify technical entities (if available)
        if self.nlp:
            doc = self.nlp(text)
            # Look for proper nouns and technical terms
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PRODUCT"]:
                    # Check if it looks like a technology name
                    if self._is_technology(ent.text):
                        skills.add(ent.text)
        
        return sorted(list(skills))
    
    def _extract_education(self, text: str) -> List[Dict]:
        """
        Extract education information from resume.
        
        How it works:
        1. Finds the Education section
        2. Extracts degree names (BS, MS, PhD, etc.)
        3. Extracts institution names using spaCy
        4. Extracts dates/years
        
        Args:
            text: Resume text
            
        Returns:
            List of education entries, each with degree, institution, year (if found)
        """
        education_list = []
        
        # Step 1: Find the Education section
        education_section = self._find_section(text, "education")
        
        if not education_section:
            # If no explicit section, search entire text
            education_section = text
        
        # Step 2: Extract degrees using patterns
        degrees_found = []
        for pattern in self.degree_patterns:
            matches = re.finditer(pattern, education_section, re.IGNORECASE)
            for match in matches:
                degrees_found.append(match.group())
        
        # Step 3: Extract institution names using spaCy (if available)
        institutions = []
        if self.nlp:
            doc = self.nlp(education_section)
            for ent in doc.ents:
                if ent.label_ == "ORG":  # Organization entity
                    institutions.append(ent.text)
        
        # Step 4: Extract years (graduation dates)
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, education_section)
        years = [f"{year[0]}{year[1]}" if isinstance(year, tuple) else year for year in years]
        
        # Step 5: Combine into structured format
        # Create one entry per degree found
        for i, degree in enumerate(degrees_found):
            edu_entry = {
                "degree": degree,
                "institution": institutions[i] if i < len(institutions) else None,
                "year": years[i] if i < len(years) else None,
            }
            education_list.append(edu_entry)
        
        # If no structured data found, try to extract lines from education section
        if not education_list and education_section:
            # Split into lines and try to extract from first few lines
            lines = education_section.split('\n')[:5]  # First 5 lines
            for line in lines:
                line = line.strip()
                if line and len(line) > 10:  # Meaningful line
                    education_list.append({"degree": None, "institution": line, "year": None})
        
        return education_list
    
    def _extract_experience(self, text: str) -> List[Dict]:
        """
        Extract work experience from resume.
        
        How it works:
        1. Finds the Experience section
        2. Uses spaCy to identify organizations and dates
        3. Extracts job titles using patterns
        4. Groups information by position
        
        Args:
            text: Resume text
            
        Returns:
            List of experience entries, each with title, company, dates
        """
        experience_list = []
        
        # Step 1: Find the Experience section
        experience_section = self._find_section(text, "experience")
        
        if not experience_section:
            return experience_list
        
        # Step 2: Split into individual positions (usually separated by dates or company names)
        # Look for patterns like "2020 - 2021" or "Company Name"
        position_separators = r'(\d{4}\s*[-–—]\s*\d{4}|\d{4}\s*[-–—]\s*Present|\w+\s+\d{4})'
        positions = re.split(position_separators, experience_section)
        
        # Step 3: Extract information from each position
        companies = []
        dates = []
        
        if self.nlp:
            doc = self.nlp(experience_section)
            # Extract organizations (companies)
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    companies.append(ent.text)
            # Extract dates
            for ent in doc.ents:
                if ent.label_ == "DATE":
                    dates.append(ent.text)
        
        # Step 4: Extract job titles (usually before company names)
        # Common patterns: "Software Engineer at Company" or "Position | Company"
        title_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:at|@|—|-|\|)\s+'
        titles = re.findall(title_pattern, experience_section)
        
        # Step 5: Combine into structured format
        # Create entries based on what we found
        max_items = max(len(companies), len(dates), len(titles))
        
        for i in range(min(max_items, 10)):  # Limit to 10 entries
            exp_entry = {
                "title": titles[i] if i < len(titles) else None,
                "company": companies[i] if i < len(companies) else None,
                "dates": dates[i] if i < len(dates) else None,
            }
            if any(exp_entry.values()):  # Only add if we found something
                experience_list.append(exp_entry)
        
        return experience_list
    
    def _extract_projects(self, text: str) -> List[str]:
        """
        Extract projects from resume.
        
        How it works:
        1. Finds the Projects section
        2. Splits into individual projects (usually bullet points or separate lines)
        3. Cleans up each project description
        
        Args:
            text: Resume text
            
        Returns:
            List of project descriptions
        """
        projects = []
        
        # Step 1: Find the Projects section
        projects_section = self._find_section(text, "projects")
        
        if not projects_section:
            return projects
        
        # Step 2: Split into individual projects
        # Projects are often separated by bullet points, dashes, or new lines with numbers
        project_items = re.split(r'[\n•\-]\s*(?=\w)', projects_section)
        
        # Step 3: Clean and filter projects
        for item in project_items:
            item = item.strip()
            # Filter out empty strings and very short items
            if item and len(item) > 10:  # Meaningful project description
                # Remove common prefixes
                item = re.sub(r'^(\d+\.|•|-)\s*', '', item)
                projects.append(item)
        
        return projects
    
    def _find_section(self, text: str, section_type: str) -> Optional[str]:
        """
        Find a specific section in the resume text.
        
        How it works:
        1. Looks for section headers using keywords
        2. Extracts text until the next section header
        
        Args:
            text: Resume text
            section_type: Type of section to find (e.g., "skills", "education")
            
        Returns:
            Section text or None if not found
        """
        keywords = self.section_keywords.get(section_type, [])
        
        # Step 1: Find where the section starts
        start_idx = None
        for keyword in keywords:
            # Look for section header (case-insensitive)
            pattern = rf'({keyword}[\s:]*\n)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start_idx = match.end()
                break
        
        if start_idx is None:
            return None
        
        # Step 2: Find where the section ends (next section header)
        # Look for other section keywords after the start
        remaining_text = text[start_idx:]
        end_idx = len(remaining_text)
        
        # Find the next section header
        all_keywords = []
        for kw_list in self.section_keywords.values():
            all_keywords.extend(kw_list)
        
        for keyword in all_keywords:
            if keyword not in keywords:  # Different section
                pattern = rf'({keyword}[\s:]*\n)'
                match = re.search(pattern, remaining_text, re.IGNORECASE)
                if match:
                    end_idx = min(end_idx, match.start())
        
        # Step 3: Extract section text
        section_text = remaining_text[:end_idx].strip()
        return section_text if section_text else None
    
    def _extract_name(self, text: str) -> Optional[str]:
        """
        Extract name from resume (usually first line).
        
        Args:
            text: Resume text
            
        Returns:
            Name or None
        """
        lines = text.split('\n')
        if lines:
            first_line = lines[0].strip()
            # Simple heuristic: first line that's not too long and has capital letters
            if len(first_line) < 50 and any(c.isupper() for c in first_line):
                return first_line
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """
        Extract email address from text.
        
        Args:
            text: Resume text
            
        Returns:
            Email or None
        """
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(pattern, text)
        return match.group() if match else None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """
        Extract phone number from text.
        
        Args:
            text: Resume text
            
        Returns:
            Phone number or None
        """
        patterns = [
            r'\b\d{3}-\d{3}-\d{4}\b',  # 123-456-7890
            r'\b\(\d{3}\)\s?\d{3}-\d{4}\b',  # (123) 456-7890
            r'\b\d{10}\b',  # 1234567890
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        
        return None
    
    def _is_technology(self, text: str) -> bool:
        """
        Check if a text looks like a technology name.
        
        Simple heuristic - can be enhanced.
        
        Args:
            text: Text to check
            
        Returns:
            True if likely a technology name
        """
        # Common technology indicators
        tech_indicators = ['cloud', 'framework', 'library', 'tool', 'platform']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in tech_indicators)
    
    def parse_to_json(self, pdf_path: str, output_path: Optional[str] = None) -> str:
        """
        Parse PDF and return/save as JSON.
        
        Args:
            pdf_path: Path to PDF file
            output_path: Optional path to save JSON file
            
        Returns:
            JSON string of parsed data
        """
        # Parse the PDF
        result = self.parse_pdf(pdf_path)
        
        # Convert to JSON
        json_str = json.dumps(result, indent=2, ensure_ascii=False)
        
        # Save to file if output path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            print(f"Saved parsed resume to: {output_path}")
        
        return json_str

