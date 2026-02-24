"""
SQLite History Manager – Phase 7: Tracking & History.

Persists real analysis results (scores, skills) produced by the live pipeline.
No demo or dummy data is ever inserted here.

Database file: <project_root>/database.db
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

# ── Resolve DB path relative to project root ──────────────────────────────────
_HERE        = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
DB_PATH      = os.path.join(_PROJECT_ROOT, "database.db")


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute("PRAGMA foreign_keys=ON;")
    return c


def _init() -> None:
    """Create tables once on first import."""
    con = _conn()
    with con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS profiles (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT UNIQUE NOT NULL,
                full_name  TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS score_snapshots (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id       INTEGER NOT NULL
                                   REFERENCES profiles(id) ON DELETE CASCADE,
                target_role      TEXT    NOT NULL,
                overall_score    REAL    NOT NULL,
                skills_score     REAL    DEFAULT 0,
                experience_score REAL    DEFAULT 0,
                projects_score   REAL    DEFAULT 0,
                matched_skills   TEXT    DEFAULT '[]',
                missing_skills   TEXT    DEFAULT '[]',
                matched_count    INTEGER DEFAULT 0,
                missing_count    INTEGER DEFAULT 0,
                notes            TEXT    DEFAULT '',
                saved_at         TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS skill_progress (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL
                             REFERENCES profiles(id) ON DELETE CASCADE,
                skill_name TEXT    NOT NULL,
                status     TEXT    DEFAULT 'missing',
                updated_at TEXT    DEFAULT (datetime('now')),
                UNIQUE(profile_id, skill_name)
            );
        """)
    con.close()


_init()


# ── Profile ───────────────────────────────────────────────────────────────────

def get_or_create_profile(username: str, full_name: str = "") -> int:
    username = username.strip().lower()
    if not username:
        raise ValueError("username cannot be empty")
    con = _conn()
    with con:
        row = con.execute(
            "SELECT id FROM profiles WHERE username=?", (username,)
        ).fetchone()
        if row:
            con.close()
            return int(row["id"])
        cur = con.execute(
            "INSERT INTO profiles (username, full_name) VALUES (?,?)",
            (username, full_name.strip())
        )
        pid = cur.lastrowid
    con.close()
    return pid


def get_all_profiles() -> List[Dict[str, Any]]:
    con = _conn()
    rows = con.execute(
        "SELECT id, username, full_name, created_at FROM profiles ORDER BY username"
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def delete_profile(profile_id: int) -> None:
    con = _conn()
    with con:
        con.execute("DELETE FROM profiles WHERE id=?", (profile_id,))
    con.close()


# ── Score snapshots ───────────────────────────────────────────────────────────

def save_score_snapshot(
    profile_id: int,
    target_role: str,
    overall_score: float,
    skills_score: float = 0.0,
    experience_score: float = 0.0,
    projects_score: float = 0.0,
    matched_skills: Optional[List[str]] = None,
    missing_skills: Optional[List[str]] = None,
    notes: str = "",
) -> int:
    matched_skills = matched_skills or []
    missing_skills = missing_skills or []
    con = _conn()
    with con:
        cur = con.execute(
            """INSERT INTO score_snapshots
               (profile_id, target_role, overall_score, skills_score,
                experience_score, projects_score,
                matched_skills, missing_skills,
                matched_count, missing_count, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                profile_id,
                target_role.strip(),
                round(float(overall_score), 2),
                round(float(skills_score), 2),
                round(float(experience_score), 2),
                round(float(projects_score), 2),
                json.dumps(matched_skills),
                json.dumps(missing_skills),
                len(matched_skills),
                len(missing_skills),
                notes,
            ),
        )
        sid = cur.lastrowid
    con.close()
    return sid


def get_snapshots_for_profile(
    profile_id: int,
    target_role: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    con = _conn()
    if target_role:
        rows = con.execute(
            """SELECT * FROM score_snapshots
               WHERE profile_id=? AND target_role=?
               ORDER BY saved_at ASC LIMIT ?""",
            (profile_id, target_role.strip(), limit),
        ).fetchall()
    else:
        rows = con.execute(
            """SELECT * FROM score_snapshots
               WHERE profile_id=?
               ORDER BY saved_at ASC LIMIT ?""",
            (profile_id, limit),
        ).fetchall()
    con.close()
    result = []
    for r in rows:
        d = dict(r)
        for f in ("matched_skills", "missing_skills"):
            try:
                d[f] = json.loads(d[f]) if d[f] else []
            except Exception:
                d[f] = []
        result.append(d)
    return result


def get_distinct_roles(profile_id: int) -> List[str]:
    con = _conn()
    rows = con.execute(
        "SELECT DISTINCT target_role FROM score_snapshots WHERE profile_id=? ORDER BY target_role",
        (profile_id,),
    ).fetchall()
    con.close()
    return [r["target_role"] for r in rows]


def delete_snapshot(snapshot_id: int) -> None:
    con = _conn()
    with con:
        con.execute("DELETE FROM score_snapshots WHERE id=?", (snapshot_id,))
    con.close()


def clear_snapshots_for_profile(profile_id: int) -> int:
    con = _conn()
    with con:
        cur = con.execute(
            "DELETE FROM score_snapshots WHERE profile_id=?", (profile_id,)
        )
        n = cur.rowcount
    con.close()
    return n


def get_before_after(profile_id: int, target_role: str) -> Dict[str, Any]:
    con = _conn()
    rows = con.execute(
        """SELECT * FROM score_snapshots
           WHERE profile_id=? AND target_role=?
           ORDER BY saved_at ASC""",
        (profile_id, target_role.strip()),
    ).fetchall()
    con.close()
    if not rows:
        return {"first": None, "latest": None, "delta": 0.0}
    first  = dict(rows[0])
    latest = dict(rows[-1])
    for snap in (first, latest):
        for f in ("matched_skills", "missing_skills"):
            try:
                snap[f] = json.loads(snap[f]) if snap[f] else []
            except Exception:
                snap[f] = []
    return {
        "first": first,
        "latest": latest,
        "delta": round(latest["overall_score"] - first["overall_score"], 2),
    }


# ── Skill-level progress ──────────────────────────────────────────────────────

def upsert_skill_status(profile_id: int, skill_name: str, status: str) -> None:
    con = _conn()
    with con:
        con.execute(
            """INSERT INTO skill_progress (profile_id, skill_name, status, updated_at)
               VALUES (?,?,?,datetime('now'))
               ON CONFLICT(profile_id, skill_name)
               DO UPDATE SET status=excluded.status,
                             updated_at=excluded.updated_at""",
            (profile_id, skill_name.strip().lower(), status),
        )
    con.close()


def get_skill_statuses(profile_id: int) -> Dict[str, str]:
    con = _conn()
    rows = con.execute(
        "SELECT skill_name, status FROM skill_progress WHERE profile_id=?",
        (profile_id,),
    ).fetchall()
    con.close()
    return {r["skill_name"]: r["status"] for r in rows}
