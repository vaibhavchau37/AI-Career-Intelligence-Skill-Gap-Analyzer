"""Functions to generate explanations for scores and recommendations."""

from typing import Dict, List
from src.models.analysis_result import RoleScore, SkillGap


def generate_score_explanation(score: RoleScore) -> str:
    """Generate human-readable explanation for a role score."""
    score_value = score.overall_score
    
    # Overall assessment
    if score_value >= 80:
        assessment = "Excellent fit"
    elif score_value >= 65:
        assessment = "Good fit"
    elif score_value >= 50:
        assessment = "Moderate fit"
    elif score_value >= 35:
        assessment = "Needs improvement"
    else:
        assessment = "Poor fit"
    
    explanation = f"Your readiness score for {score.role_name} is {score_value:.1f}/100 ({assessment}).\n\n"
    
    # Score breakdown
    explanation += "Score Breakdown:\n"
    for category, value in score.breakdown.items():
        explanation += f"  - {category.replace('_', ' ').title()}: {value:.1f}%\n"
    
    # Strengths
    if score.matched_skills:
        explanation += f"\nStrengths:\n"
        explanation += f"  - You have {len(score.matched_skills)} matching skills\n"
        top_skills = score.matched_skills[:5]
        explanation += f"  - Key skills: {', '.join(top_skills)}\n"
    
    # Weaknesses
    if score.missing_skills:
        required_missing = [s for s in score.missing_skills if s.category == "required"]
        if required_missing:
            explanation += f"\nCritical Gaps:\n"
            explanation += f"  - Missing {len(required_missing)} required skills\n"
            top_missing = required_missing[:3]
            explanation += f"  - Focus on: {', '.join([s.skill for s in top_missing])}\n"
    
    # Experience
    if score.experience_score < 50:
        explanation += f"\nNote: Experience level is below ideal. Consider gaining more hands-on experience.\n"
    
    return explanation


def explain_skill_gap(skill_gap: SkillGap) -> str:
    """Generate explanation for a skill gap."""
    importance_text = "critical" if skill_gap.category == "required" else "beneficial"
    
    explanation = f"Missing skill: {skill_gap.skill}\n"
    explanation += f"  - Importance: {importance_text} ({skill_gap.category})\n"
    
    if skill_gap.description:
        explanation += f"  - Description: {skill_gap.description}\n"
    
    if skill_gap.learning_resources:
        explanation += f"  - Learning resources: {', '.join(skill_gap.learning_resources[:3])}\n"
    
    return explanation


def generate_roadmap_summary(roadmap_items: List) -> str:
    """Generate summary for a learning roadmap."""
    if not roadmap_items:
        return "No specific roadmap generated."
    
    total_days = sum(item.get('estimated_days', 0) for item in roadmap_items)
    
    summary = f"Learning Roadmap ({total_days} days estimated):\n\n"
    
    for i, item in enumerate(roadmap_items[:10], 1):  # Top 10 items
        summary += f"{i}. {item.get('skill', 'N/A')}\n"
        summary += f"   Priority: {item.get('priority', 'Medium')}\n"
        if item.get('estimated_days'):
            summary += f"   Estimated time: {item['estimated_days']} days\n"
    
    return summary

