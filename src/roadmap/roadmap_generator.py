"""Learning roadmap generator - creates personalized learning paths."""

from typing import List, Dict, Optional
from src.models.analysis_result import LearningPath, SkillGap
from src.models.job_role import JobRole


class RoadmapGenerator:
    """Generate personalized learning roadmaps."""
    
    def __init__(self, default_timeline_days: int = 90):
        """
        Initialize roadmap generator.
        
        Args:
            default_timeline_days: Default timeline for roadmap in days
        """
        self.default_timeline_days = default_timeline_days
        
        # Learning resource mappings (can be loaded from external file)
        self.learning_resources = self._load_default_resources()
    
    def generate_roadmap(
        self,
        skill_gaps: List[SkillGap],
        prioritize_by_importance: bool = True
    ) -> List[LearningPath]:
        """
        Generate learning roadmap from skill gaps.
        
        Args:
            skill_gaps: List of skill gaps to address
            prioritize_by_importance: Whether to prioritize by importance
            
        Returns:
            List of LearningPath objects
        """
        if not skill_gaps:
            return []
        
        # Sort gaps by priority
        if prioritize_by_importance:
            sorted_gaps = sorted(
                skill_gaps,
                key=lambda x: (0 if x.category == 'required' else 1, -x.importance),
                reverse=False
            )
        else:
            sorted_gaps = skill_gaps
        
        roadmap_items = []
        
        for idx, gap in enumerate(sorted_gaps, 1):
            # Estimate days needed (simple heuristic)
            estimated_days = self._estimate_learning_days(gap.skill, gap.category)
            
            # Get learning resources
            resources = self._get_learning_resources(gap.skill)
            if gap.learning_resources:
                resources.extend(gap.learning_resources)
            
            # Determine prerequisites
            prerequisites = self._get_prerequisites(gap.skill)
            
            roadmap_item = LearningPath(
                skill=gap.skill,
                priority=idx,
                estimated_days=estimated_days,
                resources=resources,
                prerequisites=prerequisites,
            )
            
            roadmap_items.append(roadmap_item)
        
        return roadmap_items
    
    def _estimate_learning_days(self, skill: str, category: str) -> int:
        """
        Estimate number of days needed to learn a skill.
        
        Simple heuristic - can be enhanced with ML or data.
        """
        # Required skills typically need more time
        base_days = 14 if category == 'required' else 7
        
        # Adjust based on skill complexity (simple keyword matching)
        skill_lower = skill.lower()
        
        if any(term in skill_lower for term in ['deep learning', 'neural network', 'transformer']):
            return base_days * 3
        elif any(term in skill_lower for term in ['machine learning', 'data science', 'nlp']):
            return base_days * 2
        elif any(term in skill_lower for term in ['cloud', 'aws', 'azure', 'gcp']):
            return base_days * 2
        else:
            return base_days
    
    def _get_learning_resources(self, skill: str) -> List[str]:
        """Get learning resources for a skill."""
        skill_lower = skill.lower()
        
        # Check if we have specific resources
        if skill in self.learning_resources:
            return self.learning_resources[skill]
        
        # Generic resources based on skill type
        if any(term in skill_lower for term in ['python', 'programming', 'coding']):
            return [
                "Python Official Documentation",
                "Python for Data Science (Coursera)",
                "Python Crash Course (Book)",
            ]
        elif any(term in skill_lower for term in ['machine learning', 'ml']):
            return [
                "Machine Learning Course by Andrew Ng (Coursera)",
                "Scikit-learn Documentation",
                "Hands-On Machine Learning (Book)",
            ]
        elif any(term in skill_lower for term in ['deep learning', 'neural network']):
            return [
                "Deep Learning Specialization (Coursera)",
                "Fast.ai Practical Deep Learning",
                "Deep Learning Book by Ian Goodfellow",
            ]
        elif any(term in skill_lower for term in ['tensorflow', 'keras']):
            return [
                "TensorFlow Official Tutorials",
                "TensorFlow Developer Certificate",
                "Deep Learning with TensorFlow (Course)",
            ]
        elif any(term in skill_lower for term in ['pytorch']):
            return [
                "PyTorch Official Tutorials",
                "Deep Learning with PyTorch (Course)",
            ]
        elif any(term in skill_lower for term in ['aws', 'cloud']):
            return [
                "AWS Certified Solutions Architect",
                "AWS Free Tier (Hands-on Practice)",
                "AWS Documentation",
            ]
        else:
            return [
                f"Search for '{skill}' tutorials on Coursera/edX",
                f"Read documentation for {skill}",
                f"Practice {skill} with hands-on projects",
            ]
    
    def _get_prerequisites(self, skill: str) -> List[str]:
        """Get prerequisite skills."""
        skill_lower = skill.lower()
        
        prerequisites = []
        
        # Common prerequisites
        if any(term in skill_lower for term in ['machine learning', 'deep learning', 'tensorflow', 'pytorch']):
            prerequisites.append('Python')
            prerequisites.append('Mathematics/Statistics')
        
        if any(term in skill_lower for term in ['deep learning', 'neural network']):
            prerequisites.append('Machine Learning')
            prerequisites.append('Linear Algebra')
        
        if any(term in skill_lower for term in ['data science', 'data analysis']):
            prerequisites.append('Python')
            prerequisites.append('SQL')
            prerequisites.append('Statistics')
        
        if any(term in skill_lower for term in ['aws', 'azure', 'gcp', 'cloud']):
            prerequisites.append('Linux/Command Line')
            prerequisites.append('Networking Basics')
        
        return prerequisites
    
    def _load_default_resources(self) -> Dict[str, List[str]]:
        """Load default learning resources."""
        # This can be loaded from a JSON/YAML file
        return {
            # Add specific skill-resource mappings here
        }
    
    def create_timeline(self, roadmap_items: List[LearningPath], total_days: Optional[int] = None) -> Dict:
        """
        Create a timeline from roadmap items.
        
        Args:
            roadmap_items: List of learning paths
            total_days: Total timeline days (if None, uses sum of estimates)
            
        Returns:
            Dictionary with timeline breakdown
        """
        if total_days is None:
            total_days = sum(item.estimated_days for item in roadmap_items)
        
        timeline = {
            'total_days': total_days,
            'weeks': round(total_days / 7, 1),
            'months': round(total_days / 30, 1),
            'items': [
                {
                    'skill': item.skill,
                    'priority': item.priority,
                    'days': item.estimated_days,
                    'resources': item.resources[:3],  # Top 3 resources
                }
                for item in roadmap_items
            ]
        }
        
        return timeline

