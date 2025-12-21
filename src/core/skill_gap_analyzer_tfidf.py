"""
Skill Gap Analyzer using TF-IDF + Cosine Similarity

This module analyzes skill gaps between resume skills and job role requirements
using TF-IDF vectorization and cosine similarity for better matching.

How it works:
1. Converts skills to TF-IDF vectors
2. Calculates cosine similarity between resume and job role skills
3. Identifies matched, missing, and extra skills
4. Explains why skills are marked as missing
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SkillGapAnalyzerTFIDF:
    """
    Skill Gap Analyzer using TF-IDF and Cosine Similarity.
    
    This analyzer provides more sophisticated skill matching compared to
    simple string matching by considering semantic similarity.
    """
    
    def __init__(self, similarity_threshold: float = 0.3):
        """
        Initialize the TF-IDF-based skill gap analyzer.
        
        Args:
            similarity_threshold: Minimum cosine similarity (0-1) to consider skills as matched.
                                 Lower values = more lenient matching (default: 0.3)
        """
        self.similarity_threshold = similarity_threshold
        self.vectorizer = None
        self._explanation_cache = {}  # Cache for explanations
    
    def analyze_gaps(
        self,
        resume_skills: List[str],
        job_role_skills: List[str],
        required_skills: Optional[List[str]] = None,
        preferred_skills: Optional[List[str]] = None
    ) -> Dict:
        """
        Analyze skill gaps between resume and job role.
        
        How it works:
        1. Creates TF-IDF vectors for all skills
        2. Calculates cosine similarity between resume and job skills
        3. Matches skills above similarity threshold
        4. Identifies missing and extra skills
        5. Provides explanations
        
        Args:
            resume_skills: List of skills from resume
            job_role_skills: List of all skills required for job role
            required_skills: List of required skills (if None, all job_role_skills are treated as required)
            preferred_skills: List of preferred/optional skills
            
        Returns:
            Dictionary with:
            - matched_skills: List of matched skill pairs (resume_skill, job_skill, similarity)
            - missing_skills: List of job skills not found in resume
            - extra_skills: List of resume skills not needed for job
            - match_details: Detailed matching information
            - explanations: Why skills are marked as missing
        """
        if not resume_skills or not job_role_skills:
            return {
                'matched_skills': [],
                'missing_skills': job_role_skills if job_role_skills else [],
                'extra_skills': resume_skills if resume_skills else [],
                'match_details': {},
                'explanations': {}
            }
        
        # Determine required vs preferred
        if required_skills is None:
            required_skills = job_role_skills
            preferred_skills = []
        
        if preferred_skills is None:
            preferred_skills = []
        
        # Step 1: Prepare skill lists for vectorization
        all_skills = resume_skills + job_role_skills
        unique_skills = list(set(all_skills))
        
        # Step 2: Create TF-IDF vectors
        # TF-IDF converts text to numerical vectors based on term frequency and inverse document frequency
        self.vectorizer = TfidfVectorizer(
            lowercase=True,      # Convert to lowercase
            analyzer='word',      # Analyze by words
            ngram_range=(1, 2),   # Use 1-grams and 2-grams (e.g., "machine learning")
            token_pattern=r'\b[a-zA-Z][a-zA-Z0-9]*\b',  # Token pattern for skills
            min_df=1,            # Minimum document frequency
            max_df=1.0           # Maximum document frequency
        )
        
        # Create vectors for each skill individually
        # Each skill is treated as a separate "document"
        skill_vectors = self.vectorizer.fit_transform(unique_skills)
        
        # Get vectors for resume and job skills
        resume_indices = [unique_skills.index(s) for s in resume_skills if s in unique_skills]
        job_indices = [unique_skills.index(s) for s in job_role_skills if s in unique_skills]
        
        resume_vectors = skill_vectors[resume_indices] if resume_indices else None
        job_vectors = skill_vectors[job_indices] if job_indices else None
        
        # Step 3: Calculate cosine similarity
        # Cosine similarity measures the angle between two vectors
        # Range: -1 to 1 (1 = identical, 0 = orthogonal, -1 = opposite)
        if resume_vectors is not None and job_vectors is not None:
            similarity_matrix = cosine_similarity(resume_vectors, job_vectors)
        else:
            similarity_matrix = np.zeros((len(resume_skills), len(job_role_skills)))
        
        # Step 4: Find matches
        matched_skills, job_matched_indices = self._find_matches(
            resume_skills, job_role_skills, similarity_matrix
        )
        
        # Step 5: Identify missing skills (job skills not matched)
        missing_skills = [
            job_role_skills[i] for i in range(len(job_role_skills))
            if i not in job_matched_indices
        ]
        
        # Step 6: Identify extra skills (resume skills not matched)
        resume_matched_indices = [m['resume_index'] for m in matched_skills]
        extra_skills = [
            resume_skills[i] for i in range(len(resume_skills))
            if i not in resume_matched_indices
        ]
        
        # Step 7: Categorize missing skills (required vs preferred)
        missing_required = [s for s in missing_skills if s in required_skills]
        missing_preferred = [s for s in missing_skills if s in preferred_skills]
        
        # Step 8: Generate explanations
        explanations = self._generate_explanations(
            matched_skills, missing_skills, extra_skills,
            resume_skills, job_role_skills, similarity_matrix
        )
        
        # Step 9: Calculate statistics
        match_details = {
            'total_resume_skills': len(resume_skills),
            'total_job_skills': len(job_role_skills),
            'matched_count': len(matched_skills),
            'missing_count': len(missing_skills),
            'extra_count': len(extra_skills),
            'match_percentage': (len(matched_skills) / len(job_role_skills) * 100) if job_role_skills else 0,
            'average_similarity': np.mean([m['similarity'] for m in matched_skills]) if matched_skills else 0,
        }
        
        return {
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'missing_required': missing_required,
            'missing_preferred': missing_preferred,
            'extra_skills': extra_skills,
            'match_details': match_details,
            'explanations': explanations,
            'similarity_matrix': similarity_matrix.tolist(),  # For debugging
        }
    
    def _find_matches(
        self,
        resume_skills: List[str],
        job_role_skills: List[str],
        similarity_matrix: np.ndarray
    ) -> Tuple[List[Dict], List[int]]:
        """
        Find matched skills based on cosine similarity.
        
        Uses greedy matching: each job skill is matched to the resume skill
        with highest similarity above threshold.
        
        Args:
            resume_skills: List of resume skills
            job_role_skills: List of job role skills
            similarity_matrix: Cosine similarity matrix (resume_skills x job_role_skills)
            
        Returns:
            Tuple of (matched skills list, matched job skill indices)
        """
        matched_skills = []
        job_matched_indices = set()
        resume_matched_indices = set()
        
        # Create list of all potential matches with similarities
        potential_matches = []
        for i, resume_skill in enumerate(resume_skills):
            for j, job_skill in enumerate(job_role_skills):
                similarity = float(similarity_matrix[i][j])
                if similarity >= self.similarity_threshold:
                    potential_matches.append({
                        'resume_index': i,
                        'job_index': j,
                        'resume_skill': resume_skill,
                        'job_skill': job_skill,
                        'similarity': similarity
                    })
        
        # Sort by similarity (highest first)
        potential_matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Greedy matching: assign best matches first
        for match in potential_matches:
            if (match['resume_index'] not in resume_matched_indices and
                match['job_index'] not in job_matched_indices):
                
                matched_skills.append({
                    'resume_skill': match['resume_skill'],
                    'job_skill': match['job_skill'],
                    'similarity': match['similarity'],
                    'resume_index': match['resume_index'],
                    'job_index': match['job_index']
                })
                
                resume_matched_indices.add(match['resume_index'])
                job_matched_indices.add(match['job_index'])
        
        return matched_skills, list(job_matched_indices)
    
    def _generate_explanations(
        self,
        matched_skills: List[Dict],
        missing_skills: List[str],
        extra_skills: List[str],
        resume_skills: List[str],
        job_role_skills: List[str],
        similarity_matrix: np.ndarray
    ) -> Dict[str, str]:
        """
        Generate explanations for why skills are marked as missing.
        
        Args:
            matched_skills: List of matched skills
            missing_skills: List of missing skills
            extra_skills: List of extra skills
            resume_skills: Original resume skills
            job_role_skills: Original job role skills
            similarity_matrix: Similarity matrix for reference
            
        Returns:
            Dictionary of explanations
        """
        explanations = {}
        
        # Explain missing skills
        for missing_skill in missing_skills:
            job_index = job_role_skills.index(missing_skill)
            
            # Find closest resume skill (highest similarity)
            max_similarity = 0
            closest_resume_skill = None
            
            for i, resume_skill in enumerate(resume_skills):
                similarity = float(similarity_matrix[i][job_index])
                if similarity > max_similarity:
                    max_similarity = similarity
                    closest_resume_skill = resume_skill
            
            # Generate explanation
            if max_similarity < self.similarity_threshold:
                if closest_resume_skill:
                    explanations[missing_skill] = (
                        f"Skill '{missing_skill}' is marked as missing because "
                        f"no resume skill matches it closely enough. "
                        f"The closest match is '{closest_resume_skill}' with similarity {max_similarity:.2f}, "
                        f"which is below the threshold of {self.similarity_threshold}. "
                        f"This means the resume lacks this specific skill or a very similar one."
                    )
                else:
                    explanations[missing_skill] = (
                        f"Skill '{missing_skill}' is marked as missing because "
                        f"it does not appear in the resume at all, and no similar skills were found."
                    )
            else:
                # Shouldn't happen, but handle edge case
                explanations[missing_skill] = (
                    f"Skill '{missing_skill}' is marked as missing due to matching algorithm constraints."
                )
        
        return explanations
    
    def explain_similarity_calculation(self) -> str:
        """
        Explain how cosine similarity is calculated.
        
        Returns:
            Human-readable explanation of the similarity calculation process
        """
        explanation = """
HOW COSINE SIMILARITY WORKS:

1. TF-IDF Vectorization:
   - Each skill is converted to a numerical vector
   - TF (Term Frequency): How often words appear in the skill
   - IDF (Inverse Document Frequency): How rare/common words are across all skills
   - TF-IDF = TF × IDF (higher for important, rare terms)

2. Vector Representation:
   - Skills with similar words get similar vectors
   - Example: "Machine Learning" and "ML" share "Machine" → similar vectors
   - Example: "Python" and "Java" → different vectors (no shared words)

3. Cosine Similarity:
   - Measures the angle between two vectors
   - Formula: cos(θ) = (A · B) / (||A|| × ||B||)
   - Range: -1 to 1
     * 1.0 = Identical or very similar (same angle/direction)
     * 0.0 = Orthogonal (completely different)
     * -1.0 = Opposite (unlikely for skills)

4. Matching Decision:
   - If similarity ≥ threshold (default 0.3) → Skills match
   - If similarity < threshold → Skills don't match

5. Why Skills are Marked Missing:
   - No resume skill has similarity ≥ threshold with the job skill
   - This means the resume lacks that specific skill or anything similar enough

EXAMPLE:
  Job Skill: "Machine Learning"
  Resume Skill: "ML"
  
  Step 1: TF-IDF vectors created for both
  Step 2: Cosine similarity calculated (likely ~0.7-0.9)
  Step 3: Since 0.7 > 0.3 (threshold) → MATCH!
  
  Job Skill: "TensorFlow"
  Resume Skill: "Python"
  
  Step 1: TF-IDF vectors created (different words)
  Step 2: Cosine similarity calculated (likely ~0.1-0.2)
  Step 3: Since 0.2 < 0.3 (threshold) → NO MATCH → Missing!
"""
        return explanation.strip()
    
    def get_similarity_between_skills(self, skill1: str, skill2: str) -> float:
        """
        Calculate cosine similarity between two skills.
        
        Useful for testing and understanding individual skill similarities.
        
        Args:
            skill1: First skill
            skill2: Second skill
            
        Returns:
            Cosine similarity score (0-1)
        """
        if not skill1 or not skill2:
            return 0.0
        
        # Create vectorizer
        vectorizer = TfidfVectorizer(
            lowercase=True,
            analyzer='word',
            ngram_range=(1, 2),
            token_pattern=r'\b[a-zA-Z][a-zA-Z0-9]*\b',
        )
        
        # Vectorize
        try:
            vectors = vectorizer.fit_transform([skill1, skill2])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return float(similarity)
        except Exception:
            return 0.0

