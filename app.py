"""
AI Career Intelligence & Skill Gap Analyzer - Streamlit Web App

A clean, simple, college-presentation ready web interface for career analysis.
"""

import streamlit as st
import sys
from pathlib import Path
import json
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.pdf_resume_parser import PDFResumeParser
from src.core.skill_gap_analyzer_tfidf import SkillGapAnalyzerTFIDF
from src.core.job_readiness_scorer import JobReadinessScorer
from src.matcher.role_suitability_predictor import RoleSuitabilityPredictor
from src.roadmap.personalized_roadmap_generator import PersonalizedRoadmapGenerator
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


def load_job_roles():
    """Load job roles from skill mapping."""
    try:
        with open("data/job_roles/skill_mapping.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("job_roles", {})
    except Exception as e:
        st.error(f"Error loading job roles: {e}")
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
    
    completion_status = [has_resume, has_role, has_gaps, has_score, has_suitability, has_roadmap]
    completed_count = sum(completion_status)
    progress_pct = (completed_count / 6) * 100
    
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
        </div>
        <div style="display: flex; justify-content: space-around; margin-top: 10px; font-size: 0.85rem;">
            <span>Resume</span>
            <span>Role</span>
            <span>Gaps</span>
            <span>Score</span>
            <span>Suitability</span>
            <span>Roadmap</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📄 Resume Upload",
        "🎯 Select Role", 
        "📊 Skill Gaps",
        "⭐ Readiness Score",
        "🔍 Role Suitability",
        "🗺️ Learning Roadmap"
    ])
    
    # Load job roles
    job_roles = load_job_roles()
    role_names = list(job_roles.keys()) if job_roles else []
    
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
                
                st.success("✅ Resume parsed successfully! Scroll down to view your complete resume profile.")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Error parsing resume: {e}")
                st.info("💡 **Troubleshooting:** Please ensure your PDF contains text (not just images). Try converting your resume to a text-based PDF.")
        
        # Display comprehensive resume information
        if has_resume:
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
            
            selected_role = st.selectbox(
                "Choose a job role:",
                role_names,
                help="Select the job role you're interested in",
                key="role_selectbox"
            )
            
            st.session_state.selected_role = selected_role
            
            if selected_role:
                role_info = job_roles[selected_role]
                
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
                
                # Show real-time job market data
                st.markdown("---")
                st.subheader("📊 Real-Time Job Market (India)")
                
                if job_market and job_market.is_available():
                    # Fetch all available jobs
                    with st.spinner("🔍 Fetching real-time job listings from India..."):
                        # Fetch more jobs (up to 50 - API limit)
                        jobs = job_market.get_jobs_for_role(selected_role, location="India", limit=50)
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
            role_info = job_roles[selected_role]
            
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
            role_info = job_roles[selected_role]
            
            missing_skills = gap_results.get('missing_required', []) + gap_results.get('missing_preferred', [])
            
            if not missing_skills:
                st.success("🎉 No missing skills! You're ready for this role!")
            else:
                roadmap_days = st.slider(
                    "Roadmap Duration (days)",
                    min_value=7,
                    max_value=60,
                    value=30,
                    step=7
                )
                
                if st.button("🗺️ Generate Learning Roadmap", type="primary"):
                    with st.spinner("Generating personalized roadmap..."):
                        generator = PersonalizedRoadmapGenerator(roadmap_days=roadmap_days)
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
                        with st.expander(f"{plan['skill']} ({plan['days']} days, Days {plan['start_day']}-{plan['end_day']})"):
                            st.write("**Tasks:**")
                            for task in plan['tasks']:
                                st.write(f"Day {task['day']}: {task['task']} ({task['type']})")
                            
                            st.write("**Resources:**")
                            for resource in plan['resources']:
                                st.write(f"• {resource}")
                    
                    # Timeline view
                    st.subheader("📅 Day-by-Day Timeline")
                    timeline = roadmap['timeline']
                    
                    # Group by day
                    days_dict = {}
                    for item in timeline:
                        day = item['day']
                        if day not in days_dict:
                            days_dict[day] = []
                        days_dict[day].append(item)
                    
                    for day in sorted(days_dict.keys()):
                        st.write(f"**Day {day}:**")
                        for item in days_dict[day]:
                            st.write(f"  • {item['task']} ({item['skill']})")
                    
                    # Download roadmap
                    roadmap_json = json.dumps(roadmap, indent=2, default=str)
                    st.download_button(
                        label="📥 Download Roadmap (JSON)",
                        data=roadmap_json,
                        file_name=f"roadmap_{selected_role}_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )


if __name__ == "__main__":
    main()
