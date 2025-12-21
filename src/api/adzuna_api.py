"""
Adzuna API Integration for Real-Time Job Listings

Fetches real-time job data from India using Adzuna API.
"""

import requests
import os
from typing import List, Dict, Optional
from datetime import datetime


class AdzunaJobAPI:
    """
    Adzuna API client for fetching real-time job listings.
    
    API Documentation: https://developer.adzuna.com/
    """
    
    BASE_URL = "https://api.adzuna.com/v1/api"
    
    def __init__(self, app_id: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize Adzuna API client.
        
        Args:
            app_id: Adzuna App ID (or from environment variable ADZUNA_APP_ID)
            api_key: Adzuna API Key (or from environment variable ADZUNA_API_KEY)
        """
        self.app_id = app_id or os.getenv("ADZUNA_APP_ID")
        self.api_key = api_key or os.getenv("ADZUNA_API_KEY")
        
        if not self.app_id or not self.api_key:
            raise ValueError(
                "Adzuna API credentials not found. "
                "Set ADZUNA_APP_ID and ADZUNA_API_KEY environment variables or pass them as parameters."
            )
    
    def search_jobs(
        self,
        keywords: str,
        location: str = "India",
        results_per_page: int = 20,
        page: int = 1,
        category: Optional[str] = None
    ) -> Dict:
        """
        Search for jobs in India.
        
        Args:
            keywords: Job search keywords (e.g., "Machine Learning Engineer")
            location: Location (default: "India")
            results_per_page: Number of results per page (max 50)
            page: Page number
            category: Job category (optional)
            
        Returns:
            Dictionary with job listings and metadata
        """
        # Adzuna uses country code for India
        country_code = "in"  # India
        
        url = f"{self.BASE_URL}/jobs/{country_code}/search/{page}"
        
        params = {
            "app_id": self.app_id,
            "app_key": self.api_key,
            "results_per_page": min(results_per_page, 50),
            "what": keywords,
            "where": location,
        }
        
        if category:
            params["category"] = category
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "results": data.get("results", []),
                "count": data.get("count", 0),
                "total_results": len(data.get("results", [])),
                "metadata": {
                    "page": page,
                    "results_per_page": results_per_page,
                    "location": location,
                    "keywords": keywords
                }
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "count": 0
            }
    
    def get_jobs_by_category(
        self,
        category: str,
        location: str = "India",
        results_per_page: int = 20
    ) -> Dict:
        """
        Get jobs by category.
        
        Common categories:
        - it-jobs (IT & Software)
        - engineering-jobs (Engineering)
        - data-science-jobs (Data Science)
        - ai-jobs (AI & Machine Learning)
        
        Args:
            category: Job category
            location: Location
            results_per_page: Number of results
            
        Returns:
            Dictionary with job listings
        """
        return self.search_jobs(
            keywords="",
            location=location,
            results_per_page=results_per_page,
            category=category
        )
    
    def format_job_listing(self, job: Dict) -> Dict:
        """
        Format a job listing for display.
        
        Args:
            job: Raw job data from API
            
        Returns:
            Formatted job dictionary
        """
        return {
            "title": job.get("title", "N/A"),
            "company": job.get("company", {}).get("display_name", "N/A"),
            "location": job.get("location", {}).get("display_name", "N/A"),
            "description": job.get("description", "")[:500] + "..." if len(job.get("description", "")) > 500 else job.get("description", ""),
            "salary_min": job.get("salary_min"),
            "salary_max": job.get("salary_max"),
            "salary_currency": job.get("salary_is_predicted", False),
            "created": job.get("created", ""),
            "url": job.get("redirect_url", ""),
            "category": job.get("category", {}).get("label", "N/A"),
            "contract_type": job.get("contract_type", "N/A"),
        }
    
    def get_jobs_for_role(
        self,
        role_name: str,
        location: str = "India",
        limit: int = 10
    ) -> List[Dict]:
        """
        Get job listings for a specific role.
        
        Args:
            role_name: Name of the role (e.g., "ML Engineer", "Data Scientist")
            location: Location (default: "India")
            limit: Maximum number of jobs to return
            
        Returns:
            List of formatted job listings
        """
        # Map role names to search keywords
        role_keywords = {
            "ML Engineer": "Machine Learning Engineer",
            "Data Scientist": "Data Scientist",
            "Data Analyst": "Data Analyst",
            "AI Engineer": "AI Engineer Artificial Intelligence",
            "Python Developer": "Python Developer"
        }
        
        keywords = role_keywords.get(role_name, role_name)
        
        result = self.search_jobs(
            keywords=keywords,
            location=location,
            results_per_page=limit
        )
        
        if result["success"]:
            jobs = result["results"]
            return [self.format_job_listing(job) for job in jobs[:limit]]
        else:
            return []
    
    def get_job_statistics(
        self,
        keywords: str,
        location: str = "India"
    ) -> Dict:
        """
        Get job market statistics.
        
        Args:
            keywords: Job keywords
            location: Location
            
        Returns:
            Dictionary with statistics
        """
        result = self.search_jobs(keywords=keywords, location=location, results_per_page=1)
        
        if result["success"]:
            return {
                "total_jobs": result["count"],
                "location": location,
                "keywords": keywords,
                "last_updated": datetime.now().isoformat()
            }
        else:
            return {
                "error": result.get("error", "Unknown error"),
                "total_jobs": 0
            }

