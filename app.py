"""
AI Career Intelligence & Skill Gap Analyzer - Streamlit Web App

A clean, simple, college-presentation ready web interface for career analysis.
"""

import os
import sys
import json
import time
import yaml
import difflib
import html
from pathlib import Path
from datetime import datetime

import streamlit as st

# Local dev convenience: load environment variables from .env (ignored by git)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


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

from src.core.pdf_resume_parser import PDFResumeParser
from src.core.skill_gap_analyzer_tfidf import SkillGapAnalyzerTFIDF
from src.core.job_readiness_scorer import JobReadinessScorer
from src.core.skill_extractor import SkillExtractor
from src.matcher.role_suitability_predictor import RoleSuitabilityPredictor
from src.roadmap.personalized_roadmap_generator import PersonalizedRoadmapGenerator
from src.api.interview_ai import start_interview, interview_turn, generate_skill_questions
from src.api.job_market_analyzer import JobMarketAnalyzer

# Tracking & History
try:
    from src.utils.tracking_ui import render_tracking_tab
    _TRACKING_OK = True
except Exception as _tracking_err:
    _TRACKING_OK  = False
    _TRACKING_ERR = str(_tracking_err)

# Page configuration
st.set_page_config(
    page_title="AI Career Intelligence Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Global CSS (Figma / Spline Design System) ───────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ═══════════════════════════════════════════════════
   DESIGN TOKENS
═══════════════════════════════════════════════════ */
:root {
  --bg:           #07090f;
  --surface:      rgba(255,255,255,0.03);
  --surface-hi:   rgba(255,255,255,0.06);
  --border:       rgba(255,255,255,0.07);
  --border-hi:    rgba(255,255,255,0.14);
  --primary:      #6366f1;
  --primary-glow: rgba(99,102,241,0.35);
  --accent:       #06b6d4;
  --accent-glow:  rgba(6,182,212,0.30);
  --success:      #10b981;
  --success-glow: rgba(16,185,129,0.30);
  --warning:      #f59e0b;
  --danger:       #ef4444;
  --text-primary: #f1f5f9;
  --text-secondary:#94a3b8;
  --text-muted:   #475569;
}

/* ═══════════════════════════════════════════════════
   BASE / RESET
═══════════════════════════════════════════════════ */
* { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
[data-testid="stHeader"]         { background: transparent !important; }
[data-testid="stToolbar"]        { display: none !important; }
[data-testid="stDecoration"]     { display: none !important; }
#MainMenu                        { display: none !important; }
footer                           { display: none !important; }
[data-testid="stAppViewContainer"] { background: var(--bg) !important; }

/* ── Animated gradient-mesh background ── */
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed; inset: 0; z-index: -1; pointer-events: none;
    background:
        radial-gradient(ellipse 900px 600px at 10% 20%,  rgba(99,102,241,0.12) 0%, transparent 70%),
        radial-gradient(ellipse 700px 500px at 85% 10%,  rgba(6,182,212,0.09)  0%, transparent 65%),
        radial-gradient(ellipse 600px 700px at 50% 85%,  rgba(16,185,129,0.07) 0%, transparent 60%),
        var(--bg);
}

/* ═══════════════════════════════════════════════════
   TYPOGRAPHY
═══════════════════════════════════════════════════ */
.stMarkdown p, .stMarkdown li, .stMarkdown span { color: var(--text-secondary) !important; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: var(--text-primary) !important; }

/* ═══════════════════════════════════════════════════
   APP HERO HEADER
═══════════════════════════════════════════════════ */
.main-header {
    position: relative; overflow: hidden;
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    border: 1px solid var(--border-hi);
    border-radius: 20px;
    padding: 36px 40px 28px;
    text-align: center;
    margin-bottom: 24px;
    box-shadow: 0 0 0 1px rgba(99,102,241,0.1), 0 24px 64px rgba(0,0,0,0.6);
}
.main-header::before {
    content: "";
    position: absolute; inset: 0; pointer-events: none;
    background:
        radial-gradient(ellipse 500px 300px at 15% 50%, rgba(99,102,241,0.25) 0%, transparent 60%),
        radial-gradient(ellipse 400px 200px at 85% 30%, rgba(6,182,212,0.15)  0%, transparent 60%);
}
.main-header h1 {
    position: relative; z-index: 1;
    margin: 0; font-size: 2.35rem; font-weight: 900;
    letter-spacing: -1px; line-height: 1.15;
    background: linear-gradient(135deg, #fff 30%, #a5b4fc 70%, #67e8f9 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.main-header h1 .hdr-icon {
    display: inline-block;
    -webkit-text-fill-color: initial;
    background: none; -webkit-background-clip: unset; background-clip: unset;
    filter: drop-shadow(0 0 10px rgba(255,255,255,0.55));
    margin-right: 6px;
}
.main-header .subtitle {
    position: relative; z-index: 1;
    color: rgba(255,255,255,0.45); font-size: 0.9rem;
    margin-top: 8px; letter-spacing: 0.4px;
}
.main-header .hero-chips {
    position: relative; z-index: 1;
    display: flex; gap: 8px; justify-content: center;
    flex-wrap: wrap; margin-top: 14px;
}
.hero-chip {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.12);
    color: rgba(255,255,255,0.7);
    padding: 4px 14px; border-radius: 99px; font-size: 0.78rem;
    backdrop-filter: blur(8px);
}

/* ═══════════════════════════════════════════════════
   PROGRESS TRACKER (Spline-style nodes)
═══════════════════════════════════════════════════ */
.nav-card {
    background: rgba(255,255,255,0.025);
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
    border: 1px solid var(--border-hi);
    border-radius: 18px;
    padding: 22px 32px 20px;
    margin-bottom: 24px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.06);
}
.pt-top {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 14px;
}
.pt-title {
    font-size: 0.8rem; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: var(--text-muted);
}
.pt-count {
    font-size: 0.85rem; font-weight: 700;
    color: var(--primary); background: rgba(99,102,241,0.12);
    padding: 3px 12px; border-radius: 99px;
    border: 1px solid rgba(99,102,241,0.25);
}
.pt-bar-wrap {
    height: 4px; border-radius: 99px;
    background: rgba(255,255,255,0.08);
    overflow: visible; margin-bottom: 20px;
    position: relative;
}
.pt-bar-fill {
    height: 100%; border-radius: 99px;
    background: linear-gradient(90deg, var(--primary), var(--accent));
    box-shadow: 0 0 12px var(--primary-glow);
    transition: width 0.6s cubic-bezier(0.34,1.56,0.64,1);
    position: relative;
}
.pt-bar-fill::after {
    content: "";
    position: absolute; right: -5px; top: -4px;
    width: 12px; height: 12px; border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 14px var(--accent-glow);
}
.pt-steps {
    display: flex; justify-content: space-between;
    align-items: flex-start; position: relative;
}
.pt-steps::before {
    content: ""; position: absolute;
    top: 19px; left: 5%; right: 5%; height: 2px;
    background: rgba(255,255,255,0.06); z-index: 0;
}
.pt-step {
    display: flex; flex-direction: column;
    align-items: center; flex: 1;
    position: relative; z-index: 1; cursor: default;
}
.pt-circle {
    width: 40px; height: 40px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.8rem; font-weight: 700;
    transition: all 0.35s cubic-bezier(0.34,1.56,0.64,1);
    position: relative;
}
/* Done state */
.pt-done .pt-circle {
    background: linear-gradient(135deg, #059669, #10b981);
    border: 2px solid rgba(16,185,129,0.5);
    color: white;
    box-shadow: 0 0 16px var(--success-glow), 0 4px 12px rgba(0,0,0,0.3);
}
.pt-done .pt-circle::after {
    content: "✓"; position: absolute; font-size: 1rem; font-weight: 800;
}
/* Active/current state */
.pt-active .pt-circle {
    background: linear-gradient(135deg, var(--primary), #818cf8);
    border: 2px solid rgba(165,180,252,0.6);
    color: white;
    box-shadow: 0 0 20px var(--primary-glow), 0 4px 14px rgba(0,0,0,0.4);
    animation: node-pulse 2.5s ease-in-out infinite;
}
@keyframes node-pulse {
    0%,100% { box-shadow: 0 0 20px var(--primary-glow), 0 4px 14px rgba(0,0,0,0.4); transform: scale(1);   }
    50%      { box-shadow: 0 0 32px var(--primary-glow), 0 4px 18px rgba(0,0,0,0.4); transform: scale(1.05); }
}
/* Waiting state */
.pt-wait .pt-circle {
    background: rgba(255,255,255,0.04);
    border: 2px solid rgba(255,255,255,0.1);
    color: rgba(255,255,255,0.25);
}
.pt-label {
    font-size: 0.68rem; margin-top: 7px;
    text-align: center; max-width: 58px; line-height: 1.3;
    color: var(--text-muted); font-weight: 500;
}
.pt-done   .pt-label { color: var(--success); font-weight: 600; }
.pt-active .pt-label { color: #a5b4fc;         font-weight: 700; }

/* ═══════════════════════════════════════════════════
   TABS (Frosted glass pill)
═══════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.035) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    padding: 5px 6px !important;
    gap: 2px !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.05) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    color: var(--text-muted) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.78rem !important; font-weight: 500 !important;
    padding: 7px 14px !important;
    transition: all 0.2s ease !important;
    border: 1px solid transparent !important;
}
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
    color: var(--text-secondary) !important;
    background: rgba(255,255,255,0.05) !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--primary), #818cf8) !important;
    color: white !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 14px var(--primary-glow) !important;
    border-color: rgba(165,180,252,0.3) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"]    { display: none !important; }

/* ═══════════════════════════════════════════════════
   GLASSMORPHISM CARDS
═══════════════════════════════════════════════════ */
.glass-card {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid var(--border-hi);
    border-radius: 16px; padding: 20px 22px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    color: var(--text-secondary);
}
.glass-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.08);
}
.info-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border-hi);
    border-left: 3px solid var(--primary);
    border-radius: 12px; padding: 16px 20px;
    margin: 10px 0;
    box-shadow: 0 2px 12px rgba(0,0,0,0.25);
    color: var(--text-secondary);
}
.score-box {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border-hi);
    border-left: 4px solid var(--primary);
    border-radius: 12px; padding: 1.2rem 1.4rem;
    margin: 1rem 0; color: var(--text-secondary);
    box-shadow: 0 0 0 1px rgba(99,102,241,0.08);
}

/* ═══════════════════════════════════════════════════
   STAT CARDS (Spline-depth tiles)
═══════════════════════════════════════════════════ */
.stat-card {
    position: relative; overflow: hidden;
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border-hi);
    border-radius: 16px; padding: 22px 16px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.05);
    transition: transform 0.3s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.25s ease;
}
.stat-card::before {
    content: ""; position: absolute; inset: 0; pointer-events: none;
    background: radial-gradient(ellipse 120px 80px at 50% -20%, rgba(99,102,241,0.18) 0%, transparent 60%);
}
.stat-card:hover { transform: translateY(-4px) scale(1.02); box-shadow: 0 12px 32px rgba(0,0,0,0.5); }
.stat-card h2 {
    position: relative; z-index: 1;
    font-size: 2.2rem; font-weight: 900; margin: 0;
    background: linear-gradient(135deg, #fff, #a5b4fc);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.stat-card p { position: relative; z-index: 1; margin: 5px 0 0; font-size: 0.78rem; color: var(--text-muted); }

/* ═══════════════════════════════════════════════════
   EXPERIENCE / PROJECT / EDUCATION CARDS
═══════════════════════════════════════════════════ */
.experience-card {
    background: rgba(16,185,129,0.04);
    border: 1px solid rgba(16,185,129,0.15);
    border-left: 3px solid var(--success);
    border-radius: 12px; padding: 14px 18px; margin: 10px 0;
    color: var(--text-secondary);
    transition: border-color 0.2s, background 0.2s;
}
.experience-card:hover { background: rgba(16,185,129,0.07); border-color: rgba(16,185,129,0.3); }
.project-card {
    background: rgba(245,158,11,0.04);
    border: 1px solid rgba(245,158,11,0.15);
    border-left: 3px solid var(--warning);
    border-radius: 12px; padding: 14px 18px; margin: 10px 0;
    color: var(--text-secondary);
    transition: border-color 0.2s, background 0.2s;
}
.project-card:hover { background: rgba(245,158,11,0.07); border-color: rgba(245,158,11,0.3); }
.education-card {
    background: rgba(6,182,212,0.04);
    border: 1px solid rgba(6,182,212,0.15);
    border-left: 3px solid var(--accent);
    border-radius: 12px; padding: 14px 18px; margin: 10px 0;
    color: var(--text-secondary);
    transition: border-color 0.2s, background 0.2s;
}
.education-card:hover { background: rgba(6,182,212,0.07); border-color: rgba(6,182,212,0.3); }
.resume-card {
    background: linear-gradient(135deg, rgba(16,185,129,0.15) 0%, rgba(5,150,105,0.1) 100%);
    border: 1px solid rgba(16,185,129,0.25);
    border-radius: 14px; padding: 20px 24px; margin: 16px 0;
    color: #d1fae5;
    box-shadow: 0 4px 20px rgba(16,185,129,0.15);
}

/* ═══════════════════════════════════════════════════
   SKILL BADGES
═══════════════════════════════════════════════════ */
.skill-badge {
    display: inline-block;
    background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(129,140,248,0.15));
    border: 1px solid rgba(99,102,241,0.3);
    color: #a5b4fc;
    padding: 4px 12px; border-radius: 99px;
    margin: 3px; font-size: 0.78rem; font-weight: 500;
    letter-spacing: 0.3px;
    backdrop-filter: blur(8px);
    transition: all 0.2s ease;
}
.skill-badge:hover { background: rgba(99,102,241,0.3); border-color: rgba(99,102,241,0.5); color: white; }
.skill-match   { color: var(--success) !important; font-weight: 700; }
.skill-missing { color: var(--danger)  !important; font-weight: 700; }

/* ═══════════════════════════════════════════════════
   TAB HERO BANNERS
═══════════════════════════════════════════════════ */
.tab-hero {
    position: relative; overflow: hidden;
    border-radius: 18px;
    padding: 26px 28px 22px;
    margin-bottom: 24px;
    border: 1px solid var(--border-hi);
    box-shadow: 0 4px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.06);
}
.tab-hero::before {
    content: ""; position: absolute; inset: 0; pointer-events: none;
    background: radial-gradient(ellipse 300px 200px at 100% 50%, rgba(255,255,255,0.04) 0%, transparent 60%);
}
.tab-hero-inner {
    display: flex; align-items: flex-start; gap: 16px;
    position: relative; z-index: 1;
}
.tab-hero-icon {
    font-size: 2.4rem; line-height: 1; flex-shrink: 0;
    filter: drop-shadow(0 0 12px rgba(255,255,255,0.25));
}
.tab-hero-text { flex: 1; min-width: 0; }
.tab-hero-text h2 {
    margin: 0 0 4px; font-size: 1.45rem; font-weight: 800;
    letter-spacing: -0.5px; line-height: 1.2;
    color: #fff;
}
.tab-hero-text p {
    margin: 0; font-size: 0.85rem; color: rgba(255,255,255,0.55) !important;
    line-height: 1.5;
}
.tab-hero-badge {
    flex-shrink: 0; align-self: flex-start;
    display: inline-flex; align-items: center; gap: 5px;
    padding: 5px 14px; border-radius: 99px;
    font-size: 0.75rem; font-weight: 700; letter-spacing: 0.3px;
    backdrop-filter: blur(8px);
}
.badge-done    { background: rgba(16,185,129,0.15); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.35); }
.badge-active  { background: rgba(99,102,241,0.18); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.4); }
.badge-waiting { background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.35); border: 1px solid rgba(255,255,255,0.1); }

/* Per-tab accent colours */
.tab-hero-resume   { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); }
.tab-hero-role     { background: linear-gradient(135deg, #0c1a0c 0%, #052e16 100%); }
.tab-hero-gaps     { background: linear-gradient(135deg, #12111e 0%, #1e1240 100%); }
.tab-hero-score    { background: linear-gradient(135deg, #161005 0%, #2d1f06 100%); }
.tab-hero-suit     { background: linear-gradient(135deg, #061020 0%, #0c2340 100%); }
.tab-hero-roadmap  { background: linear-gradient(135deg, #07131a 0%, #0e2732 100%); }
.tab-hero-interview{ background: linear-gradient(135deg, #13061f 0%, #260d40 100%); }
.tab-hero-tracking { background: linear-gradient(135deg, #0e0e1a 0%, #1a1a35 100%); }

/* ── Tab section titles (inside tabs) ── */
.tab-section-title {
    display: flex; align-items: center; gap: 10px;
    font-size: 1rem; font-weight: 700;
    color: var(--text-primary);
    margin: 28px 0 12px; padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
    letter-spacing: -0.2px;
}
.tab-section-title .tst-dot {
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
/* keep .sub-header as fallback alias */
.sub-header { font-size: 1rem; font-weight: 700; color: var(--text-primary);
              margin: 24px 0 12px; padding-bottom: 8px;
              border-bottom: 1px solid var(--border); }

/* ═══════════════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════════════ */
.stButton > button {
    background: linear-gradient(135deg, var(--primary), #818cf8) !important;
    color: white !important; font-weight: 600 !important;
    border: 1px solid rgba(165,180,252,0.3) !important;
    border-radius: 10px !important;
    padding: 0.55rem 1.4rem !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.2px !important;
    box-shadow: 0 4px 14px var(--primary-glow), inset 0 1px 0 rgba(255,255,255,0.15) !important;
    transition: all 0.2s cubic-bezier(0.34,1.56,0.64,1) !important;
}
.stButton > button:hover  { transform: translateY(-2px) scale(1.02) !important; box-shadow: 0 8px 22px var(--primary-glow) !important; }
.stButton > button:active { transform: translateY(0) scale(0.99) !important; }

/* ═══════════════════════════════════════════════════
   UPLOAD AREA
═══════════════════════════════════════════════════ */
.upload-area {
    border: 1.5px dashed rgba(99,102,241,0.4);
    border-radius: 18px;
    padding: 44px 32px;
    text-align: center;
    background: radial-gradient(ellipse 300px 200px at 50% 0%, rgba(99,102,241,0.06) 0%, transparent 60%),
                rgba(255,255,255,0.015);
    backdrop-filter: blur(12px);
    transition: all 0.3s ease;
    color: var(--text-secondary);
    position: relative; overflow: hidden;
}
.upload-area::before {
    content: ""; position: absolute; inset: 0; pointer-events: none;
    background: radial-gradient(ellipse 200px 150px at 50% 50%, rgba(99,102,241,0.05) 0%, transparent 70%);
    transition: opacity 0.3s;
}
.upload-area:hover {
    border-color: rgba(99,102,241,0.7);
    background: rgba(99,102,241,0.06);
    box-shadow: 0 0 30px rgba(99,102,241,0.1);
    transform: scale(1.005);
}

/* ═══════════════════════════════════════════════════
   FORM INPUTS
═══════════════════════════════════════════════════ */
[data-testid="stFileUploader"] label { color: var(--text-secondary) !important; }
[data-testid="stFileUploader"] section {
    background: var(--surface) !important;
    border-color: var(--border-hi) !important;
    border-radius: 12px !important;
}
.stTextInput input {
    background: rgba(255,255,255,0.04) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput input:focus { border-color: rgba(99,102,241,0.5) !important; box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important; }
.stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border-color: var(--border-hi) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
}
.stTextArea textarea {
    background: rgba(255,255,255,0.04) !important;
    border-color: var(--border-hi) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}

/* ═══════════════════════════════════════════════════
   METRICS
═══════════════════════════════════════════════════ */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: 12px !important;
    padding: 14px !important;
}
[data-testid="stMetricValue"] { color: #a5b4fc !important; font-weight: 800 !important; }
[data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size: 0.78rem !important; }

/* ═══════════════════════════════════════════════════
   EXPANDERS / CONTAINERS
═══════════════════════════════════════════════════ */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.025) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary { color: var(--text-secondary) !important; }

/* ═══════════════════════════════════════════════════
   ALERTS
═══════════════════════════════════════════════════ */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border-width: 1px !important;
    font-size: 0.88rem !important;
}

/* ═══════════════════════════════════════════════════
   CHAT MESSAGES (Interview tab)
═══════════════════════════════════════════════════ */
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.025) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
}

/* ═══════════════════════════════════════════════════
   PROGRESS BAR (Streamlit native)
═══════════════════════════════════════════════════ */
[data-testid="stProgress"] > div > div > div {
    background: linear-gradient(90deg, var(--primary), var(--accent)) !important;
    border-radius: 99px !important;
}

/* ═══════════════════════════════════════════════════
   SCANNING ANIMATION
═══════════════════════════════════════════════════ */
.scanning-animation {
    display: inline-block;
    animation: scan 1.8s cubic-bezier(0.4,0,0.6,1) infinite;
}
@keyframes scan {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.25; }
}

/* ═══════════════════════════════════════════════════
   SCROLLBAR
═══════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 6px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.22); }

/* ═══════════════════════════════════════════════════
   DIVIDER
═══════════════════════════════════════════════════ */
hr { border-color: var(--border) !important; margin: 20px 0 !important; }

/* ═══════════════════════════════════════════════════
   SECTION SEPARATOR (decorative)
═══════════════════════════════════════════════════ */
.section-sep {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border-hi), transparent);
    margin: 24px 0;
}

/* ═══════════════════════════════════════════════════
   INTERVIEW TAB EXTRA
═══════════════════════════════════════════════════ */
.interview-header {
    background: linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(6,182,212,0.10) 100%);
    border: 1px solid rgba(99,102,241,0.2);
    color: var(--text-primary); padding: 20px 24px; border-radius: 16px;
    margin-bottom: 18px;
    box-shadow: 0 4px 24px rgba(99,102,241,0.1);
}
.interview-stat {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border-hi);
    border-radius: 12px; padding: 16px 10px; text-align: center;
    transition: transform 0.2s;
}
.interview-stat:hover { transform: translateY(-2px); }
.interview-stat .val { font-size: 1.9rem; font-weight: 800; color: #a5b4fc; }
.interview-stat .lbl { font-size: 0.72rem; color: var(--text-muted); margin-top: 3px; }
.score-chip {
    display: inline-block; padding: 3px 10px; border-radius: 99px;
    font-size: 0.78rem; font-weight: 600; font-family: 'Inter', sans-serif;
}
.score-high  { background: rgba(16,185,129,0.15); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.3); }
.score-mid   { background: rgba(245,158,11,0.15); color: #fcd34d; border: 1px solid rgba(245,158,11,0.3); }
.score-low   { background: rgba(239,68,68,0.15);  color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }
.feedback-card {
    background: rgba(99,102,241,0.06);
    border: 1px solid rgba(99,102,241,0.18);
    border-radius: 12px; padding: 14px 18px; margin: 8px 0;
}
.feedback-card ul { margin: 8px 0 0; padding-left: 18px; }
.feedback-card li { margin-bottom: 5px; font-size: 0.88rem; color: var(--text-secondary); }
.tip-box {
    background: rgba(16,185,129,0.06);
    border: 1px solid rgba(16,185,129,0.2);
    border-radius: 12px; padding: 14px 18px; font-size: 0.88rem; color: #6ee7b7;
}
.skill-q-card {
    background: rgba(245,158,11,0.05);
    border: 1px solid rgba(245,158,11,0.18);
    border-radius: 10px; padding: 12px 16px; margin: 6px 0;
    font-size: 0.88rem; color: var(--text-secondary);
    transition: background 0.2s;
}
.skill-q-card:hover { background: rgba(245,158,11,0.09); }
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
            df = pd.read_csv("data/raw/linkdin_Job_data.csv", usecols=["job"], dtype=str)
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
            df = pd.read_csv("data/raw/LinkedIn_Jobs_Data_India.csv", usecols=["title"], dtype=str)
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
    
    # ── App Header ──────────────────────────────────────────────────────────
    st.markdown("""
    <div class="main-header">
        <h1><span class="hdr-icon">🎯</span> AI Career Intelligence &amp; Skill Gap Analyzer</h1>
        <div class="subtitle">Your personalized AI-powered career co-pilot — from resume to role readiness</div>
        <div class="hero-chips">
            <span class="hero-chip">📄 Resume Parsing</span>
            <span class="hero-chip">📊 Skill Gap Analysis</span>
            <span class="hero-chip">⭐ Readiness Scoring</span>
            <span class="hero-chip">🗺️ Learning Roadmap</span>
            <span class="hero-chip">🧠 AI Mock Interview</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    # ── Progress Tracker ────────────────────────────────────────────────────
    def _step_class(done: bool, active: bool) -> str:
        if done:   return "pt-done"
        if active: return "pt-active"
        return "pt-wait"

    def _step_icon(done: bool, active: bool, num: int) -> str:
        if done:   return "✓"
        if active: return str(num)
        return str(num)

    steps_info = [
        (has_resume,     has_resume or True,           "📄", "Resume"),
        (has_role,       has_resume,                   "🎯", "Role"),
        (has_gaps,       has_role,                     "📊", "Gaps"),
        (has_score,      has_gaps,                     "⭐", "Score"),
        (has_suitability,has_score,                    "🔍", "Suitability"),
        (has_roadmap,    has_suitability,               "🗺️", "Roadmap"),
        (has_interview,  has_roadmap,                   "🧠", "Interview"),
    ]
    # Build step HTML
    steps_html = "".join(
        f'<div class="pt-step {_step_class(done, prev and not done)}">'
        f'  <div class="pt-circle">{_step_icon(done, prev and not done, i+1)}</div>'
        f'  <div class="pt-label">{label}</div>'
        f'</div>'
        for i, (done, prev, icon, label) in enumerate(steps_info)
    )

    st.markdown(f"""
    <div class="nav-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <span style="font-size:1.05rem; font-weight:700; color:rgba(255,255,255,0.9);">📍 Progress Tracker</span>
            <span style="font-size:0.95rem; font-weight:700; color:#79c0ff;">{completed_count} / 7 Steps</span>
        </div>
        <div class="pt-bar-wrap">
            <div class="pt-bar-fill" style="width:{round(progress_pct)}%"></div>
        </div>
        <div class="pt-steps">{steps_html}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📄 Resume Upload",
        "🎯 Select Role",
        "📊 Skill Gaps",
        "⭐ Readiness Score",
        "🔍 Role Suitability",
        "🗺️ Learning Roadmap",
        "🧠 Interview & Practice AI",
        "📈 Tracking & History",
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
        _b1 = "badge-done" if has_resume else "badge-active"
        _t1 = "✅ Resume Loaded" if has_resume else "⬆️ Upload Resume"
        st.markdown(f"""
        <div class="tab-hero tab-hero-resume">
          <div class="tab-hero-inner">
            <div class="tab-hero-icon">📄</div>
            <div class="tab-hero-text">
              <h2>Resume Upload</h2>
              <p>Upload your PDF resume — our AI instantly extracts skills, experience, education &amp; projects and builds your profile.</p>
            </div>
            <span class="tab-hero-badge {_b1}">{_t1}</span>
          </div>
        </div>""", unsafe_allow_html=True)
        
        # Upload section with enhanced UI
        if not has_resume:
            st.markdown("""
            <div class="upload-area">
                <div style="font-size:3rem; margin-bottom:10px">📄</div>
                <h3 style="color:#58a6ff; margin:0 0 8px">🚀 Analyze Your Career Readiness</h3>
                <p style="color:#8b949e; margin:0">Upload your resume PDF &bull; AI extracts skills, experience &amp; education instantly</p>
            </div>
            """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if not has_resume:
                st.caption("Upload your resume PDF — our AI will extract skills, experience, education and projects.")
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
                
                st.caption("✅ Resume parsed — scroll down to view your profile.")
                st.balloons()
                
                # Update has_resume check for immediate display
                has_resume = True
                
            except Exception as e:
                st.error(f"❌ Error parsing resume: {e}")
                st.caption("Tip: make sure the PDF contains selectable text, not just scanned images.")
        
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
                    st.caption("🎉 Excellent resume — well-structured and comprehensive.")
                elif quality_score >= 60:
                    st.caption("Good resume — consider adding more detail to sections.")
                else:
                    st.caption("⚠️ Resume needs more information for a better analysis.")
    
    # Tab 2: Select Target Role
    with tab2:
        _b2 = "badge-done" if has_role else "badge-active"
        _t2 = f"✅ {st.session_state.get('selected_role','Role Selected')}" if has_role else "Step 2 of 7"
        st.markdown(f"""
        <div class="tab-hero tab-hero-role">
          <div class="tab-hero-inner">
            <div class="tab-hero-icon">🎯</div>
            <div class="tab-hero-text">
              <h2>Select Target Role</h2>
              <p>Choose the job role you&apos;re aiming for. We&apos;ll map it to required skills and tailor every analysis on this page to that role.</p>
            </div>
            <span class="tab-hero-badge {_b2}">{_t2}</span>
          </div>
        </div>""", unsafe_allow_html=True)
        
        if not has_resume:
            st.warning("⚠️ Please upload your resume first in the 'Resume Upload' tab!")
        else:
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
                    # Clear previous results so stale counts are never shown
                    st.session_state.pop("realtime_jobs", None)
                    st.session_state.pop("realtime_stats", None)
                    st.session_state.pop("realtime_titles", None)
                    st.session_state.pop("realtime_fetch_ts", None)

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

                    st.session_state["realtime_jobs"]     = jobs_live
                    st.session_state["realtime_stats"]    = stats_live
                    st.session_state["realtime_fetch_ts"] = datetime.now().strftime("%d %b %Y  %H:%M:%S")

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
            jobs_live       = st.session_state.get("realtime_jobs",    []) or []
            stats_live      = st.session_state.get("realtime_stats",   {}) or {}
            fetch_ts        = st.session_state.get("realtime_fetch_ts", None)

            if stats_live and stats_live.get("total_jobs", 0) > 0:
                ts_label = f"  ·  fetched at {fetch_ts}" if fetch_ts else ""
                st.caption(f"Adzuna reports {stats_live.get('total_jobs', 0):,} jobs for this search{ts_label}")

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
                    st.caption(f"Role '{selected_role}' confirmed — proceed to Skill Gaps.")

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
                                st.caption(f"Showing {len(jobs)} of {total_jobs} jobs")
                            else:
                                st.caption("All jobs loaded")
                    
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
                            st.caption("Select a job from the dropdown above to view details.")
                    else:
                        st.caption("No jobs found — market may be competitive or try different keywords.")
                else:
                    st.warning("⚠️ Real-time job data not available")
                    st.caption("To enable real-time job listings from India:")
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
        _b3 = "badge-done" if has_gaps else ("badge-active" if has_role else "badge-waiting")
        _t3 = "✅ Analysis Done" if has_gaps else ("Step 3 of 7" if has_role else "Complete Step 2 first")
        st.markdown(f"""
        <div class="tab-hero tab-hero-gaps">
          <div class="tab-hero-inner">
            <div class="tab-hero-icon">📊</div>
            <div class="tab-hero-text">
              <h2>Skill Gap Analysis</h2>
              <p>See exactly which required &amp; preferred skills you have, which you&apos;re missing, and how your proficiency compares to the role benchmark.</p>
            </div>
            <span class="tab-hero-badge {_b3}">{_t3}</span>
          </div>
        </div>""", unsafe_allow_html=True)
        
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
                        st.caption("No skills matched above threshold.")
                    
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
                        st.caption("🎉 All required skills are present!")
                    
                    # Missing preferred skills
                    if gap_results['missing_preferred']:
                        st.subheader("⚠️ Missing Preferred Skills")
                        for skill in gap_results['missing_preferred'][:10]:
                            st.write(f"• {skill}")
                        if len(gap_results['missing_preferred']) > 10:
                            st.write(f"... and {len(gap_results['missing_preferred']) - 10} more")
    
    # Tab 4: Readiness Score
    with tab4:
        _b4 = "badge-done" if has_score else ("badge-active" if has_gaps else "badge-waiting")
        _t4 = "✅ Score Ready" if has_score else ("Step 4 of 7" if has_gaps else "Complete Step 3 first")
        st.markdown(f"""
        <div class="tab-hero tab-hero-score">
          <div class="tab-hero-inner">
            <div class="tab-hero-icon">⭐</div>
            <div class="tab-hero-text">
              <h2>Job Readiness Score</h2>
              <p>Your overall readiness score (0–100) broken down across skills, experience, education &amp; projects — with actionable coaching tips.</p>
            </div>
            <span class="tab-hero-badge {_b4}">{_t4}</span>
          </div>
        </div>""", unsafe_allow_html=True)
        
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
                    st.caption(f"Found {len(projects)} projects in resume.")
            
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
        _b5 = "badge-done" if has_suitability else ("badge-active" if has_score else "badge-waiting")
        _t5 = "✅ Analysis Done" if has_suitability else ("Step 5 of 7" if has_score else "Complete Step 4 first")
        st.markdown(f"""
        <div class="tab-hero tab-hero-suit">
          <div class="tab-hero-inner">
            <div class="tab-hero-icon">🔍</div>
            <div class="tab-hero-text">
              <h2>Role Suitability Analysis</h2>
              <p>AI-powered prediction of how well your overall profile fits the target role, with a confidence score and a detailed strengths/gaps breakdown.</p>
            </div>
            <span class="tab-hero-badge {_b5}">{_t5}</span>
          </div>
        </div>""", unsafe_allow_html=True)
        
        # Show job market overview – fetch live once per role, cache in session_state
        if job_market and job_market.is_available() and has_role:
            selected_role = st.session_state.get('selected_role')
            if selected_role:
                cache_key    = f"suit_stats_{selected_role}"
                cache_ts_key = f"suit_stats_ts_{selected_role}"

                col_info, col_refresh = st.columns([5, 1])
                with col_refresh:
                    do_refresh = st.button("🔄 Refresh", key="suit_stats_refresh",
                                           help="Re-fetch live job count from Adzuna")

                if do_refresh or cache_key not in st.session_state:
                    with st.spinner("Fetching live job count..."):
                        _stats_fresh = job_market.get_market_statistics(selected_role, location="India")
                    st.session_state[cache_key]    = _stats_fresh
                    st.session_state[cache_ts_key] = datetime.now().strftime("%d %b %Y  %H:%M:%S")

                stats    = st.session_state[cache_key]
                stats_ts = st.session_state.get(cache_ts_key, "")

                with col_info:
                    if stats.get('total_jobs', 0) > 0:
                        st.caption(f"Live job market data — India · last fetched {stats_ts}")
                    else:
                        st.caption("Live job market data available for India.")

                if stats.get('total_jobs', 0) > 0:
                    st.metric("Total Jobs in India", f"{stats.get('total_jobs', 0):,}",
                              help=f"Live count from Adzuna for '{selected_role}' · {stats_ts}")
        
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
                    st.caption("No roles meet the suitability threshold.")
                
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
                    st.caption("All analyzed roles are suitable.")
                
                # Recommendations
                st.subheader("💡 Recommendations")
                for rec in suitability_results['recommendations']:
                    st.caption(rec)
    
    # Tab 6: Learning Roadmap
    with tab6:
        _b6 = "badge-done" if has_roadmap else ("badge-active" if has_suitability else "badge-waiting")
        _t6 = "✅ Roadmap Ready" if has_roadmap else ("Step 6 of 7" if has_suitability else "Complete Step 5 first")
        st.markdown(f"""
        <div class="tab-hero tab-hero-roadmap">
          <div class="tab-hero-inner">
            <div class="tab-hero-icon">🗺️</div>
            <div class="tab-hero-text">
              <h2>Personalized Learning Roadmap</h2>
              <p>A step-by-step skill-building plan tailored to your gaps — with curated resources, timelines, and milestones to get you role-ready.</p>
            </div>
            <span class="tab-hero-badge {_b6}">{_t6}</span>
          </div>
        </div>""", unsafe_allow_html=True)
        
        if not has_gaps or not has_role:
            st.warning("⚠️ Please complete skill gap analysis and select a target role!")
        else:
            gap_results = st.session_state.analysis_results['skill_gaps']
            selected_role = st.session_state.selected_role
            role_info = get_active_role_info(selected_role, job_roles, curated_role_names)
            
            missing_skills = gap_results.get('missing_required', []) + gap_results.get('missing_preferred', [])
            
            if not missing_skills:
                st.caption("🎉 No missing skills — you're ready for this role!")
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
                                    st.caption("Roadmap format updated — regenerate to see week-wise plan.")
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
        _b7 = 'badge-done' if has_interview else ('badge-active' if has_roadmap else 'badge-waiting')
        _t7 = '✅ Interview Done' if has_interview else ('Step 7 of 7' if has_roadmap else 'Complete Step 6 first')
        st.markdown(f"""
        <div class=\"tab-hero tab-hero-interview\">
          <div class=\"tab-hero-inner\">
            <div class=\"tab-hero-icon\">🧠</div>
            <div class=\"tab-hero-text\">
              <h2>Interview &amp; Practice AI</h2>
              <p>AI-powered mock interviews for your target role &mdash; real-time feedback, answer scoring, and a skill-targeted question bank.</p>
            </div>
            <span class=\"tab-hero-badge {_b7}\">{_t7}</span>
          </div>
        </div>""", unsafe_allow_html=True)


        # ── Silently resolve API key ───────────────────────────────────
        def _resolve_interview_provider() -> tuple[str, str]:
            for prov, env_name in [("Gemini","GOOGLE_GEMINI_API_KEY"),("OpenAI","OPENAI_API_KEY"),("SambaNova","SAMBANOVA_API_KEY")]:
                key = os.getenv(env_name, "")
                if not key:
                    try:    key = st.secrets.get(env_name, "") or ""
                    except: key = ""
                if key:
                    return prov, key.strip()
            return "", ""

        _ai_provider, _api_key = _resolve_interview_provider()
        _ai_ready = bool(_api_key)

        gap_results   = st.session_state.get('analysis_results', {}).get('skill_gaps', {})
        missing_skills = gap_results.get('missing_required', []) + gap_results.get('missing_preferred', [])
        role_label     = st.session_state.get('selected_role') or "Data Scientist"

        if 'interview_state' not in st.session_state:
            st.session_state.interview_state = {
                "started": False, "role": role_label,
                "current_question": "", "history": [], "scores": [],
            }

        state = st.session_state.interview_state
        state["provider"] = _ai_provider
        state["api_key"]   = _api_key

        # derive stats
        history   = state.get("history", [])
        q_count   = sum(1 for m in history if m["role"] == "assistant"
                        and not m["content"].startswith("**Feedback"))
        a_count   = sum(1 for m in history if m["role"] == "user")
        scores    = state.get("scores", [])
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0

        # ── Header banner ──────────────────────────────────────────
        st.markdown(f"""
        <div class="interview-header">
            <span style="font-size:2rem">🧠</span>
            <div>
                <h2>AI Interview Simulator</h2>
                <p>Role: <strong>{role_label}</strong> &nbsp;•&nbsp;
                   Questions asked: <strong>{q_count}</strong> &nbsp;•&nbsp;
                   Answers given: <strong>{a_count}</strong>
                   {'&nbsp;&bull;&nbsp; Avg score: <strong>' + str(avg_score) + '/10</strong>' if avg_score else ''}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Stats row (shown after at least 1 turn) ──────────────────────
        if a_count > 0:
            sc1, sc2, sc3, sc4 = st.columns(4)
            with sc1:
                st.markdown(f'<div class="interview-stat"><div class="val">{q_count}</div><div class="lbl">Questions</div></div>', unsafe_allow_html=True)
            with sc2:
                st.markdown(f'<div class="interview-stat"><div class="val">{a_count}</div><div class="lbl">Answers</div></div>', unsafe_allow_html=True)
            with sc3:
                score_color = "#28a745" if avg_score >= 7 else "#ffc107" if avg_score >= 5 else "#dc3545"
                st.markdown(f'<div class="interview-stat"><div class="val" style="color:{score_color}">{avg_score if avg_score else "-"}</div><div class="lbl">Avg Score /10</div></div>', unsafe_allow_html=True)
            with sc4:
                best = max(scores) if scores else 0
                st.markdown(f'<div class="interview-stat"><div class="val" style="color:#7c83fd">{best if best else "-"}</div><div class="lbl">Best Score /10</div></div>', unsafe_allow_html=True)
            st.write("")

        # ── Controls row ────────────────────────────────────────────
        btn_col, role_col, clear_col = st.columns([2, 3, 1])
        with btn_col:
            start_clicked = st.button("▶️ Start / Restart Interview", use_container_width=True)
        with role_col:
            st.text_input("Interviewing for", value=role_label, disabled=True, label_visibility="collapsed")
        with clear_col:
            if st.button("🔄 Clear", use_container_width=True, help="Clear chat history"):
                st.session_state.interview_state = {
                    "started": False, "role": role_label,
                    "current_question": "", "history": [], "scores": [],
                    "provider": _ai_provider, "api_key": _api_key,
                }
                st.rerun()

        if start_clicked:
            if not _ai_ready:
                st.error("❌ AI service is not configured. Contact the administrator.")
            else:
                with st.spinner("🎬 Starting your interview..."):
                    try:
                        first_q = start_interview(role=role_label, provider=_ai_provider, api_key=_api_key)
                        st.session_state.interview_state = {
                            "started": True, "role": role_label,
                            "provider": _ai_provider, "api_key": _api_key,
                            "current_question": first_q,
                            "history": [{"role": "assistant", "content": first_q}],
                            "scores": [],
                        }
                        st.rerun()
                    except Exception as e:
                        _em = str(e)
                        if "quota" in _em.lower() or "429" in _em:
                            st.error("⚠️ AI service is temporarily at capacity. Please try again in a moment.")
                        elif "401" in _em or "403" in _em:
                            st.error("❌ AI authentication failed. Please contact the administrator.")
                        else:
                            st.error(f"❌ Could not start interview: {_em}")

        # ── Tips box (before first start) ───────────────────────────
        if not state.get("started"):
            st.markdown("""
            <div class="tip-box">
            <strong>💡 Tips for a great interview:</strong>
            <ul style="margin:6px 0 0 0; padding-left:18px;">
                <li>Answer with real examples using the STAR method (Situation, Task, Action, Result).</li>
                <li>Keep answers concise — 2-4 sentences per point.</li>
                <li>It’s okay to say “I’m not sure, but I would approach it by...”</li>
                <li>Complete the Skill Gaps tab first for more targeted questions.</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            st.write("")

        # ── Chat history ────────────────────────────────────────────
        if state.get("started") and state.get("history"):
            for msg in state["history"]:
                role_msg = msg.get("role", "assistant")
                content  = msg.get("content", "")
                score    = msg.get("score", 0)

                if role_msg == "user":
                    st.chat_message("user").write(content)
                elif content.startswith("**Feedback"):
                    # Render feedback as a styled card
                    with st.chat_message("assistant"):
                        lines = content.replace("**Feedback:**\n", "").strip().split("\n")
                        bullet_html = "".join(
                            f"<li>{ln.lstrip('- ').strip()}</li>"
                            for ln in lines if ln.strip()
                        )
                        score_html = ""
                        if score and int(score) > 0:
                            sc_class = "score-high" if score >= 7 else "score-mid" if score >= 5 else "score-low"
                            score_html = f'<span class="score-chip {sc_class}">⭐ Score: {score}/10</span>'
                        st.markdown(f"""
                        <div class="feedback-card">
                            <strong>💬 Feedback</strong> {score_html}
                            <ul>{bullet_html}</ul>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.chat_message("assistant").write(content)

            # Answer input
            user_answer = st.chat_input(f"Your answer for the {role_label} interview...")
            if user_answer:
                state["history"].append({"role": "user", "content": user_answer})
                with st.spinner("🤔 Evaluating your answer..."):
                    try:
                        result = interview_turn(
                            role=state.get("role", role_label),
                            question=state.get("current_question", ""),
                            answer=user_answer,
                            missing_skills=missing_skills if missing_skills else None,
                            provider=state.get("provider", _ai_provider),
                            api_key=state.get("api_key") or _api_key,
                        )
                        feedback  = result.get("feedback", "").strip()
                        next_q    = result.get("next_question", "").strip()
                        score_val = int(result.get("score", 0) or 0)

                        if score_val > 0:
                            state.setdefault("scores", []).append(score_val)

                        if feedback:
                            state["history"].append({
                                "role": "assistant",
                                "content": f"**Feedback:**\n{feedback}",
                                "score": score_val,
                            })
                        if next_q:
                            state["current_question"] = next_q
                            state["history"].append({"role": "assistant", "content": next_q})

                        st.session_state.interview_state = state
                        st.rerun()
                    except Exception as e:
                        _msg = str(e)
                        if "quota" in _msg.lower() or "429" in _msg:
                            st.error("⚠️ AI service is temporarily unavailable. Please try again in a moment.")
                        else:
                            st.error(f"❌ Error processing answer: {_msg}")

        # ── Skill-Based Question Generator ────────────────────────────
        st.divider()
        st.markdown("### 🧩 Skill-Based Question Bank")
        st.caption("AI-generated practice questions targeted at your identified skill gaps.")

        if not missing_skills:
            st.caption("Complete Skill Gaps (Tab 3) first to unlock targeted practice questions.")
        else:
            # Skill gap badges
            badges = "".join(
                f'<span class="skill-badge">{s}</span>'
                for s in missing_skills[:12]
            )
            st.markdown(f'<div style="margin-bottom:10px">{badges}</div>', unsafe_allow_html=True)

            qps = st.select_slider(
                "Questions per skill",
                options=[1, 2, 3, 4, 5],
                value=3,
                help="Number of practice questions to generate per skill gap"
            )
            if st.button("⚡ Generate Question Bank", use_container_width=False):
                if not _ai_ready:
                    st.error("❌ AI service is not configured. Contact the administrator.")
                else:
                    with st.spinner(f"Generating {qps} questions per skill..."):
                        try:
                            questions_by_skill = generate_skill_questions(
                                role=role_label,
                                missing_skills=missing_skills,
                                questions_per_skill=int(qps),
                                provider=_ai_provider,
                                api_key=_api_key,
                            )
                            st.session_state.analysis_results['skill_questions'] = questions_by_skill
                            st.caption(f"✅ Generated questions for {len(questions_by_skill)} skills.")
                        except Exception as e:
                            _em = str(e)
                            if "quota" in _em.lower() or "429" in _em:
                                st.error("⚠️ AI quota reached. Please try again later.")
                            else:
                                st.error(f"❌ {_em}")

            questions_by_skill = st.session_state.analysis_results.get('skill_questions')
            if questions_by_skill:
                total_q = sum(len(v) for v in questions_by_skill.values())
                st.caption(f"📚 **{total_q} questions** across **{len(questions_by_skill)} skills**")
                for skill, qs in questions_by_skill.items():
                    with st.expander(f"🎯  {skill}  ({len(qs)} questions)", expanded=False):
                        for idx, q in enumerate(qs, 1):
                            st.markdown(
                                f'<div class="skill-q-card"><strong>Q{idx}.</strong> {q}</div>',
                                unsafe_allow_html=True
                            )

    # ── Tab 8: Tracking & History ──────────────────────────────────────────
    with tab8:
        st.markdown("""
        <div class=\"tab-hero tab-hero-tracking\">
          <div class=\"tab-hero-inner\">
            <div class=\"tab-hero-icon\">📈</div>
            <div class=\"tab-hero-text\">
              <h2>Tracking &amp; History</h2>
              <p>Visual analytics of your career progress &mdash; score trends, skill growth charts, and a full analysis history log.</p>
            </div>
            <span class=\"tab-hero-badge badge-active\">📊 Live</span>
          </div>
        </div>""", unsafe_allow_html=True)
        if _TRACKING_OK:
            render_tracking_tab(
                analysis_results=st.session_state.get("analysis_results", {}),
                selected_role=st.session_state.get("selected_role"),
            )
        else:
            st.error(f"Tracking module unavailable: {_TRACKING_ERR}")
            st.info(
                "Ensure `src/utils/tracking_ui.py` and "
                "`src/database/history_manager.py` are present."
            )


if __name__ == "__main__":
    main()
