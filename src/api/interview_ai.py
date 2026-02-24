"""Interview & practice helpers.

Provides:
- Interview simulator turns (question -> answer -> feedback + next question)
- Skill-based question generation from missing skills
"""

from __future__ import annotations

import json
import re
from typing import Optional

from src.api.llm_router import chat_complete


def _build_system_prompt(role: str) -> str:
    return (
        f"You are an expert technical interviewer conducting a mock interview for the role: {role}. "
        "Ask one focused, practical question at a time. "
        "After the candidate answers, provide structured feedback covering: "
        "(1) what was strong, (2) what could be improved, (3) a tip. "
        "Then ask the next question. Stay professional, encouraging, and role-relevant."
    )


def _extract_json(raw: str) -> dict:
    """Robustly extract JSON from LLM output that may include markdown fences."""
    # Strip markdown code fences
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    # Try direct parse
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    # Try to find first {...} block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return {}


def start_interview(
    role: str = "Data Scientist",
    provider: str = "OpenAI",
    api_key: Optional[str] = None,
) -> str:
    system_prompt = _build_system_prompt(role)
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"Start a mock interview for the role: {role}. "
                "Introduce yourself briefly as the interviewer (1 sentence), "
                "then ask only the first interview question."
            ),
        },
    ]
    return chat_complete(provider, messages, temperature=0.6, max_tokens=300, api_key=api_key)


def interview_turn(
    *,
    role: str,
    question: str,
    answer: str,
    missing_skills: Optional[list[str]] = None,
    provider: str = "OpenAI",
    api_key: Optional[str] = None,
) -> dict:
    """One interview turn: returns feedback + next_question.

    Output schema: {"feedback": str, "next_question": str, "score": int (1-10)}
    """
    skills_hint = ""
    if missing_skills:
        top = ", ".join(missing_skills[:8])
        skills_hint = (
            f"\nNote: The candidate has gaps in: {top}. "
            "Weave relevant skill-gap questions in naturally when appropriate."
        )

    prompt = (
        f"Role: {role}\n"
        f"Interviewer asked: {question}\n"
        f"Candidate answered: {answer}"
        f"{skills_hint}\n\n"
        "Respond with ONLY a JSON object with exactly these keys:\n"
        "  feedback: a string with 3-5 bullet points starting with '-' covering strengths, improvements, and a tip\n"
        "  next_question: a single focused interview question as a plain string\n"
        "  score: an integer 1-10 rating the candidate answer quality\n"
        "Do not include any text outside the JSON."
    )

    raw = chat_complete(
        provider,
        [
            {"role": "system", "content": _build_system_prompt(role)},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        max_tokens=500,
        api_key=api_key,
    )

    data = _extract_json(raw)
    if data and "feedback" in data and "next_question" in data:
        return {
            "feedback": str(data.get("feedback", "")).strip(),
            "next_question": str(data.get("next_question", "")).strip(),
            "score": int(data.get("score", 0)) if str(data.get("score", "")).isdigit() else 0,
        }
    # Fallback: raw text is feedback
    return {
        "feedback": raw.strip(),
        "next_question": f"Can you describe a challenging project where you applied your {role} skills?",
        "score": 0,
    }


def generate_skill_questions(
    *,
    role: str,
    missing_skills: list[str],
    questions_per_skill: int = 3,
    provider: str = "OpenAI",
    api_key: Optional[str] = None,
) -> dict[str, list[str]]:
    """Generate interview questions grouped by missing skill."""
    skills = [s for s in missing_skills if s][:12]
    prompt = (
        f"You are a senior interviewer for the role: {role}.\n"
        f"Generate exactly {questions_per_skill} practical interview questions for EACH of these skills:\n"
        f"{', '.join(skills)}\n\n"
        "Return ONLY a JSON object where each key is a skill name and the value is "
        f"a list of exactly {questions_per_skill} interview question strings.\n"
        "No extra text outside the JSON."
    )

    raw = chat_complete(
        provider,
        [
            {"role": "system", "content": "You generate structured interview questions for technical roles."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        max_tokens=900,
        api_key=api_key,
    )

    data = _extract_json(raw)
    if data:
        out: dict[str, list[str]] = {}
        for k, v in data.items():
            if isinstance(k, str) and isinstance(v, list):
                out[k] = [str(q).strip() for q in v if str(q).strip()]
        if out:
            return out

    # Fallback: return raw lines under generic key
    lines = [ln.strip("-• ").strip() for ln in raw.splitlines() if ln.strip()]
    return {"Questions": lines}
