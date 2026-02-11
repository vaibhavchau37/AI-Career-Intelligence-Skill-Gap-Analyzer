"""
MySQL Database Manager for AI Career Intelligence & Skill Gap Analyzer.

Handles user registration, login, session management, and progress tracking.
Uses mysql-connector-python for MySQL connectivity.
"""

import mysql.connector
from mysql.connector import Error
import json
import hashlib
import os
from datetime import datetime
from typing import Optional, Dict, List, Any


class DatabaseManager:
    """Manages MySQL database connections and operations."""

    def __init__(self, host: str = "localhost", user: str = "root",
                 password: str = "", database: str = "career_analyzer",
                 port: int = 3306):
        """
        Initialize database connection parameters.
        
        Args:
            host: MySQL host address
            user: MySQL username
            password: MySQL password
            database: Database name
            port: MySQL port
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.connection = None

    def connect(self) -> bool:
        """Establish connection to MySQL database."""
        try:
            # First connect without database to create it if needed
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                port=self.port
            )
            cursor = self.connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.database}`")
            cursor.execute(f"USE `{self.database}`")
            cursor.close()
            self._create_tables()
            return True
        except Error as e:
            print(f"Database connection error: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def _get_cursor(self):
        """Get a database cursor, reconnecting if needed."""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        return self.connection.cursor(dictionary=True)

    def _create_tables(self):
        """Create all required tables if they don't exist."""
        cursor = self._get_cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)

        # Resume uploads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resume_uploads (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                filename VARCHAR(255),
                parsed_data JSON,
                skills_extracted JSON,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Analysis sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                resume_id INT,
                target_role VARCHAR(255),
                readiness_score FLOAT,
                matched_skills JSON,
                missing_skills JSON,
                skill_gap_results JSON,
                suitability_results JSON,
                roadmap_data JSON,
                interview_questions JSON,
                session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (resume_id) REFERENCES resume_uploads(id) ON DELETE SET NULL
            )
        """)

        # User progress tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                session_id INT,
                skill_name VARCHAR(255),
                status ENUM('not_started', 'in_progress', 'completed') DEFAULT 'not_started',
                progress_percentage FLOAT DEFAULT 0,
                notes TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES analysis_sessions(id) ON DELETE SET NULL
            )
        """)

        # Reports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                session_id INT,
                report_type VARCHAR(50),
                report_data JSON,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES analysis_sessions(id) ON DELETE SET NULL
            )
        """)

        self.connection.commit()
        cursor.close()

    # ─── User Management ───────────────────────────────────────────

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt."""
        salt = "career_analyzer_salt_2024"
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

    def register_user(self, username: str, email: str, password: str,
                      full_name: str = "") -> Dict[str, Any]:
        """
        Register a new user.
        
        Returns:
            dict with 'success' and 'message' or 'user_id'
        """
        try:
            cursor = self._get_cursor()
            password_hash = self._hash_password(password)

            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES (%s, %s, %s, %s)
            """, (username, email, password_hash, full_name))

            self.connection.commit()
            user_id = cursor.lastrowid
            cursor.close()

            return {"success": True, "user_id": user_id, "message": "Registration successful!"}
        except mysql.connector.IntegrityError as e:
            if "username" in str(e):
                return {"success": False, "message": "Username already exists."}
            elif "email" in str(e):
                return {"success": False, "message": "Email already registered."}
            return {"success": False, "message": f"Registration failed: {e}"}
        except Error as e:
            return {"success": False, "message": f"Database error: {e}"}

    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user.
        
        Returns:
            dict with 'success', 'user_id', 'username', 'email', 'full_name'
        """
        try:
            cursor = self._get_cursor()
            password_hash = self._hash_password(password)

            cursor.execute("""
                SELECT id, username, email, full_name FROM users
                WHERE username = %s AND password_hash = %s AND is_active = TRUE
            """, (username, password_hash))

            user = cursor.fetchone()

            if user:
                # Update last login
                cursor.execute("""
                    UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s
                """, (user['id'],))
                self.connection.commit()
                cursor.close()

                return {
                    "success": True,
                    "user_id": user['id'],
                    "username": user['username'],
                    "email": user['email'],
                    "full_name": user['full_name']
                }
            else:
                cursor.close()
                return {"success": False, "message": "Invalid username or password."}
        except Error as e:
            return {"success": False, "message": f"Login failed: {e}"}

    # ─── Resume Operations ─────────────────────────────────────────

    def save_resume(self, user_id: int, filename: str,
                    parsed_data: Dict, skills: List[str]) -> Optional[int]:
        """Save parsed resume data to database. Returns resume_id."""
        try:
            cursor = self._get_cursor()
            cursor.execute("""
                INSERT INTO resume_uploads (user_id, filename, parsed_data, skills_extracted)
                VALUES (%s, %s, %s, %s)
            """, (user_id, filename, json.dumps(parsed_data, default=str),
                  json.dumps(skills)))

            self.connection.commit()
            resume_id = cursor.lastrowid
            cursor.close()
            return resume_id
        except Error as e:
            print(f"Error saving resume: {e}")
            return None

    def get_user_resumes(self, user_id: int) -> List[Dict]:
        """Get all resumes uploaded by a user."""
        try:
            cursor = self._get_cursor()
            cursor.execute("""
                SELECT id, filename, skills_extracted, upload_date
                FROM resume_uploads
                WHERE user_id = %s
                ORDER BY upload_date DESC
            """, (user_id,))

            resumes = cursor.fetchall()
            cursor.close()

            for r in resumes:
                if r.get('skills_extracted') and isinstance(r['skills_extracted'], str):
                    r['skills_extracted'] = json.loads(r['skills_extracted'])
            return resumes
        except Error as e:
            print(f"Error fetching resumes: {e}")
            return []

    def get_resume_by_id(self, resume_id: int) -> Optional[Dict]:
        """Get a specific resume by ID."""
        try:
            cursor = self._get_cursor()
            cursor.execute("""
                SELECT * FROM resume_uploads WHERE id = %s
            """, (resume_id,))
            resume = cursor.fetchone()
            cursor.close()

            if resume:
                if resume.get('parsed_data') and isinstance(resume['parsed_data'], str):
                    resume['parsed_data'] = json.loads(resume['parsed_data'])
                if resume.get('skills_extracted') and isinstance(resume['skills_extracted'], str):
                    resume['skills_extracted'] = json.loads(resume['skills_extracted'])
            return resume
        except Error as e:
            print(f"Error fetching resume: {e}")
            return None

    # ─── Analysis Session Operations ───────────────────────────────

    def save_analysis_session(self, user_id: int, resume_id: int,
                              target_role: str, readiness_score: float,
                              matched_skills: List, missing_skills: List,
                              skill_gap_results: Dict = None,
                              suitability_results: Dict = None,
                              roadmap_data: Dict = None,
                              interview_questions: List = None) -> Optional[int]:
        """Save a complete analysis session. Returns session_id."""
        try:
            cursor = self._get_cursor()
            cursor.execute("""
                INSERT INTO analysis_sessions
                (user_id, resume_id, target_role, readiness_score,
                 matched_skills, missing_skills, skill_gap_results,
                 suitability_results, roadmap_data, interview_questions)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, resume_id, target_role, readiness_score,
                json.dumps(matched_skills, default=str),
                json.dumps(missing_skills, default=str),
                json.dumps(skill_gap_results, default=str) if skill_gap_results else None,
                json.dumps(suitability_results, default=str) if suitability_results else None,
                json.dumps(roadmap_data, default=str) if roadmap_data else None,
                json.dumps(interview_questions, default=str) if interview_questions else None
            ))

            self.connection.commit()
            session_id = cursor.lastrowid
            cursor.close()
            return session_id
        except Error as e:
            print(f"Error saving session: {e}")
            return None

    def get_user_sessions(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get analysis history for a user."""
        try:
            cursor = self._get_cursor()
            cursor.execute("""
                SELECT id, target_role, readiness_score, session_date,
                       matched_skills, missing_skills
                FROM analysis_sessions
                WHERE user_id = %s
                ORDER BY session_date DESC
                LIMIT %s
            """, (user_id, limit))

            sessions = cursor.fetchall()
            cursor.close()

            for s in sessions:
                for field in ['matched_skills', 'missing_skills']:
                    if s.get(field) and isinstance(s[field], str):
                        s[field] = json.loads(s[field])
            return sessions
        except Error as e:
            print(f"Error fetching sessions: {e}")
            return []

    def get_session_by_id(self, session_id: int) -> Optional[Dict]:
        """Get full session details."""
        try:
            cursor = self._get_cursor()
            cursor.execute("SELECT * FROM analysis_sessions WHERE id = %s", (session_id,))
            session = cursor.fetchone()
            cursor.close()

            if session:
                json_fields = ['matched_skills', 'missing_skills', 'skill_gap_results',
                               'suitability_results', 'roadmap_data', 'interview_questions']
                for field in json_fields:
                    if session.get(field) and isinstance(session[field], str):
                        session[field] = json.loads(session[field])
            return session
        except Error as e:
            print(f"Error fetching session: {e}")
            return None

    # ─── Progress Tracking ─────────────────────────────────────────

    def save_skill_progress(self, user_id: int, session_id: int,
                            skill_name: str, status: str = "not_started",
                            progress: float = 0, notes: str = "") -> bool:
        """Save or update skill learning progress."""
        try:
            cursor = self._get_cursor()

            # Check if progress exists
            cursor.execute("""
                SELECT id FROM user_progress
                WHERE user_id = %s AND session_id = %s AND skill_name = %s
            """, (user_id, session_id, skill_name))

            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE user_progress
                    SET status = %s, progress_percentage = %s, notes = %s
                    WHERE id = %s
                """, (status, progress, notes, existing['id']))
            else:
                cursor.execute("""
                    INSERT INTO user_progress
                    (user_id, session_id, skill_name, status, progress_percentage, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, session_id, skill_name, status, progress, notes))

            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error saving progress: {e}")
            return False

    def get_user_progress(self, user_id: int, session_id: int = None) -> List[Dict]:
        """Get learning progress for a user."""
        try:
            cursor = self._get_cursor()

            if session_id:
                cursor.execute("""
                    SELECT * FROM user_progress
                    WHERE user_id = %s AND session_id = %s
                    ORDER BY updated_at DESC
                """, (user_id, session_id))
            else:
                cursor.execute("""
                    SELECT * FROM user_progress
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                """, (user_id,))

            progress = cursor.fetchall()
            cursor.close()
            return progress
        except Error as e:
            print(f"Error fetching progress: {e}")
            return []

    # ─── Report Operations ─────────────────────────────────────────

    def save_report(self, user_id: int, session_id: int,
                    report_type: str, report_data: Dict) -> Optional[int]:
        """Save a generated report."""
        try:
            cursor = self._get_cursor()
            cursor.execute("""
                INSERT INTO reports (user_id, session_id, report_type, report_data)
                VALUES (%s, %s, %s, %s)
            """, (user_id, session_id, report_type, json.dumps(report_data, default=str)))

            self.connection.commit()
            report_id = cursor.lastrowid
            cursor.close()
            return report_id
        except Error as e:
            print(f"Error saving report: {e}")
            return None

    # ─── Dashboard Statistics ──────────────────────────────────────

    def get_user_dashboard_stats(self, user_id: int) -> Dict:
        """Get aggregated stats for user dashboard."""
        try:
            cursor = self._get_cursor()

            # Total sessions
            cursor.execute("""
                SELECT COUNT(*) as total FROM analysis_sessions WHERE user_id = %s
            """, (user_id,))
            total_sessions = cursor.fetchone()['total']

            # Average readiness score
            cursor.execute("""
                SELECT AVG(readiness_score) as avg_score
                FROM analysis_sessions WHERE user_id = %s
            """, (user_id,))
            avg_score = cursor.fetchone()['avg_score'] or 0

            # Best score
            cursor.execute("""
                SELECT MAX(readiness_score) as best_score, target_role
                FROM analysis_sessions WHERE user_id = %s
                GROUP BY target_role ORDER BY best_score DESC LIMIT 1
            """, (user_id,))
            best = cursor.fetchone()
            best_score = best['best_score'] if best else 0
            best_role = best['target_role'] if best else "N/A"

            # Skills progress
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM user_progress WHERE user_id = %s
                GROUP BY status
            """, (user_id,))
            progress_stats = {row['status']: row['count'] for row in cursor.fetchall()}

            # Score history (last 10)
            cursor.execute("""
                SELECT target_role, readiness_score, session_date
                FROM analysis_sessions WHERE user_id = %s
                ORDER BY session_date DESC LIMIT 10
            """, (user_id,))
            score_history = cursor.fetchall()

            cursor.close()

            return {
                "total_sessions": total_sessions,
                "avg_score": round(avg_score, 1),
                "best_score": round(best_score, 1),
                "best_role": best_role,
                "skills_not_started": progress_stats.get("not_started", 0),
                "skills_in_progress": progress_stats.get("in_progress", 0),
                "skills_completed": progress_stats.get("completed", 0),
                "score_history": score_history
            }
        except Error as e:
            print(f"Error fetching stats: {e}")
            return {
                "total_sessions": 0, "avg_score": 0, "best_score": 0,
                "best_role": "N/A", "skills_not_started": 0,
                "skills_in_progress": 0, "skills_completed": 0,
                "score_history": []
            }
