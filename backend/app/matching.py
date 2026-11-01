"""
Auto-matching & scoring algorithm
Score = 0.40 * skill_overlap (Jaccard) + 0.35 * experience_fit + 0.25 * other_factors
"""
from typing import Dict, List, Optional


def calculate_skill_overlap(cv_skills: List[str], job_skills: List[str]) -> float:
    """Calculate Jaccard similarity between CV skills and job required skills"""
    if not job_skills:
        return 0.5  # Neutral score if no skills specified
    
    cv_set = set(s.lower() for s in cv_skills)
    job_set = set(s.lower() for s in job_skills)
    
    intersection = cv_set.intersection(job_set)
    union = cv_set.union(job_set)
    
    if not union:
        return 0.5
    
    return len(intersection) / len(union)


def calculate_experience_fit(cv_experience: float, job_required: float) -> float:
    """
    Calculate how well candidate's experience matches job requirement
    Returns value between 0 and 1
    """
    if job_required <= 0:
        return 1.0  # No experience required
    
    # If candidate has more than required, cap at 1.0
    # If less, proportional score
    return min(cv_experience / job_required, 1.0)


def calculate_location_match(cv_location: str, job_location: str) -> float:
    """Simple location match score"""
    if not job_location:
        return 1.0
    
    if not cv_location:
        return 0.5
    
    # Exact match or contains
    if cv_location.lower() == job_location.lower():
        return 1.0
    
    if cv_location.lower() in job_location.lower() or job_location.lower() in cv_location.lower():
        return 0.8
    
    return 0.3


def calculate_match_score(
    cv_data: Dict,
    job_data: Dict
) -> tuple[float, Dict]:
    """
    Calculate overall match score between CV and job
    
    Args:
        cv_data: Dict with keys: skills, experience_years, location, etc.
        job_data: Dict with keys: skills_required, experience_years, location, etc.
    
    Returns:
        Tuple of (total_score, match_reason_dict)
    """
    # Extract data
    cv_skills = cv_data.get('skills', [])
    job_skills = job_data.get('skills_required', [])
    cv_exp = cv_data.get('experience_years', 0)
    job_exp = job_data.get('experience_years', 0)
    cv_loc = cv_data.get('location', '')
    job_loc = job_data.get('location', '')
    
    # Calculate component scores
    skill_score = calculate_skill_overlap(cv_skills, job_skills)
    exp_score = calculate_experience_fit(cv_exp, job_exp)
    location_score = calculate_location_match(cv_loc, job_loc)
    
    # Weighted sum
    total_score = (0.40 * skill_score) + (0.35 * exp_score) + (0.25 * location_score)
    
    # Generate explanation
    cv_skills_lower = [s.lower() for s in cv_skills]
    job_skills_lower = [s.lower() for s in job_skills]
    
    matched_skills = [s for s in cv_skills if s.lower() in job_skills_lower]
    missing_skills = [s for s in job_skills if s.lower() not in cv_skills_lower]
    
    match_reason = {
        'score': round(total_score, 2),
        'skill_score': round(skill_score, 2),
        'experience_score': round(exp_score, 2),
        'location_score': round(location_score, 2),
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'experience_gap': max(0, job_exp - cv_exp),
        'recommendation': get_recommendation(total_score)
    }
    
    return round(total_score, 2), match_reason


def get_recommendation(score: float) -> str:
    """Get recommendation text based on score"""
    if score >= 0.75:
        return "Rất phù hợp"
    elif score >= 0.60:
        return "Phù hợp"
    elif score >= 0.45:
        return "Có thể cân nhắc"
    else:
        return "Ít phù hợp"


def recommend_jobs_for_user(
    user_profile: Dict,
    all_jobs: List[Dict],
    top_k: int = 10
) -> List[tuple[Dict, float]]:
    """
    Recommend jobs for a user based on their profile
    
    Args:
        user_profile: User's aggregated profile (skills from CV, applications, etc.)
        all_jobs: List of all active jobs
        top_k: Number of recommendations to return
    
    Returns:
        List of (job, score) tuples sorted by score descending
    """
    scored_jobs = []
    
    for job in all_jobs:
        if job.get('status') != 'active':
            continue
        
        score, reason = calculate_match_score(user_profile, job)
        
        # Only include jobs with reasonable match
        if score >= 0.45:
            job_with_reason = {**job, 'match_score': score, 'match_reason': reason}
            scored_jobs.append((job_with_reason, score))
    
    # Sort by score descending
    scored_jobs.sort(key=lambda x: x[1], reverse=True)
    
    # Return top_k
    return scored_jobs[:top_k]
