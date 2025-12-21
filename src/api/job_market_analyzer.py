"""
Job Market Analyzer - Real-time job data integration
"""

import os
from typing import List, Dict, Optional
from src.api.adzuna_api import AdzunaJobAPI


class JobMarketAnalyzer:
    """
    Analyze job market trends and get real-time job listings.
    """
    
    def __init__(self):
        """Initialize job market analyzer."""
        try:
            self.adzuna = AdzunaJobAPI()
            self.api_available = True
        except ValueError:
            self.adzuna = None
            self.api_available = False
    
    def get_jobs_for_role(
        self,
        role_name: str,
        location: str = "India",
        limit: int = 10
    ) -> List[Dict]:
        """
        Get real-time job listings for a role.
        
        Args:
            role_name: Job role name
            location: Location (default: India)
            limit: Number of jobs to fetch
            
        Returns:
            List of job listings
        """
        if not self.api_available:
            return []
        
        return self.adzuna.get_jobs_for_role(role_name, location, limit)
    
    def get_market_statistics(
        self,
        role_name: str,
        location: str = "India"
    ) -> Dict:
        """
        Get job market statistics for a role.
        
        Args:
            role_name: Job role name
            location: Location
            
        Returns:
            Dictionary with market statistics
        """
        if not self.api_available:
            return {
                "error": "API not configured",
                "total_jobs": 0
            }
        
        role_keywords = {
            "ML Engineer": "Machine Learning Engineer",
            "Data Scientist": "Data Scientist",
            "Data Analyst": "Data Analyst",
            "AI Engineer": "AI Engineer",
            "Python Developer": "Python Developer"
        }
        
        keywords = role_keywords.get(role_name, role_name)
        return self.adzuna.get_job_statistics(keywords, location)
    
    def is_available(self) -> bool:
        """Check if API is available."""
        return self.api_available

