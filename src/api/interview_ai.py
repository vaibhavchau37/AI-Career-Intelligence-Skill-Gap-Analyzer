"""Interview & practice helpers powered by OpenAI Chat API.

Provides:
- Interview simulator turns (question -> answer -> feedback + next question)
- Skill-based question generation from missing skills

OpenAI is optional and controlled by environment variables.
"""

from __future__ import annotations

import json
from typing import Optional

from src.api.llm_router import chat_complete


INTERVIEWER_SYSTEM_PROMPT = (
    "Act as an interviewer for a Data Scientist role. "
    "Ask one question at a time. After the candidate answers, give concise feedback "
    "(strengths + what to improve) and then ask the next question. "
    "Keep questions practical and role-relevant."
)


def start_interview(role: str = "Data Scientist", provider: str = "OpenAI") -> str:
    messages = [
        {"role": "system", "content": INTERVIEWER_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Start a mock interview for the role: {role}. "
                "Ask the first question only."
            ),
        },
    ]
    return chat_complete(provider, messages, temperature=0.6, max_tokens=250)


def interview_turn(
    *,
    role: str,
    question: str,
    answer: str,
    missing_skills: Optional[list[str]] = None,
    provider: str = "OpenAI",
) -> dict:
    """One interview turn: returns feedback + next question.

    Output schema:
    {"feedback": "...", "next_question": "..."}
    """
    skills_hint = ""
    if missing_skills:
        top = ", ".join(missing_skills[:8])
        skills_hint = (
            f"The candidate is currently missing these skills: {top}. "
            "Prefer to include them across questions when relevant."
        )

    prompt = (
        f"Role: {role}\n"
        f"Interviewer question: {question}\n"
        f"Candidate answer: {answer}\n\n"
        f"{skills_hint}\n"
        "Return JSON only with keys: feedback, next_question. "
        "feedback must be 3-6 bullet points (use '-' bullets). "
        "next_question must be a single interview question."
    )

    raw = chat_complete(
        provider,
        [
            {"role": "system", "content": INTERVIEWER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        max_tokens=450,
    )

    # Best-effort JSON parsing.
    try:
        data = json.loads(raw)
        return {
            "feedback": str(data.get("feedback", "")).strip(),
            "next_question": str(data.get("next_question", "")).strip(),
        }
    except Exception:
        # Fallback: treat raw as feedback and ask a generic next question.
        return {
            "feedback": raw.strip(),
            "next_question": "Tell me about a recent data science project you built end-to-end.",
        }


def generate_skill_questions(
    *,
    role: str,
    missing_skills: list[str],
    questions_per_skill: int = 3,
    provider: str = "OpenAI",
) -> dict[str, list[str]]:
    """Generate interview questions grouped by missing skill."""
    skills = [s for s in missing_skills if s][:12]
    prompt = (
        f"Generate interview questions for role: {role}.\n"
        f"Only use these missing skills: {', '.join(skills)}\n"
        f"For each skill, generate {questions_per_skill} questions.\n"
        "Return JSON only: {skill: [questions...]}. "
        "Questions must be concise and practical."
    )

    raw = chat_complete(
        provider,
        [
            {
                "role": "system",
                "content": "You generate interview questions for technical roles.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
        max_tokens=700,
    )

    try:
        data = json.loads(raw)
        out: dict[str, list[str]] = {}
        for k, v in data.items():
            if not isinstance(k, str) or not isinstance(v, list):
                continue
            out[k] = [str(q).strip() for q in v if str(q).strip()]
        return out
    except Exception:
        # Fallback: return a flat list under "Questions"
        lines = [ln.strip("-• ") for ln in raw.splitlines() if ln.strip()]
        return {"Questions": lines}
