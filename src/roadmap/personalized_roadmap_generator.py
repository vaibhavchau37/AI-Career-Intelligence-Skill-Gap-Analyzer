"""
Personalized Learning Roadmap Generator

Creates 30-day learning roadmaps with practical tasks to close skill gaps.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from src.models.analysis_result import LearningPath


class PersonalizedRoadmapGenerator:
    """
    Generate personalized 30-day learning roadmaps.
    
    Focuses on practical tasks rather than long courses.
    """
    
    def __init__(self, roadmap_days: int = 30):
        """
        Initialize roadmap generator.
        
        Args:
            roadmap_days: Number of days for roadmap (default: 30)
        """
        self.roadmap_days = roadmap_days
        self.skill_tasks = self._load_skill_tasks()
    
    def generate_roadmap(
        self,
        missing_skills: List[str],
        target_role: str,
        required_skills: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate 30-day personalized learning roadmap.
        
        Args:
            missing_skills: List of missing skills to learn
            target_role: Target job role name
            required_skills: List of all required skills (for prioritization)
            
        Returns:
            Dictionary with:
            - roadmap: List of daily/weekly tasks
            - skill_plans: Skill-wise learning plans
            - timeline: Day-by-day breakdown
            - summary: Roadmap summary
        """
        # Prioritize skills (required first)
        if required_skills:
            prioritized_skills = self._prioritize_skills(missing_skills, required_skills)
        else:
            prioritized_skills = missing_skills
        
        # Generate skill-wise plans
        skill_plans = []
        total_days_allocated = 0
        
        for skill in prioritized_skills:
            if total_days_allocated >= self.roadmap_days:
                break
            
            # Estimate days needed (max 7 days per skill for 30-day roadmap)
            days_needed = min(7, self._estimate_skill_days(skill))
            remaining_days = self.roadmap_days - total_days_allocated
            
            if days_needed > remaining_days:
                days_needed = remaining_days
            
            skill_plan = self._create_skill_plan(skill, days_needed, total_days_allocated + 1)
            skill_plans.append(skill_plan)
            total_days_allocated += days_needed
        
        # Create day-by-day timeline
        timeline = self._create_timeline(skill_plans)
        
        # Generate summary
        summary = self._generate_summary(skill_plans, target_role)
        
        return {
            'target_role': target_role,
            'roadmap_days': self.roadmap_days,
            'skill_plans': skill_plans,
            'timeline': timeline,
            'summary': summary,
            'total_skills': len(skill_plans),
            'estimated_completion': (datetime.now() + timedelta(days=self.roadmap_days)).strftime("%Y-%m-%d")
        }
    
    def _prioritize_skills(
        self,
        missing_skills: List[str],
        required_skills: List[str]
    ) -> List[str]:
        """Prioritize skills: required skills first."""
        required_missing = [s for s in missing_skills if s in required_skills]
        preferred_missing = [s for s in missing_skills if s not in required_skills]
        return required_missing + preferred_missing
    
    def _estimate_skill_days(self, skill: str) -> int:
        """Estimate days needed to learn a skill."""
        skill_lower = skill.lower()
        
        # Simple estimation based on skill complexity
        if any(term in skill_lower for term in ['deep learning', 'neural network', 'transformer']):
            return 7
        elif any(term in skill_lower for term in ['machine learning', 'tensorflow', 'pytorch']):
            return 5
        elif any(term in skill_lower for term in ['aws', 'docker', 'kubernetes', 'cloud']):
            return 4
        elif any(term in skill_lower for term in ['statistics', 'data analysis']):
            return 3
        else:
            return 3  # Default
    
    def _create_skill_plan(
        self,
        skill: str,
        days: int,
        start_day: int
    ) -> Dict:
        """Create a learning plan for a specific skill."""
        tasks = self._get_practical_tasks(skill, days)
        
        return {
            'skill': skill,
            'days': days,
            'start_day': start_day,
            'end_day': start_day + days - 1,
            'tasks': tasks,
            'resources': self._get_learning_resources(skill)
        }
    
    def _get_practical_tasks(self, skill: str, days: int) -> List[Dict]:
        """Get practical tasks for learning a skill."""
        skill_lower = skill.lower()
        
        # Get base tasks from skill_tasks dictionary
        base_tasks = self.skill_tasks.get(skill, [])
        
        if base_tasks:
            # Use predefined tasks, adjust for days
            tasks = base_tasks[:days]
            return tasks
        
        # Generate generic tasks based on skill type
        tasks = []
        
        if days >= 1:
            tasks.append({
                'day': 1,
                'task': f"Set up environment and complete '{skill}' tutorial",
                'type': 'setup'
            })
        
        if days >= 2:
            tasks.append({
                'day': 2,
                'task': f"Build a simple '{skill}' project (Hello World equivalent)",
                'type': 'practice'
            })
        
        if days >= 3:
            tasks.append({
                'day': 3,
                'task': f"Complete hands-on exercise: '{skill}' basics",
                'type': 'practice'
            })
        
        if days >= 4:
            tasks.append({
                'day': 4,
                'task': f"Build intermediate '{skill}' project",
                'type': 'project'
            })
        
        if days >= 5:
            tasks.append({
                'day': 5,
                'task': f"Practice advanced '{skill}' concepts",
                'type': 'practice'
            })
        
        if days >= 6:
            tasks.append({
                'day': 6,
                'task': f"Build portfolio project using '{skill}'",
                'type': 'project'
            })
        
        if days >= 7:
            tasks.append({
                'day': 7,
                'task': f"Review and document '{skill}' knowledge",
                'type': 'review'
            })
        
        return tasks[:days]
    
    def _get_learning_resources(self, skill: str) -> List[str]:
        """Get learning resources for a skill."""
        skill_lower = skill.lower()
        
        resources = []
        
        # Add official documentation
        if 'python' in skill_lower:
            resources.append("Python.org Official Tutorial")
        elif 'tensorflow' in skill_lower:
            resources.append("TensorFlow Official Tutorials")
        elif 'pytorch' in skill_lower:
            resources.append("PyTorch Official Tutorials")
        elif 'aws' in skill_lower:
            resources.append("AWS Free Tier (Hands-on Practice)")
        elif 'docker' in skill_lower:
            resources.append("Docker Official Getting Started Guide")
        
        # Add practice platforms
        if any(term in skill_lower for term in ['python', 'programming', 'coding']):
            resources.append("LeetCode / HackerRank (Practice Problems)")
        
        if any(term in skill_lower for term in ['machine learning', 'ml', 'data science']):
            resources.append("Kaggle Learn (Free Courses)")
        
        # Add generic resources
        resources.append(f"Search YouTube for '{skill} tutorial'")
        resources.append(f"Build a project using {skill}")
        
        return resources[:5]  # Top 5 resources
    
    def _create_timeline(self, skill_plans: List[Dict]) -> List[Dict]:
        """Create day-by-day timeline."""
        timeline = []
        
        for plan in skill_plans:
            for day in range(plan['start_day'], plan['end_day'] + 1):
                task_index = day - plan['start_day']
                if task_index < len(plan['tasks']):
                    task = plan['tasks'][task_index]
                    timeline.append({
                        'day': day,
                        'skill': plan['skill'],
                        'task': task['task'],
                        'type': task.get('type', 'practice')
                    })
        
        return timeline
    
    def _generate_summary(self, skill_plans: List[Dict], target_role: str) -> str:
        """Generate roadmap summary."""
        total_skills = len(skill_plans)
        total_days = sum(plan['days'] for plan in skill_plans)
        
        summary = f"""
30-Day Learning Roadmap for {target_role}

OVERVIEW:
- Target Role: {target_role}
- Skills to Learn: {total_skills}
- Timeline: {total_days} days
- Start Date: {datetime.now().strftime('%Y-%m-%d')}
- Completion Date: {(datetime.now() + timedelta(days=total_days)).strftime('%Y-%m-%d')}

SKILLS COVERED:
"""
        for i, plan in enumerate(skill_plans, 1):
            summary += f"{i}. {plan['skill']} ({plan['days']} days, Days {plan['start_day']}-{plan['end_day']})\n"
        
        summary += "\nAPPROACH:\n"
        summary += "- Focus on practical tasks and projects\n"
        summary += "- Learn by doing, not just watching\n"
        summary += "- Build portfolio projects to demonstrate skills\n"
        summary += "- Review and document your learning\n"
        
        return summary.strip()
    
    def _load_skill_tasks(self) -> Dict[str, List[Dict]]:
        """Load predefined practical tasks for common skills."""
        return {
            "Python": [
                {'day': 1, 'task': 'Install Python and set up IDE (VS Code/PyCharm)', 'type': 'setup'},
                {'day': 2, 'task': 'Complete Python basics tutorial (variables, loops, functions)', 'type': 'practice'},
                {'day': 3, 'task': 'Build a simple calculator or to-do list app', 'type': 'project'},
                {'day': 4, 'task': 'Learn file handling and data structures (lists, dicts)', 'type': 'practice'},
                {'day': 5, 'task': 'Build a data processing script (CSV/JSON)', 'type': 'project'},
            ],
            "Machine Learning": [
                {'day': 1, 'task': 'Set up ML environment (scikit-learn, pandas)', 'type': 'setup'},
                {'day': 2, 'task': 'Complete scikit-learn tutorial (linear regression)', 'type': 'practice'},
                {'day': 3, 'task': 'Build a simple prediction model (house prices)', 'type': 'project'},
                {'day': 4, 'task': 'Learn classification algorithms (logistic regression)', 'type': 'practice'},
                {'day': 5, 'task': 'Build a classification project (spam detection)', 'type': 'project'},
            ],
            "TensorFlow": [
                {'day': 1, 'task': 'Install TensorFlow and run first neural network', 'type': 'setup'},
                {'day': 2, 'task': 'Complete TensorFlow basics tutorial', 'type': 'practice'},
                {'day': 3, 'task': 'Build a simple image classifier (MNIST)', 'type': 'project'},
                {'day': 4, 'task': 'Learn CNN architecture and build custom model', 'type': 'practice'},
                {'day': 5, 'task': 'Deploy model using TensorFlow Serving', 'type': 'project'},
            ],
            "Deep Learning": [
                {'day': 1, 'task': 'Understand neural network basics (perceptron)', 'type': 'practice'},
                {'day': 2, 'task': 'Build a simple neural network from scratch', 'type': 'project'},
                {'day': 3, 'task': 'Learn backpropagation and gradient descent', 'type': 'practice'},
                {'day': 4, 'task': 'Build a deep neural network (3+ layers)', 'type': 'project'},
                {'day': 5, 'task': 'Learn about CNNs and RNNs', 'type': 'practice'},
                {'day': 6, 'task': 'Build a CNN for image classification', 'type': 'project'},
                {'day': 7, 'task': 'Build an RNN for text processing', 'type': 'project'},
            ],
            "AWS": [
                {'day': 1, 'task': 'Create AWS free tier account and explore console', 'type': 'setup'},
                {'day': 2, 'task': 'Launch EC2 instance and connect via SSH', 'type': 'practice'},
                {'day': 3, 'task': 'Set up S3 bucket and upload/download files', 'type': 'practice'},
                {'day': 4, 'task': 'Deploy a simple web app on EC2', 'type': 'project'},
            ],
            "Docker": [
                {'day': 1, 'task': 'Install Docker and run first container', 'type': 'setup'},
                {'day': 2, 'task': 'Create Dockerfile for a Python app', 'type': 'practice'},
                {'day': 3, 'task': 'Build and run containerized application', 'type': 'project'},
                {'day': 4, 'task': 'Learn Docker Compose for multi-container apps', 'type': 'practice'},
            ],
            "Statistics": [
                {'day': 1, 'task': 'Review basic statistics concepts (mean, median, std)', 'type': 'practice'},
                {'day': 2, 'task': 'Learn hypothesis testing (t-test, chi-square)', 'type': 'practice'},
                {'day': 3, 'task': 'Apply statistics to a real dataset', 'type': 'project'},
            ],
        }

