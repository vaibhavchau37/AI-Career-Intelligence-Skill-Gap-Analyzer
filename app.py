"""
AI Career Intelligence & Skill Gap Analyzer - Streamlit Web App

A clean, simple, college-presentation ready web interface for career analysis.
"""

import streamlit as st

# Local dev convenience: load environment variables from .env (ignored by git)
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


def _has_config_value(key_name: str) -> bool:
    """Return True if a config value exists in env or Streamlit secrets."""
    if os.getenv(key_name):
        return True
    try:
        return bool(st.secrets.get(key_name))
    except Exception:
        return False


def _default_ai_provider() -> str:
    # Prefer providers that are configured to avoid confusing quota errors.
    if _has_config_value("GOOGLE_GEMINI_API_KEY"):
        return "Gemini"
    if _has_config_value("SAMBANOVA_API_KEY"):
        return "SambaNova"
    return "OpenAI"
import sys
from pathlib import Path
import json
import time
import yaml
import os
import difflib
import html
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.pdf_resume_parser import PDFResumeParser
from src.core.skill_gap_analyzer_tfidf import SkillGapAnalyzerTFIDF
from src.core.job_readiness_scorer import JobReadinessScorer
from src.core.skill_extractor import SkillExtractor
from src.matcher.role_suitability_predictor import RoleSuitabilityPredictor
from src.roadmap.personalized_roadmap_generator import PersonalizedRoadmapGenerator
from src.api.interview_ai import start_interview, interview_turn, generate_skill_questions
from src.api.job_market_analyzer import JobMarketAnalyzer

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will use environment variables directly

# Page configuration
st.set_page_config(
    page_title="AI Career Intelligence Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .score-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
    .skill-match {
        color: #28a745;
        font-weight: bold;
    }
    .skill-missing {
        color: #dc3545;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
    }
    .nav-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .progress-step {
        display: inline-block;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        text-align: center;
        line-height: 30px;
        margin: 0 5px;
        font-weight: bold;
    }
    .step-completed {
        background-color: #28a745;
        color: white;
    }
    .step-current {
        background-color: #1f77b4;
        color: white;
    }
    .step-pending {
        background-color: #e0e0e0;
        color: #6c757d;
    }
    .resume-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .info-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .skill-badge {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        margin: 5px;
        font-size: 0.9rem;
        font-weight: 500;
    }
    .experience-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 3px solid #28a745;
        margin: 10px 0;
    }
    .project-card {
        background: #fff3cd;
        padding: 15px;
        border-radius: 8px;
        border-left: 3px solid #ffc107;
        margin: 10px 0;
    }
    .education-card {
        background: #d1ecf1;
        padding: 15px;
        border-radius: 8px;
        border-left: 3px solid #17a2b8;
        margin: 10px 0;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .scanning-animation {
        display: inline-block;
        animation: scan 2s infinite;
    }
    @keyframes scan {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    .upload-area {
        border: 3px dashed #1f77b4;
        border-radius: 10px;
        padding: 40px;
        text-align: center;
        background: #f0f2f6;
        transition: all 0.3s;
    }
    .upload-area:hover {
        background: #e0e7f0;
        border-color: #764ba2;
    }
</style>
""", unsafe_allow_html=True)


def load_combined_skills():
    """Load combined skills from extracted LinkedIn data."""
    try:
        with open("data/combined_skills.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            # Extract skill names from skills_by_frequency array
            skills_list = [item['skill'] for item in data.get('skills_by_frequency', [])]
            return {
                'total_skills': data.get('total_skills', 0),
                'skills_list': skills_list,
                'skills_by_frequency': data.get('skills_by_frequency', [])
            }
    except Exception as e:
        st.warning(f"Could not load combined skills data: {e}")
        return {'total_skills': 0, 'skills_list': [], 'skills_by_frequency': []}


def load_combined_job_titles():
    """Load combined job titles from extracted LinkedIn data."""
    try:
        with open("data/combined_job_titles.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            # Extract title names from titles_by_frequency array
            titles_list = [item['title'] for item in data.get('titles_by_frequency', [])]
            return {
                'total_titles': data.get('total_titles', 0),
                'titles_list': titles_list,
                'titles_by_frequency': data.get('titles_by_frequency', [])
            }
    except Exception as e:
        st.warning(f"Could not load combined job titles data: {e}")
        return {'total_titles': 0, 'titles_list': [], 'titles_by_frequency': []}


@st.cache_data(show_spinner=False)
def load_market_job_titles() -> dict:
    """Load job titles from all available datasets (JSON + CSV) for the role dropdown.

    Returns:
        dict with keys:
        - titles: List[str]
        - title_counts: Dict[str, int] (0 when unknown)
    """

    def normalize_title(value: str) -> str:
        value = html.unescape(str(value or "")).strip()
        # Collapse whitespace
        value = " ".join(value.split())
        return value

    def simplify_linkedin_job_field(value: str) -> str:
        """Best-effort clean-up for the noisy `job` field in linkdin_Job_data.csv."""
        value = normalize_title(value)
        if not value:
            return value
        # Remove salary / extra details after " - "
        if " - " in value:
            value = value.split(" - ", 1)[0].strip()
        # Remove company portion after first comma
        if "," in value:
            value = value.split(",", 1)[0].strip()
        return value

    titles: list[str] = []
    title_counts: dict[str, int] = {}

    # 1) Combined JSON (already curated + deduped with counts)
    try:
        with open("data/combined_job_titles.json", "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        for item in data.get("titles_by_frequency", []) or []:
            t = normalize_title(item.get("title", ""))
            if not t:
                continue
            if t not in title_counts:
                titles.append(t)
            title_counts[t] = int(item.get("count", 0) or 0)
    except Exception:
        pass

    # 2) Extracted JSON (smaller dataset)
    try:
        with open("data/extracted_job_titles.json", "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        for item in data.get("titles_by_frequency", []) or []:
            t = normalize_title(item.get("title", ""))
            if not t:
                continue
            if t not in title_counts:
                titles.append(t)
            # Only set count if we don't already have a better one
            title_counts.setdefault(t, int(item.get("count", 0) or 0))
    except Exception:
        pass

    # 3) CSV datasets (optional; may add titles not present in JSON)
    try:
        import pandas as pd

        # a) Noisy dataset: `job` column
        try:
            df = pd.read_csv("linkdin_Job_data.csv", usecols=["job"], dtype=str)
            for raw in df["job"].dropna().tolist():
                t = simplify_linkedin_job_field(raw)
                if not t:
                    continue
                if t not in title_counts:
                    titles.append(t)
                    title_counts[t] = 0
        except Exception:
            pass

        # b) Cleaner dataset: `title` column
        try:
            df = pd.read_csv("LinkedIn_Jobs_Data_India.csv", usecols=["title"], dtype=str)
            for raw in df["title"].dropna().tolist():
                t = normalize_title(raw)
                if not t:
                    continue
                if t not in title_counts:
                    titles.append(t)
                    title_counts[t] = 0
        except Exception:
            pass
    except Exception:
        # pandas not available
        pass

    return {"titles": titles, "title_counts": title_counts}


def build_role_options(curated_role_names: list[str], market_titles: list[str]) -> list[str]:
    """Combine curated roles with market job titles for the dropdown."""
    seen = set()
    options: list[str] = []

    # Keep curated roles first
    for r in curated_role_names:
        if r and r not in seen:
            options.append(r)
            seen.add(r)

    # Add market titles
    for t in market_titles:
        if t and t not in seen:
            options.append(t)
            seen.add(t)

    return options


def resolve_role_template(selected_title: str, curated_role_names: list[str]) -> str | None:
    """Map an arbitrary job title to the closest curated role template."""
    if not selected_title:
        return None
    if selected_title in curated_role_names:
        return selected_title

    title_lower = selected_title.lower()
    # Prefer substring matches (more intuitive)
    for role in curated_role_names:
        if role and role.lower() in title_lower:
            return role

    # Fallback to fuzzy match
    matches = difflib.get_close_matches(selected_title, curated_role_names, n=1, cutoff=0.25)
    return matches[0] if matches else None


def get_role_info_for_selection(
    selected_title: str,
    job_roles: dict,
    curated_role_names: list[str],
    combined_skills_data: dict,
) -> tuple[dict, str | None]:
    """Return a role_info dict for a selected dropdown value.

    For curated roles, returns their data directly.
    For market titles, returns the closest curated role template (or a safe fallback).
    """
    if selected_title in job_roles:
        return job_roles[selected_title], selected_title

    template = resolve_role_template(selected_title, curated_role_names)
    if template and template in job_roles:
        role_info = dict(job_roles[template])
        desc = role_info.get("description", "") or ""
        suffix = f"(Analyzed using skills template: {template})"
        role_info["description"] = (desc + "\n\n" + suffix).strip()
        return role_info, template

    # Ultimate fallback: use top market skills as a generic baseline
    skills_by_freq = combined_skills_data.get("skills_by_frequency", []) or []
    top_skills = [s.get("skill") for s in skills_by_freq if isinstance(s, dict) and s.get("skill")]
    top_skills = [str(s).strip() for s in top_skills if str(s).strip()]
    required = top_skills[:8]
    optional = top_skills[8:25]
    return {
        "description": "Market job title selected (no exact template found). Using common in-demand skills.",
        "required_skills": required,
        "optional_skills": optional,
    }, None


@st.cache_data(show_spinner=False)
def derive_role_skills_from_live_jobs(job_descriptions: list[str]) -> dict:
    """Derive required/optional skills from live job descriptions.

    Uses the existing taxonomy-based `SkillExtractor` (no LLM / no demo data).
    """
    # Load extractor with taxonomy/synonyms from config
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except Exception:
        cfg = {}

    taxonomy_path = (cfg.get("skills") or {}).get("taxonomy_path")
    synonyms_path = (cfg.get("skills") or {}).get("synonyms_path")
    extractor = SkillExtractor(skill_taxonomy_path=taxonomy_path, skill_synonyms_path=synonyms_path)

    from collections import Counter
    counts: Counter = Counter()
    for desc in job_descriptions:
        text = str(desc or "")
        if not text.strip():
            continue
        # SkillExtractor expects a Resume object normally; use the internal text extractor
        skills = extractor._extract_from_text(text)
        for s in skills:
            s = str(s).strip()
            if s:
                counts[s] += 1

    ranked = [s for s, _ in counts.most_common()]
    required = ranked[:10]
    optional = ranked[10:30]
    return {
        "required_skills": required,
        "optional_skills": optional,
        "skill_counts": dict(counts),
    }


def get_active_role_info(selected_role: str, job_roles: dict, curated_role_names: list[str]) -> dict:
    """Get the role_info used for analysis.

    Priority:
    1) Use the role info computed during real-time selection (stored in session_state)
    2) Use closest curated template
    3) Derive from live jobs currently in session (if present)
    """
    cached = st.session_state.get("selected_role_info")
    if cached and st.session_state.get("selected_role") == selected_role:
        return cached

    template = resolve_role_template(selected_role, curated_role_names)
    if template and template in job_roles:
        role_info = dict(job_roles[template])
        desc = role_info.get("description", "") or ""
        role_info["description"] = (desc + f"\n\n(Analyzed using skills template: {template})").strip()
        return role_info

    jobs_live = st.session_state.get("realtime_jobs", []) or []
    descriptions = [str((j or {}).get("description", "")) for j in jobs_live]
    if any(d.strip() for d in descriptions):
        derived = derive_role_skills_from_live_jobs(descriptions)
        return {
            "description": "Skills derived from live Adzuna job descriptions for this search.",
            "required_skills": derived.get("required_skills", []),
            "optional_skills": derived.get("optional_skills", []),
        }

    return {
        "description": "No role template or live job data available for skill derivation.",
        "required_skills": [],
        "optional_skills": [],
    }


def load_job_roles():
    """Load job roles from YAML files."""
    job_roles = {}
    yaml_files_dir = "data/job_roles"
    
    def normalize_skills(skills_list):
        """Convert skills list to simple string list, handling both dict and string formats."""
        if not skills_list:
            return []
        
        normalized = []
        for skill in skills_list:
            if isinstance(skill, dict):
                # Extract 'name' field from dict
                skill_name = skill.get('name', '')
                if skill_name:
                    normalized.append(skill_name)
            elif isinstance(skill, str):
                # Already a string
                normalized.append(skill)
        return normalized
    
    try:
        # Get all YAML files in the directory
        yaml_files = [f for f in os.listdir(yaml_files_dir) if f.endswith('.yaml')]
        
        for yaml_file in yaml_files:
            try:
                with open(os.path.join(yaml_files_dir, yaml_file), 'r', encoding='utf-8') as f:
                    role_data = yaml.safe_load(f)
                    if role_data:
                        # Extract role name from filename (e.g., data_scientist.yaml -> Data Scientist)
                        role_name = yaml_file.replace('.yaml', '').replace('_', ' ').title()
                        
                        # If the YAML has a 'name' field, use that instead
                        if 'name' in role_data:
                            role_name = role_data['name']
                        
                        # Normalize skills to simple string lists
                        if 'required_skills' in role_data:
                            role_data['required_skills'] = normalize_skills(role_data['required_skills'])
                        if 'optional_skills' in role_data:
                            role_data['optional_skills'] = normalize_skills(role_data['optional_skills'])
                        if 'preferred_skills' in role_data:
                            role_data['preferred_skills'] = normalize_skills(role_data['preferred_skills'])
                        
                        job_roles[role_name] = role_data
            except Exception as e:
                st.warning(f"Could not load {yaml_file}: {e}")
                continue
        
        return job_roles
    except Exception as e:
        st.error(f"Error loading job roles directory: {e}")
        # Fallback to skill_mapping.json if YAML loading fails
        try:
            with open("data/job_roles/skill_mapping.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("job_roles", {})
        except:
            return {}


def main():
    """Main Streamlit app."""
    
    # Header
    st.markdown('<div class="main-header">🎯 AI Career Intelligence & Skill Gap Analyzer</div>', 
                unsafe_allow_html=True)
    
    # Initialize session state
    if 'resume_data' not in st.session_state:
        st.session_state.resume_data = None
    if 'selected_role' not in st.session_state:
        st.session_state.selected_role = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    
    # Progress tracking
    has_resume = st.session_state.get('resume_data') is not None
    has_role = st.session_state.get('selected_role') is not None
    has_gaps = 'skill_gaps' in st.session_state.get('analysis_results', {})
    has_score = 'readiness_score' in st.session_state.get('analysis_results', {})
    has_suitability = 'suitability' in st.session_state.get('analysis_results', {})
    has_roadmap = 'roadmap' in st.session_state.get('analysis_results', {})
    has_interview = bool(st.session_state.get('interview_state', {}).get('started'))
    
    completion_status = [has_resume, has_role, has_gaps, has_score, has_suitability, has_roadmap, has_interview]
    completed_count = sum(completion_status)
    progress_pct = (completed_count / 7) * 100
    
    # Progress bar at top
    st.markdown(f"""
    <div class="nav-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h3 style="margin: 0; color: white;">Progress Tracker</h3>
            <span style="font-size: 1.2rem; font-weight: bold;">{completed_count}/6 Steps</span>
        </div>
        <div style="background-color: rgba(255,255,255,0.3); height: 15px; border-radius: 8px; overflow: hidden; margin-bottom: 15px;">
            <div style="background-color: white; height: 100%; width: {progress_pct}%; transition: width 0.3s; border-radius: 8px;"></div>
        </div>
        <div style="display: flex; justify-content: space-around; align-items: center;">
            <div class="progress-step {'step-completed' if has_resume else 'step-current' if not has_resume else 'step-pending'}">1</div>
            <div class="progress-step {'step-completed' if has_role else 'step-current' if has_resume and not has_role else 'step-pending'}">2</div>
            <div class="progress-step {'step-completed' if has_gaps else 'step-current' if has_role and not has_gaps else 'step-pending'}">3</div>
            <div class="progress-step {'step-completed' if has_score else 'step-current' if has_gaps and not has_score else 'step-pending'}">4</div>
            <div class="progress-step {'step-completed' if has_suitability else 'step-current' if has_score and not has_suitability else 'step-pending'}">5</div>
            <div class="progress-step {'step-completed' if has_roadmap else 'step-current' if has_suitability and not has_roadmap else 'step-pending'}">6</div>
            <div class="progress-step {'step-completed' if has_interview else 'step-current' if has_roadmap and not has_interview else 'step-pending'}">7</div>
        </div>
        <div style="display: flex; justify-content: space-around; margin-top: 10px; font-size: 0.85rem;">
            <span>Resume</span>
            <span>Role</span>
            <span>Gaps</span>
            <span>Score</span>
            <span>Suitability</span>
            <span>Roadmap</span>
            <span>Interview</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📄 Resume Upload",
        "🎯 Select Role", 
        "📊 Skill Gaps",
        "⭐ Readiness Score",
        "🔍 Role Suitability",
        "🗺️ Learning Roadmap",
        "🧠 Interview & Practice AI"
    ])
    
    # Load job roles
    job_roles = load_job_roles()
    curated_role_names = list(job_roles.keys()) if job_roles else []
    
    # Note: Role selection is now real-time (Adzuna-driven) to avoid demo/offline data.
    
    # Initialize job market analyzer
    try:
        job_market = JobMarketAnalyzer()
    except Exception as e:
        job_market = None
        # API not configured - will show setup instructions
    
    # Tab 1: Resume Upload
    with tab1:
        st.markdown('<div class="sub-header">📄 Upload Your Resume</div>', unsafe_allow_html=True)
        
        # Upload section with enhanced UI
        if not has_resume:
            st.markdown("""
            <div class="upload-area">
                <h3 style="color: #1f77b4; margin-bottom: 10px;">📤 Ready to Upload Your Resume?</h3>
                <p style="color: #666;">Upload your resume in PDF format to begin comprehensive analysis</p>
            </div>
            """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if not has_resume:
                st.info("📋 **Instructions:** Upload your resume PDF. Our AI will scan and extract all relevant information including skills, experience, education, and projects.")
            else:
                resume_data = st.session_state.resume_data
                st.markdown(f"""
                <div class="resume-card">
                    <h3 style="margin: 0; color: white;">✅ Resume Successfully Loaded</h3>
                    <p style="margin: 5px 0; opacity: 0.9;">Ready for comprehensive analysis</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            if has_resume:
                resume_data = st.session_state.resume_data
                skills_count = len(resume_data.get('skills', []))
                st.metric("🎯 Skills Found", skills_count)
        
        with col3:
            if has_resume:
                resume_data = st.session_state.resume_data
                exp_count = len(resume_data.get('experience', []))
                st.metric("💼 Experience", exp_count)
        
        uploaded_file = st.file_uploader(
            "📎 Choose a PDF file",
            type=['pdf'],
            help="Upload your resume as a PDF file (max 10MB)",
            key="resume_uploader"
        )
        
        if uploaded_file is not None:
            try:
                # Save uploaded file temporarily
                with open("temp_resume.pdf", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Enhanced scanning animation
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Simulate scanning steps
                steps = [
                    "📄 Reading PDF file...",
                    "🔍 Extracting text content...",
                    "🤖 Analyzing with AI...",
                    "📊 Identifying skills...",
                    "💼 Parsing experience...",
                    "🎓 Extracting education...",
                    "🚀 Finding projects...",
                    "✅ Finalizing analysis..."
                ]
                
                for i, step in enumerate(steps):
                    status_text.markdown(f"""
                    <div style="text-align: center; padding: 20px;">
                        <h3 class="scanning-animation">{step}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    progress_bar.progress((i + 1) / len(steps))
                    time.sleep(0.3)  # Small delay for animation effect
                
                # Parse PDF
                parser = PDFResumeParser()
                resume_data = parser.parse_pdf("temp_resume.pdf")
                st.session_state.resume_data = resume_data
                
                progress_bar.progress(1.0)
                status_text.empty()
                progress_bar.empty()
                
                st.success("✅ Resume parsed successfully!")
                st.balloons()
                
                # Show immediate preview
                st.markdown("---")
                st.info("📋 **Resume parsed!** Your complete resume profile is displayed below. Scroll down to see all details.")
                
                # Update has_resume check for immediate display
                has_resume = True
                
            except Exception as e:
                st.error(f"❌ Error parsing resume: {e}")
                st.info("💡 **Troubleshooting:** Please ensure your PDF contains text (not just images). Try converting your resume to a text-based PDF.")
        
        # Display comprehensive resume information
        # Check if resume data exists in session state (more reliable than has_resume variable)
        if st.session_state.get('resume_data') is not None:
            resume_data = st.session_state.resume_data
            
            # Resume Statistics Dashboard
            st.markdown("---")
            st.subheader("📊 Resume Statistics Dashboard")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                skills_count = len(resume_data.get('skills', []))
                st.markdown(f"""
                <div class="stat-card">
                    <h2 style="margin: 0; font-size: 2rem;">{skills_count}</h2>
                    <p style="margin: 5px 0; opacity: 0.9;">Skills Identified</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                exp_count = len(resume_data.get('experience', []))
                st.markdown(f"""
                <div class="stat-card">
                    <h2 style="margin: 0; font-size: 2rem;">{exp_count}</h2>
                    <p style="margin: 5px 0; opacity: 0.9;">Work Experiences</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                edu_count = len(resume_data.get('education', []))
                st.markdown(f"""
                <div class="stat-card">
                    <h2 style="margin: 0; font-size: 2rem;">{edu_count}</h2>
                    <p style="margin: 5px 0; opacity: 0.9;">Education Entries</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                proj_count = len(resume_data.get('projects', []))
                st.markdown(f"""
                <div class="stat-card">
                    <h2 style="margin: 0; font-size: 2rem;">{proj_count}</h2>
                    <p style="margin: 5px 0; opacity: 0.9;">Projects Listed</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Main Resume Display
            st.markdown("---")
            st.subheader("📋 Complete Resume Profile")
            
            # Personal Information Card
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown("### 👤 Personal Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if resume_data.get('name'):
                    st.markdown(f"**👤 Full Name:** {resume_data['name']}")
                if resume_data.get('email'):
                    st.markdown(f"**📧 Email:** [{resume_data['email']}](mailto:{resume_data['email']})")
            
            with col2:
                if resume_data.get('phone'):
                    st.markdown(f"**📱 Phone:** {resume_data['phone']}")
                if resume_data.get('location'):
                    st.markdown(f"**📍 Location:** {resume_data['location']}")
                elif resume_data.get('address'):
                    st.markdown(f"**📍 Address:** {resume_data['address']}")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Skills Section
            skills = resume_data.get('skills', [])
            if skills:
                st.markdown("---")
                st.subheader("💼 Technical Skills")
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                
                # Display skills as badges
                skills_html = "".join([f'<span class="skill-badge">{skill}</span>' for skill in skills])
                st.markdown(f'<div style="margin: 10px 0;">{skills_html}</div>', unsafe_allow_html=True)
                
                # Skills categorization (if available)
                if len(skills) > 0:
                    st.caption(f"📊 Total: {len(skills)} skills identified")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Experience Section
            experience = resume_data.get('experience', [])
            if experience:
                st.markdown("---")
                st.subheader("💼 Professional Experience")
                
                for i, exp in enumerate(experience, 1):
                    st.markdown('<div class="experience-card">', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        title = exp.get('title', 'N/A')
                        company = exp.get('company', '')
                        if company:
                            st.markdown(f"**{i}. {title}** at **{company}**")
                        else:
                            st.markdown(f"**{i}. {title}**")
                    
                    with col2:
                        dates = exp.get('dates', '')
                        if dates:
                            st.caption(f"📅 {dates}")
                    
                    # Description
                    if exp.get('description'):
                        st.write(exp['description'])
                    elif exp.get('responsibilities'):
                        st.write("**Responsibilities:**")
                        for resp in exp['responsibilities']:
                            st.write(f"• {resp}")
                    
                    # Location
                    if exp.get('location'):
                        st.caption(f"📍 {exp['location']}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Education Section
            education = resume_data.get('education', [])
            if education:
                st.markdown("---")
                st.subheader("🎓 Education")
                
                for i, edu in enumerate(education, 1):
                    st.markdown('<div class="education-card">', unsafe_allow_html=True)
                    
                    degree = edu.get('degree', '')
                    institution = edu.get('institution', '')
                    if degree and institution:
                        st.markdown(f"**{i}. {degree}** from **{institution}**")
                    elif degree:
                        st.markdown(f"**{i}. {degree}**")
                    elif institution:
                        st.markdown(f"**{i}. {institution}**")
                    
                    if edu.get('dates'):
                        st.caption(f"📅 {edu['dates']}")
                    
                    if edu.get('gpa') or edu.get('grade'):
                        gpa_info = edu.get('gpa', '') or edu.get('grade', '')
                        st.caption(f"📊 GPA/Grade: {gpa_info}")
                    
                    if edu.get('description'):
                        st.write(edu['description'])
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Projects Section
            projects = resume_data.get('projects', [])
            if projects:
                st.markdown("---")
                st.subheader("🚀 Projects & Portfolio")
                
                for i, project in enumerate(projects, 1):
                    st.markdown('<div class="project-card">', unsafe_allow_html=True)
                    
                    if isinstance(project, dict):
                        project_name = project.get('name', f"Project {i}")
                        project_desc = project.get('description', project.get('details', ''))
                        st.markdown(f"**{i}. {project_name}**")
                        if project_desc:
                            st.write(project_desc)
                        if project.get('technologies'):
                            tech_str = ", ".join(project['technologies'])
                            st.caption(f"🔧 Technologies: {tech_str}")
                        if project.get('url'):
                            st.markdown(f"[🔗 View Project →]({project['url']})")
                    else:
                        # If project is just a string
                        st.markdown(f"**{i}. Project {i}**")
                        st.write(str(project))
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Certifications Section
            certifications = resume_data.get('certifications', [])
            if certifications:
                st.markdown("---")
                st.subheader("🏆 Certifications")
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                
                for cert in certifications:
                    if isinstance(cert, dict):
                        cert_name = cert.get('name', '')
                        cert_org = cert.get('organization', '')
                        cert_date = cert.get('date', '')
                        if cert_name:
                            cert_str = f"**{cert_name}**"
                            if cert_org:
                                cert_str += f" from {cert_org}"
                            if cert_date:
                                cert_str += f" ({cert_date})"
                            st.write(f"• {cert_str}")
                    else:
                        st.write(f"• {cert}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Additional Information
            st.markdown("---")
            st.subheader("📝 Additional Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Languages
                languages = resume_data.get('languages', [])
                if languages:
                    st.markdown("**🌐 Languages:**")
                    for lang in languages:
                        st.write(f"• {lang}")
                
                # Interests/Hobbies
                interests = resume_data.get('interests', resume_data.get('hobbies', []))
                if interests:
                    st.markdown("**🎯 Interests:**")
                    for interest in interests:
                        st.write(f"• {interest}")
            
            with col2:
                # Summary/Objective
                summary = resume_data.get('summary', resume_data.get('objective', ''))
                if summary:
                    st.markdown("**📄 Summary/Objective:**")
                    st.write(summary)
            
            # Export Options
            st.markdown("---")
            st.subheader("💾 Export Resume Data")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Export as JSON
                resume_json = json.dumps(resume_data, indent=2, default=str)
                st.download_button(
                    label="📥 Download as JSON",
                    data=resume_json,
                    file_name=f"resume_data_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    help="Download parsed resume data in JSON format"
                )
            
            with col2:
                # Export as Text
                resume_text = f"""
RESUME PROFILE
==============

Personal Information:
- Name: {resume_data.get('name', 'N/A')}
- Email: {resume_data.get('email', 'N/A')}
- Phone: {resume_data.get('phone', 'N/A')}

Skills ({len(skills)}):
{', '.join(skills) if skills else 'None'}

Experience ({len(experience)}):
{chr(10).join([f"- {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')}" for exp in experience]) if experience else 'None'}

Education ({len(education)}):
{chr(10).join([f"- {edu.get('degree', 'N/A')} from {edu.get('institution', 'N/A')}" for edu in education]) if education else 'None'}

Projects ({len(projects)}):
{chr(10).join([f"- {str(proj)[:100]}" for proj in projects[:10]]) if projects else 'None'}
"""
                st.download_button(
                    label="📄 Download as Text",
                    data=resume_text,
                    file_name=f"resume_profile_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    help="Download resume profile as text file"
                )
            
            with col3:
                # View Raw Data
                with st.expander("🔍 View Raw Parsed Data"):
                    st.json(resume_data)
            
            # Resume Quality Score
            st.markdown("---")
            st.subheader("⭐ Resume Quality Score")
            
            # Calculate quality score
            quality_score = 0
            quality_factors = []
            
            if resume_data.get('name'):
                quality_score += 10
                quality_factors.append("✅ Name found")
            if resume_data.get('email'):
                quality_score += 10
                quality_factors.append("✅ Email found")
            if resume_data.get('phone'):
                quality_score += 10
                quality_factors.append("✅ Phone found")
            if len(skills) >= 5:
                quality_score += 20
                quality_factors.append(f"✅ Good skills coverage ({len(skills)} skills)")
            elif len(skills) > 0:
                quality_score += 10
                quality_factors.append(f"⚠️ Limited skills ({len(skills)} skills)")
            if len(experience) >= 2:
                quality_score += 20
                quality_factors.append(f"✅ Good experience history ({len(experience)} positions)")
            elif len(experience) > 0:
                quality_score += 10
                quality_factors.append(f"⚠️ Limited experience ({len(experience)} position)")
            if len(education) > 0:
                quality_score += 10
                quality_factors.append(f"✅ Education listed ({len(education)} entries)")
            if len(projects) >= 2:
                quality_score += 10
                quality_factors.append(f"✅ Good project portfolio ({len(projects)} projects)")
            elif len(projects) > 0:
                quality_score += 5
                quality_factors.append(f"⚠️ Limited projects ({len(projects)} project)")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown(f"""
                <div class="stat-card">
                    <h2 style="margin: 0; font-size: 2.5rem;">{quality_score}/100</h2>
                    <p style="margin: 5px 0; opacity: 0.9;">Quality Score</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("**Quality Factors:**")
                for factor in quality_factors:
                    st.write(factor)
                
                if quality_score >= 80:
                    st.success("🎉 Excellent resume! Well-structured and comprehensive.")
                elif quality_score >= 60:
                    st.info("💡 Good resume! Consider adding more details.")
                else:
                    st.warning("⚠️ Resume needs improvement. Add more information for better analysis.")
    
    # Tab 2: Select Target Role
    with tab2:
        st.markdown('<div class="sub-header">🎯 Select Target Job Role</div>', unsafe_allow_html=True)
        
        if not has_resume:
            st.warning("⚠️ Please upload your resume first in the 'Resume Upload' tab!")
        else:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.info("🎯 Select the job role you want to analyze your resume against.")
            
            with col2:
                if has_role:
                    st.success(f"✅ Selected: {st.session_state.selected_role}")

            st.markdown("---")
            st.subheader("🔎 Real-Time Role Search")
            st.caption("This list is built from live Adzuna job results (no offline/demo titles).")

            q_col1, q_col2 = st.columns([2, 1])
            with q_col1:
                realtime_query = st.text_input(
                    "Job title / keywords",
                    value=st.session_state.get("realtime_role_query", ""),
                    placeholder="e.g., Staff Product Manager, Data Engineer, PCC Developer",
                    help="Used to fetch real-time job listings and generate selectable titles",
                    key="realtime_role_query",
                )
            with q_col2:
                realtime_location = st.text_input(
                    "Location",
                    value=st.session_state.get("realtime_role_location", "India"),
                    placeholder="India",
                    help="Adzuna search location",
                    key="realtime_role_location",
                )

            fetch_clicked = st.button("🔄 Fetch Real-Time Titles", type="secondary")

            if fetch_clicked:
                if not job_market or not job_market.is_available():
                    st.error("Real-time API not available. Configure Adzuna API keys to enable live search.")
                elif not realtime_query or not realtime_query.strip():
                    st.warning("Please enter a job title / keywords to search.")
                else:
                    with st.spinner("Fetching live jobs from Adzuna..."):
                        jobs_live = job_market.get_jobs_for_role(
                            realtime_query.strip(),
                            location=realtime_location.strip() or "India",
                            limit=50,
                        )
                        stats_live = job_market.get_market_statistics(
                            realtime_query.strip(),
                            location=realtime_location.strip() or "India",
                        )

                    st.session_state["realtime_jobs"] = jobs_live
                    st.session_state["realtime_stats"] = stats_live

                    # Derive unique titles from the fetched jobs
                    titles = []
                    seen = set()
                    for j in jobs_live or []:
                        t = str((j or {}).get("title", "")).strip()
                        if t and t not in seen:
                            titles.append(t)
                            seen.add(t)
                    st.session_state["realtime_titles"] = titles

            realtime_titles = st.session_state.get("realtime_titles", []) or []
            jobs_live = st.session_state.get("realtime_jobs", []) or []
            stats_live = st.session_state.get("realtime_stats", {}) or {}

            if stats_live and stats_live.get("total_jobs", 0) > 0:
                st.info(f"💡 Adzuna reports {stats_live.get('total_jobs', 0):,} jobs for this search")

            # Search-within-results (client-side filter)
            local_filter = st.text_input(
                "Filter fetched titles",
                value="",
                placeholder="Type to filter the fetched titles",
                help="Filters only the titles returned from the live fetch",
                key="realtime_titles_filter",
            )

            filtered_titles = realtime_titles
            if local_filter and local_filter.strip():
                q = local_filter.strip().lower()
                filtered_titles = [t for t in realtime_titles if q in t.lower()]

            if filtered_titles:
                selected_role = st.selectbox(
                    "Choose a job title (from live results):",
                    filtered_titles,
                    help="These titles come from real-time job listings",
                    key="role_selectbox",
                )
            else:
                selected_role = realtime_query.strip() if realtime_query else ""
                if not selected_role:
                    st.warning("Fetch titles or type a job title to proceed.")

            st.session_state.selected_role = selected_role

            if selected_role:
                # Prefer curated template when close match exists; otherwise derive skills from live job descriptions
                template = resolve_role_template(selected_role, curated_role_names)
                if template and template in job_roles:
                    role_info = dict(job_roles[template])
                    desc = role_info.get("description", "") or ""
                    role_info["description"] = (desc + f"\n\n(Analyzed using skills template: {template})").strip()
                else:
                    descriptions = [str((j or {}).get("description", "")) for j in (jobs_live or [])]
                    derived = derive_role_skills_from_live_jobs(descriptions)
                    role_info = {
                        "description": "Skills derived from live Adzuna job descriptions for this search.",
                        "required_skills": derived.get("required_skills", []),
                        "optional_skills": derived.get("optional_skills", []),
                    }

                # Persist the resolved info for other tabs
                st.session_state["selected_role_info"] = role_info
                
                st.subheader(f"📋 Role: {selected_role}")
                st.write(f"**Description:** {role_info.get('description', 'N/A')}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**✅ Required Skills:**")
                    required = role_info.get('required_skills', [])
                    for skill in required:
                        st.write(f"• {skill}")
                
                with col2:
                    st.write("**⭐ Optional Skills:**")
                    optional = role_info.get('optional_skills', [])
                    for skill in optional[:10]:
                        st.write(f"• {skill}")
                    if len(optional) > 10:
                        st.write(f"... and {len(optional) - 10} more")
                
                if st.button("✅ Confirm Selection", type="primary"):
                    st.success(f"✅ Role '{selected_role}' selected! Proceed to 'Skill Gaps' tab.")

                # Real-time job market data via API (no demo/offline metrics)
                st.markdown("---")
                st.subheader("🌐 Real-Time Job Market API (Adzuna)")
                
                if job_market and job_market.is_available():
                    # Fetch all available jobs
                    with st.spinner("🔍 Fetching real-time job listings from Adzuna API..."):
                        # Fetch more jobs (best-effort; API may cap results)
                        jobs = job_market.get_jobs_for_role(selected_role, location="India", limit=100)
                        stats = job_market.get_market_statistics(selected_role, location="India")
                    
                    # Store jobs in session state
                    if 'job_listings' not in st.session_state:
                        st.session_state.job_listings = {}
                    st.session_state.job_listings[selected_role] = jobs
                    
                    # Display total jobs count prominently
                    total_jobs = stats.get('total_jobs', len(jobs)) if stats else len(jobs)
                    
                    if total_jobs > 0:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📊 Total Jobs Available", f"{total_jobs:,}", help="Total jobs in India for this role")
                        with col2:
                            st.metric("📋 Jobs Loaded", len(jobs), help="Number of jobs currently displayed")
                        with col3:
                            if total_jobs > len(jobs):
                                st.info(f"💡 Showing {len(jobs)} of {total_jobs} jobs")
                            else:
                                st.success("✅ All jobs loaded")
                    
                    if jobs:
                        st.markdown("---")
                        st.write("**🔍 Select a Job to View Details:**")
                        
                        # Create dropdown with all jobs
                        job_options = [
                            f"{i+1}. {job['title']} at {job['company']} - {job['location']}"
                            for i, job in enumerate(jobs)
                        ]
                        
                        selected_job_index = st.selectbox(
                            "Choose a job listing:",
                            range(len(job_options)),
                            format_func=lambda x: job_options[x],
                            key=f"job_select_{selected_role}",
                            help="Select a job to view full details"
                        )
                        
                        # Display selected job details
                        if selected_job_index is not None and selected_job_index < len(jobs):
                            selected_job = jobs[selected_job_index]
                            
                            st.markdown("---")
                            st.subheader(f"📋 Job Details: {selected_job['title']}")
                            
                            # Job information in columns
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(f"""
                                **🏢 Company:** {selected_job['company']}  
                                **📍 Location:** {selected_job['location']}  
                                **📂 Category:** {selected_job.get('category', 'N/A')}  
                                **📋 Contract Type:** {selected_job.get('contract_type', 'N/A')}
                                """)
                            
                            with col2:
                                if selected_job.get('salary_min') or selected_job.get('salary_max'):
                                    salary_str = ""
                                    if selected_job.get('salary_min'):
                                        salary_str += f"₹{selected_job['salary_min']:,}"
                                    if selected_job.get('salary_max'):
                                        if salary_str:
                                            salary_str += " - "
                                        salary_str += f"₹{selected_job['salary_max']:,}"
                                    st.markdown(f"**💰 Salary:** {salary_str}")
                                
                                if selected_job.get('created'):
                                    st.markdown(f"**📅 Posted:** {selected_job['created']}")
                            
                            # Full description
                            st.markdown("**📝 Job Description:**")
                            st.write(selected_job['description'])
                            
                            # Apply button
                            if selected_job.get('url'):
                                st.markdown("---")
                                st.markdown(f"""
                                <div style="text-align: center; padding: 20px;">
                                    <a href="{selected_job['url']}" target="_blank" 
                                       style="background-color: #1f77b4; color: white; padding: 12px 30px; 
                                              text-decoration: none; border-radius: 5px; font-weight: bold; 
                                              display: inline-block;">
                                        🔗 Apply for This Job →
                                    </a>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Job navigation info
                            st.markdown("---")
                            st.caption(f"📋 Job {selected_job_index + 1} of {len(jobs)} - Use the dropdown above to navigate between jobs")
                        else:
                            st.info("Select a job from the dropdown above to view details")
                    else:
                        st.info("No jobs found. The market may be competitive or try different keywords.")
                else:
                    st.warning("⚠️ Real-time job data not available")
                    st.info("💡 To enable real-time job listings from India:")
                    with st.expander("📝 Setup Instructions"):
                        st.write("""
                        **1. Get Adzuna API Keys:**
                           - Visit: https://developer.adzuna.com/
                           - Sign up for free account
                           - Get App ID and API Key
                        
                        **2. Create .env file:**
                           - Create `.env` file in project root
                           - Add your keys:
                           ```
                           ADZUNA_APP_ID=your_app_id
                           ADZUNA_API_KEY=your_api_key
                           ```
                        
                        **3. Restart the app**
                        
                        **Free Tier:** 10,000 requests/month
                        """)
    
    # Tab 3: Skill Gap Analysis
    with tab3:
        st.markdown('<div class="sub-header">📊 Skill Gap Analysis</div>', unsafe_allow_html=True)
        
        if not has_resume or not has_role:
            st.warning("⚠️ Please upload resume and select a target role first!")
        else:
            resume_data = st.session_state.resume_data
            selected_role = st.session_state.selected_role
            role_info = get_active_role_info(selected_role, job_roles, curated_role_names)
            
            resume_skills = resume_data.get('skills', [])
            required_skills = role_info.get('required_skills', [])
            optional_skills = role_info.get('optional_skills', [])
            all_job_skills = required_skills + optional_skills
            
            if not resume_skills:
                st.error("No skills found in resume. Please check your resume format.")
            else:
                if st.button("🔍 Analyze Skill Gaps", type="primary"):
                    with st.spinner("Analyzing skill gaps using TF-IDF + Cosine Similarity..."):
                        analyzer = SkillGapAnalyzerTFIDF(similarity_threshold=0.3)
                        gap_results = analyzer.analyze_gaps(
                            resume_skills=resume_skills,
                            job_role_skills=all_job_skills,
                            required_skills=required_skills,
                            preferred_skills=optional_skills
                        )
                        st.session_state.analysis_results['skill_gaps'] = gap_results
                    st.rerun()
                
                if has_gaps:
                    gap_results = st.session_state.analysis_results['skill_gaps']
                    
                    # Display results
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("✅ Matched Skills", len(gap_results['matched_skills']))
                    with col2:
                        st.metric("❌ Missing Required", len(gap_results['missing_required']))
                    with col3:
                        st.metric("⚠️ Missing Preferred", len(gap_results['missing_preferred']))
                    
                    # Matched skills
                    st.subheader("✅ Matched Skills")
                    if gap_results['matched_skills']:
                        for match in gap_results['matched_skills']:
                            similarity = match['similarity']
                            st.write(
                                f"• <span class='skill-match'>{match['resume_skill']}</span> "
                                f"↔ {match['job_skill']} (similarity: {similarity:.2f})",
                                unsafe_allow_html=True
                            )
                    else:
                        st.info("No skills matched above threshold")
                    
                    # Missing required skills
                    st.subheader("❌ Missing Required Skills")
                    if gap_results['missing_required']:
                        for skill in gap_results['missing_required']:
                            st.write(f"• <span class='skill-missing'>{skill}</span>", unsafe_allow_html=True)
                        
                        # Show explanations
                        explanations = gap_results.get('explanations', {})
                        with st.expander("ℹ️ Why these skills are missing"):
                            for skill in gap_results['missing_required']:
                                if skill in explanations:
                                    st.write(f"**{skill}:** {explanations[skill]}")
                    else:
                        st.success("🎉 All required skills are present!")
                    
                    # Missing preferred skills
                    if gap_results['missing_preferred']:
                        st.subheader("⚠️ Missing Preferred Skills")
                        for skill in gap_results['missing_preferred'][:10]:
                            st.write(f"• {skill}")
                        if len(gap_results['missing_preferred']) > 10:
                            st.write(f"... and {len(gap_results['missing_preferred']) - 10} more")
    
    # Tab 4: Readiness Score
    with tab4:
        st.markdown('<div class="sub-header">⭐ Job Readiness Score</div>', unsafe_allow_html=True)
        
        if not has_gaps:
            st.warning("⚠️ Please complete skill gap analysis first!")
        else:
            resume_data = st.session_state.resume_data
            gap_results = st.session_state.analysis_results['skill_gaps']
            
            # Get experience and projects
            col1, col2 = st.columns(2)
            with col1:
                experience_years = st.number_input(
                    "Years of Experience",
                    min_value=0.0,
                    max_value=20.0,
                    value=0.0,
                    step=0.5,
                    help="Enter your years of relevant work experience"
                )
            
            with col2:
                projects = resume_data.get('projects', [])
                if not projects:
                    projects_input = st.text_area(
                        "Projects (one per line)",
                        help="List your projects, one per line",
                        height=100
                    )
                    projects = [p.strip() for p in projects_input.split('\n') if p.strip()]
                else:
                    st.info(f"Found {len(projects)} projects from resume")
            
            if st.button("📊 Calculate Readiness Score", type="primary"):
                with st.spinner("Calculating readiness score..."):
                    scorer = JobReadinessScorer()
                    score_results = scorer.calculate_score(
                        skill_gap_results=gap_results,
                        experience_years=experience_years,
                        projects=projects,
                        job_required_experience=2.0
                    )
                    st.session_state.analysis_results['readiness_score'] = score_results
                st.rerun()
            
            if has_score:
                score_results = st.session_state.analysis_results['readiness_score']
                overall_score = score_results['overall_score']
                breakdown = score_results['breakdown']
                
                # Display score
                st.markdown(f"""
                <div class="score-box">
                    <h2 style="text-align: center; color: #1f77b4; font-size: 2.5rem;">Overall Score: {overall_score:.1f}/100</h2>
                </div>
                """, unsafe_allow_html=True)
                
                # Score breakdown
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Skills", f"{breakdown['skills']:.1f}/100", 
                             delta=f"{breakdown['skills'] * 0.60:.1f} pts")
                with col2:
                    st.metric("Experience", f"{breakdown['experience']:.1f}/100",
                             delta=f"{breakdown['experience'] * 0.25:.1f} pts")
                with col3:
                    st.metric("Projects", f"{breakdown['projects']:.1f}/100",
                             delta=f"{breakdown['projects'] * 0.15:.1f} pts")
                
                # Detailed explanation
                with st.expander("📝 Detailed Score Explanation"):
                    st.text(score_results['explanation'])
                
                # Calculation steps
                with st.expander("🔢 Calculation Steps"):
                    calc = score_results['calculation_steps']
                    st.json(calc)
    
    # Tab 5: Role Suitability
    with tab5:
        st.markdown('<div class="sub-header">🔍 Role Suitability Analysis</div>', unsafe_allow_html=True)
        
        # Show job market overview
        if job_market and job_market.is_available() and has_role:
            st.info("💼 Real-time job market data available for India")
            selected_role = st.session_state.get('selected_role')
            if selected_role:
                stats = job_market.get_market_statistics(selected_role, location="India")
                if stats.get('total_jobs', 0) > 0:
                    st.metric("Total Jobs in India", stats.get('total_jobs', 0))
        
        if not has_resume:
            st.warning("⚠️ Please upload resume first!")
        else:
            if st.button("🔍 Analyze All Roles", type="primary"):
                with st.spinner("Analyzing role suitability..."):
                    readiness_scores = {}
                    skill_gaps_all = {}
                    
                    resume_data = st.session_state.resume_data
                    resume_skills = resume_data.get('skills', [])
                    
                    for role_name, role_info in job_roles.items():
                        required = role_info.get('required_skills', [])
                        optional = role_info.get('optional_skills', [])
                        all_skills = required + optional
                        
                        # Skill gap analysis
                        analyzer = SkillGapAnalyzerTFIDF()
                        gap_results = analyzer.analyze_gaps(
                            resume_skills=resume_skills,
                            job_role_skills=all_skills,
                            required_skills=required,
                            preferred_skills=optional
                        )
                        skill_gaps_all[role_name] = gap_results
                        
                        # Readiness score
                        scorer = JobReadinessScorer()
                        score_results = scorer.calculate_score(
                            skill_gap_results=gap_results,
                            experience_years=2.0,
                            projects=resume_data.get('projects', []),
                            job_required_experience=2.0
                        )
                        readiness_scores[role_name] = score_results['overall_score']
                    
                    # Predict suitability
                    predictor = RoleSuitabilityPredictor()
                    suitability_results = predictor.predict_suitability(
                        readiness_scores=readiness_scores,
                        skill_gaps=skill_gaps_all,
                        role_descriptions={name: info.get('description', '') for name, info in job_roles.items()}
                    )
                    
                    st.session_state.analysis_results['suitability'] = suitability_results
                st.rerun()
            
            if has_suitability:
                suitability_results = st.session_state.analysis_results['suitability']
                
                # Display best fit roles
                st.subheader("✅ Best Fit Roles")
                best_fit = suitability_results['best_fit_roles']
                
                if best_fit:
                    for i, role in enumerate(best_fit, 1):
                        with st.expander(f"{i}. {role['role_name']} - Score: {role['readiness_score']:.1f}/100"):
                            st.write(f"**Readiness Score:** {role['readiness_score']:.1f}/100")
                            st.write("**Why this role fits:**")
                            for reason in role['reasons']:
                                st.write(f"• {reason}")
                            if role['description']:
                                st.write(f"**Description:** {role['description']}")
                else:
                    st.info("No roles meet the suitability threshold")
                
                # Not suitable roles
                st.subheader("❌ Not Recommended Roles")
                not_suitable = suitability_results['not_suitable_roles']
                
                if not_suitable:
                    for role in not_suitable:
                        with st.expander(f"{role['role_name']} - Score: {role['readiness_score']:.1f}/100"):
                            st.write(f"**Readiness Score:** {role['readiness_score']:.1f}/100")
                            st.write("**Why not recommended:**")
                            for reason in role['reasons']:
                                st.write(f"• {reason}")
                else:
                    st.success("All analyzed roles are suitable!")
                
                # Recommendations
                st.subheader("💡 Recommendations")
                for rec in suitability_results['recommendations']:
                    st.info(rec)
    
    # Tab 6: Learning Roadmap
    with tab6:
        st.markdown('<div class="sub-header">🗺️ Personalized Learning Roadmap</div>', unsafe_allow_html=True)
        
        if not has_gaps or not has_role:
            st.warning("⚠️ Please complete skill gap analysis and select a target role!")
        else:
            gap_results = st.session_state.analysis_results['skill_gaps']
            selected_role = st.session_state.selected_role
            role_info = get_active_role_info(selected_role, job_roles, curated_role_names)
            
            missing_skills = gap_results.get('missing_required', []) + gap_results.get('missing_preferred', [])
            
            if not missing_skills:
                st.success("🎉 No missing skills! You're ready for this role!")
            else:
                roadmap_weeks = st.slider(
                    "Roadmap Duration (weeks)",
                    min_value=4,
                    max_value=12,
                    value=12,
                    step=1,
                    help="12 weeks ≈ 3 months (week-wise plan)"
                )
                
                if st.button("🗺️ Generate Learning Roadmap", type="primary"):
                    with st.spinner("Generating personalized roadmap..."):
                        generator = PersonalizedRoadmapGenerator(roadmap_days=int(roadmap_weeks) * 7)
                        roadmap = generator.generate_roadmap(
                            missing_skills=missing_skills,
                            target_role=selected_role,
                            required_skills=role_info.get('required_skills', [])
                        )
                        st.session_state.analysis_results['roadmap'] = roadmap
                    st.rerun()
                
                if has_roadmap:
                    roadmap = st.session_state.analysis_results['roadmap']
                    
                    # Display roadmap summary
                    st.subheader("📋 Roadmap Summary")
                    st.text(roadmap['summary'])
                    
                    # Skill-wise plans
                    st.subheader("📚 Skill-wise Learning Plans")
                    
                    for plan in roadmap['skill_plans']:
                        # Backward-compatible: older cached roadmaps may not have week fields
                        weeks = plan.get('weeks')
                        if isinstance(weeks, int) and weeks > 0:
                            header = f"{plan['skill']} ({weeks} weeks, Weeks {plan.get('start_week', 0)}-{plan.get('end_week', 0)})"
                        else:
                            header = f"{plan['skill']}"

                        with st.expander(header):
                            st.write("**Tools:**")
                            for tool in plan.get('tools', []):
                                st.write(f"• {tool}")

                            st.write("**Week-wise plan:**")
                            weekly_plan = plan.get('weekly_plan')
                            if isinstance(weekly_plan, list) and weekly_plan:
                                for w in weekly_plan:
                                    if not isinstance(w, dict):
                                        continue
                                    st.markdown(f"**Week {w.get('week', '')}: {w.get('focus', '')}**")
                                    deliverable = w.get('deliverable')
                                    if deliverable:
                                        st.write(f"Deliverable: {deliverable}")
                                    for t in w.get('tasks', []):
                                        st.write(f"• {t}")
                            else:
                                # Older roadmap format: day-based tasks
                                tasks = plan.get('tasks', [])
                                if tasks:
                                    st.info("Roadmap format updated. Regenerate to see week-wise plan.")
                                    for task in tasks:
                                        if isinstance(task, dict):
                                            st.write(f"• Day {task.get('day', '')}: {task.get('task', '')} ({task.get('type', '')})")
                                        else:
                                            st.write(f"• {task}")
                                else:
                                    st.write("No plan details available. Please regenerate the roadmap.")

                            st.write("**Clickable learning resources:**")
                            for r in plan.get('resources', []):
                                # Backward-compatible: older roadmaps used plain strings
                                if isinstance(r, dict):
                                    title = r.get('title', 'Resource')
                                    url = r.get('url', '')
                                    platform = r.get('platform', '')
                                    if url:
                                        st.markdown(f"- [{platform}: {title}]({url})")
                                    else:
                                        st.write(f"- {platform}: {title}")
                                else:
                                    st.write(f"• {r}")
                    
                    # No day-by-day timeline (week-wise is the source of truth)
                    
                    # Download roadmap
                    roadmap_json = json.dumps(roadmap, indent=2, default=str)
                    st.download_button(
                        label="📥 Download Roadmap (JSON)",
                        data=roadmap_json,
                        file_name=f"roadmap_{selected_role}_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )

    # Tab 7: Interview & Practice AI
    with tab7:
        st.markdown('<div class="sub-header">🧠 Interview & Practice AI (Advanced)</div>', unsafe_allow_html=True)

        # Ensure we have gaps to drive skill-based prep
        gap_results = st.session_state.get('analysis_results', {}).get('skill_gaps', {})
        missing_skills = gap_results.get('missing_required', []) + gap_results.get('missing_preferred', [])

        role_label = st.session_state.get('selected_role') or "Data Scientist"

        if 'interview_state' not in st.session_state:
            st.session_state.interview_state = {
                "started": False,
                "role": role_label,
                "current_question": "",
                "history": [],
            }

        provider_options = ["Gemini", "SambaNova", "OpenAI"]
        default_provider = _default_ai_provider()
        default_index = provider_options.index(default_provider) if default_provider in provider_options else 0
        ai_provider = st.selectbox(
            "AI Provider",
            options=provider_options,
            index=default_index,
            help="Uses provider API keys from env/secrets (no keys are stored in code)",
        )

        # Show configuration status (no secrets displayed)
        cfg = {
            "Gemini": _has_config_value("GOOGLE_GEMINI_API_KEY"),
            "SambaNova": _has_config_value("SAMBANOVA_API_KEY"),
            "OpenAI": _has_config_value("OPENAI_API_KEY"),
        }
        if not cfg.get(ai_provider, False):
            st.warning(
                f"{ai_provider} is not configured. Add the required API key in Streamlit Secrets or as an environment variable."
            )

        st.write("**Step 6.1 – AI Interview Simulator**")
        st.caption("Mock interview chatbot: live questions + feedback on your answers.")

        col_a, col_b = st.columns([1, 2])
        with col_a:
            if st.button("▶️ Start / Restart Interview"):
                try:
                    first_q = start_interview(role=role_label, provider=ai_provider)
                    st.session_state.interview_state = {
                        "started": True,
                        "role": role_label,
                        "provider": ai_provider,
                        "current_question": first_q,
                        "history": [
                            {"role": "assistant", "content": first_q},
                        ],
                    }
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

        with col_b:
            st.text_input("Interview role", value=role_label, disabled=True)

        state = st.session_state.interview_state
        # Keep provider in sync with the selector
        state["provider"] = ai_provider
        if state.get("started") and state.get("history"):
            for msg in state["history"]:
                if msg.get("role") == "user":
                    st.chat_message("user").write(msg.get("content", ""))
                else:
                    st.chat_message("assistant").write(msg.get("content", ""))

            user_answer = st.chat_input("Type your answer and press Enter")
            if user_answer:
                state["history"].append({"role": "user", "content": user_answer})
                try:
                    result = interview_turn(
                        role=state.get("role", role_label),
                        question=state.get("current_question", ""),
                        answer=user_answer,
                        missing_skills=missing_skills if missing_skills else None,
                        provider=state.get("provider", ai_provider),
                    )
                    feedback = result.get("feedback", "").strip()
                    next_q = result.get("next_question", "").strip()

                    if feedback:
                        state["history"].append({"role": "assistant", "content": f"Feedback:\n{feedback}"})
                    if next_q:
                        state["current_question"] = next_q
                        state["history"].append({"role": "assistant", "content": next_q})

                    st.session_state.interview_state = state
                    st.rerun()
                except Exception as e:
                    msg = str(e)
                    if "insufficient_quota" in msg or ("429" in msg and "quota" in msg.lower()):
                        st.error(
                            "OpenAI quota/billing is exceeded for this API key. "
                            "Switch provider to Gemini or SambaNova, or enable billing in your OpenAI account."
                        )
                    else:
                        st.error(msg)
        else:
            st.info(
                "Click 'Start / Restart Interview' to begin. "
                "To enable AI, set OPENAI_API_KEY (OpenAI) or GOOGLE_GEMINI_API_KEY (Gemini) "
                "as an environment variable or add it in Streamlit Secrets."
            )

        st.divider()
        st.write("**Step 6.2 – Skill-Based Question Generator**")
        st.caption("Generates questions only from your missing skills for targeted preparation.")

        if not missing_skills:
            st.info("Complete Skill Gaps first to generate skill-based questions.")
        else:
            st.write(f"Missing skills detected: {', '.join(missing_skills[:10])}{'...' if len(missing_skills) > 10 else ''}")
            qps = st.slider("Questions per skill", min_value=1, max_value=5, value=3, step=1)
            if st.button("🧩 Generate Skill-Based Questions"):
                try:
                    questions_by_skill = generate_skill_questions(
                        role=role_label,
                        missing_skills=missing_skills,
                        questions_per_skill=int(qps),
                        provider=ai_provider,
                    )
                    st.session_state.analysis_results['skill_questions'] = questions_by_skill
                except Exception as e:
                    st.error(str(e))

            questions_by_skill = st.session_state.analysis_results.get('skill_questions')
            if questions_by_skill:
                for skill, qs in questions_by_skill.items():
                    st.markdown(f"**{skill}**")
                    for q in qs:
                        st.write(f"• {q}")


if __name__ == "__main__":
    main()
