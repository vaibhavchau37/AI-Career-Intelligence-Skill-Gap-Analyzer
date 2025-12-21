"""
Role Suitability Predictor

Predicts best-fit roles and identifies not suitable roles with reasons.
"""

from typing import List, Dict, Optional
from src.models.job_role import JobRole


class RoleSuitabilityPredictor:
    """
    Predict role suitability based on readiness scores and skill gaps.
    
    Provides:
    - Best-fit roles (ranked)
    - Not suitable roles with specific reasons
    """
    
    def __init__(self, suitability_threshold: float = 50.0):
        """
        Initialize role suitability predictor.
        
        Args:
            suitability_threshold: Minimum score to consider role suitable (default: 50)
        """
        self.suitability_threshold = suitability_threshold
    
    def predict_suitability(
        self,
        readiness_scores: Dict[str, float],
        skill_gaps: Dict[str, Dict],
        role_descriptions: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Predict role suitability based on readiness scores and skill gaps.
        
        Args:
            readiness_scores: Dictionary mapping role names to readiness scores (0-100)
            skill_gaps: Dictionary mapping role names to skill gap analysis results
            role_descriptions: Optional dictionary of role descriptions
            
        Returns:
            Dictionary with:
            - best_fit_roles: List of ranked suitable roles
            - not_suitable_roles: List of roles with reasons
            - recommendations: Overall recommendations
        """
        best_fit_roles = []
        not_suitable_roles = []
        
        # Sort roles by readiness score
        sorted_roles = sorted(
            readiness_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for role_name, score in sorted_roles:
            gap_info = skill_gaps.get(role_name, {})
            missing_required = gap_info.get('missing_required', [])
            missing_preferred = gap_info.get('missing_preferred', [])
            match_details = gap_info.get('match_details', {})
            
            # Determine suitability
            if score >= self.suitability_threshold:
                # Suitable role
                reasons = self._generate_suitability_reasons(
                    role_name, score, missing_required, missing_preferred, match_details
                )
                best_fit_roles.append({
                    'role_name': role_name,
                    'readiness_score': score,
                    'reasons': reasons,
                    'description': role_descriptions.get(role_name, '') if role_descriptions else ''
                })
            else:
                # Not suitable - generate reasons
                reasons = self._generate_unsuitability_reasons(
                    role_name, score, missing_required, missing_preferred, match_details
                )
                not_suitable_roles.append({
                    'role_name': role_name,
                    'readiness_score': score,
                    'reasons': reasons,
                    'description': role_descriptions.get(role_name, '') if role_descriptions else ''
                })
        
        # Generate overall recommendations
        recommendations = self._generate_recommendations(best_fit_roles, not_suitable_roles)
        
        return {
            'best_fit_roles': best_fit_roles,
            'not_suitable_roles': not_suitable_roles,
            'recommendations': recommendations
        }
    
    def _generate_suitability_reasons(
        self,
        role_name: str,
        score: float,
        missing_required: List[str],
        missing_preferred: List[str],
        match_details: Dict
    ) -> List[str]:
        """Generate reasons why a role is suitable."""
        reasons = []
        
        if score >= 80:
            reasons.append(f"Excellent readiness score ({score:.1f}/100)")
        elif score >= 65:
            reasons.append(f"Good readiness score ({score:.1f}/100)")
        else:
            reasons.append(f"Moderate readiness score ({score:.1f}/100)")
        
        match_pct = match_details.get('match_percentage', 0)
        if match_pct >= 80:
            reasons.append(f"Strong skill match ({match_pct:.1f}% of required skills)")
        elif match_pct >= 60:
            reasons.append(f"Good skill match ({match_pct:.1f}% of required skills)")
        
        if not missing_required:
            reasons.append("All required skills are present")
        elif len(missing_required) <= 2:
            reasons.append(f"Only {len(missing_required)} required skill(s) missing")
        
        matched_count = match_details.get('matched_count', 0)
        if matched_count > 0:
            reasons.append(f"{matched_count} skills matched successfully")
        
        return reasons
    
    def _generate_unsuitability_reasons(
        self,
        role_name: str,
        score: float,
        missing_required: List[str],
        missing_preferred: List[str],
        match_details: Dict
    ) -> List[str]:
        """Generate reasons why a role is not suitable."""
        reasons = []
        
        # Score-based reasons
        if score < 35:
            reasons.append(f"Very low readiness score ({score:.1f}/100)")
        else:
            reasons.append(f"Below threshold readiness score ({score:.1f}/100)")
        
        # Missing required skills
        if missing_required:
            if len(missing_required) >= 3:
                reasons.append(f"Missing {len(missing_required)} critical required skills")
                # List top 3 missing skills
                top_missing = missing_required[:3]
                reasons.append(f"Critical gaps: {', '.join(top_missing)}")
            else:
                reasons.append(f"Missing required skills: {', '.join(missing_required)}")
        
        # Low skill match
        match_pct = match_details.get('match_percentage', 0)
        if match_pct < 50:
            reasons.append(f"Low skill match ({match_pct:.1f}% of required skills)")
        
        # Specific skill gaps
        if "Deep Learning" in missing_required or "TensorFlow" in missing_required:
            reasons.append("Lacks deployment and advanced ML experience")
        
        if "Statistics" in missing_required:
            reasons.append("Missing statistical foundations")
        
        if "AWS" in missing_required or "Docker" in missing_required:
            reasons.append("Lacks cloud/deployment experience")
        
        # Generic reason if none specific
        if len(reasons) == 1:  # Only score reason
            reasons.append("Significant skill gaps need to be addressed")
        
        return reasons
    
    def _generate_recommendations(
        self,
        best_fit_roles: List[Dict],
        not_suitable_roles: List[Dict]
    ) -> List[str]:
        """Generate overall recommendations."""
        recommendations = []
        
        if best_fit_roles:
            top_role = best_fit_roles[0]
            recommendations.append(
                f"Best match: {top_role['role_name']} "
                f"(Readiness: {top_role['readiness_score']:.1f}/100)"
            )
            
            if len(best_fit_roles) > 1:
                recommendations.append(
                    f"Also consider: {', '.join([r['role_name'] for r in best_fit_roles[1:3]])}"
                )
        else:
            recommendations.append("No roles meet the suitability threshold")
            recommendations.append("Focus on building core skills before targeting specific roles")
        
        if not_suitable_roles:
            top_unsuitable = not_suitable_roles[0]
            recommendations.append(
                f"Not recommended: {top_unsuitable['role_name']} - "
                f"{top_unsuitable['reasons'][0]}"
            )
        
        return recommendations

