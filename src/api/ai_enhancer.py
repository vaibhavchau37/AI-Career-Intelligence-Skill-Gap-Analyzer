"""
AI Enhancement using OpenAI and Google Gemini

Optional AI-powered enhancements for job analysis.
"""

import os
from typing import Optional, Dict, List

from src.api.openai_client import chat_complete


class AIEnhancer:
    """
    AI enhancement using OpenAI and Google Gemini APIs.
    
    Provides optional AI-powered features like:
    - Resume improvement suggestions
    - Skill gap explanations
    - Personalized recommendations
    """
    
    def __init__(
        self,
        openai_key: Optional[str] = None,
        gemini_key: Optional[str] = None
    ):
        """
        Initialize AI enhancer.
        
        Args:
            openai_key: OpenAI API key (or from OPENAI_API_KEY env var)
            gemini_key: Google Gemini API key (or from GOOGLE_GEMINI_API_KEY env var)
        """
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY")
        self.gemini_key = gemini_key or os.getenv("GOOGLE_GEMINI_API_KEY")
        
        self.openai_available = self.openai_key is not None
        self.gemini_available = self.gemini_key is not None
    
    def enhance_skill_gap_explanation(
        self,
        missing_skill: str,
        resume_skills: List[str],
        role_name: str
    ) -> Optional[str]:
        """
        Generate AI-enhanced explanation for missing skills.
        
        Args:
            missing_skill: Missing skill name
            resume_skills: List of resume skills
            role_name: Target job role
            
        Returns:
            Enhanced explanation or None if AI not available
        """
        if not self.openai_available and not self.gemini_available:
            return None
        
        prompt = f"""
        Explain why '{missing_skill}' is important for a {role_name} role.
        The candidate has these skills: {', '.join(resume_skills[:10])}
        Provide a brief, actionable explanation (2-3 sentences).
        """
        
        # Try OpenAI first, then Gemini
        if self.openai_available:
            try:
                return self._openai_request(prompt)
            except Exception:
                pass
        
        if self.gemini_available:
            try:
                return self._gemini_request(prompt)
            except Exception:
                pass
        
        return None
    
    def generate_learning_suggestions(
        self,
        missing_skills: List[str],
        role_name: str
    ) -> Optional[List[str]]:
        """
        Generate AI-powered learning suggestions.
        
        Args:
            missing_skills: List of missing skills
            role_name: Target job role
            
        Returns:
            List of learning suggestions or None
        """
        if not self.openai_available and not self.gemini_available:
            return None
        
        prompt = f"""
        For a {role_name} role, suggest practical learning resources for these skills: {', '.join(missing_skills[:5])}
        Provide 3-5 specific, actionable learning suggestions (courses, projects, tutorials).
        Format as a simple list.
        """
        
        if self.openai_available:
            try:
                response = self._openai_request(prompt)
                return [line.strip("- •") for line in response.split("\n") if line.strip()]
            except Exception:
                pass
        
        if self.gemini_available:
            try:
                response = self._gemini_request(prompt)
                return [line.strip("- •") for line in response.split("\n") if line.strip()]
            except Exception:
                pass
        
        return None
    
    def _openai_request(self, prompt: str) -> str:
        """Make request to OpenAI API."""
        try:
            return chat_complete(
                [
                    {"role": "system", "content": "You are a helpful career advisor."},
                    {"role": "user", "content": prompt},
                ],
                api_key=self.openai_key,
                temperature=0.7,
                max_tokens=220,
            )
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")
    
    def _gemini_request(self, prompt: str) -> str:
        """Make request to Google Gemini API."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)
            
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            
            return response.text.strip()
        except ImportError:
            raise ImportError("Google Generative AI library not installed. Install with: pip install google-generativeai")
        except Exception as e:
            raise Exception(f"Gemini API error: {e}")

