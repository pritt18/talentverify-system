from typing import Dict, Any, Tuple
import re
from difflib import SequenceMatcher

def string_similarity(a: str, b: str) -> float:
    """Returns ratio between 0.0 and 1.0 comparing two strings."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

def token_overlap(text_a: str, text_b: str) -> float:
    """Calculates Jaccard similarity between words of two texts."""
    words_a = set(re.findall(r'\b[a-zA-Z]{3,}\b', text_a.lower()))
    words_b = set(re.findall(r'\b[a-zA-Z]{3,}\b', text_b.lower()))
    if not words_a or not words_b:
        return 0.0
    overlap = words_a.intersection(words_b)
    return len(overlap) / min(len(words_a), len(words_b))

def cross_check_cv_and_linkedin(cv_data: Dict[str, Any], linkedin_data: Dict[str, Any]) -> Tuple[str, int, str]:
    """
    Cross-checks extracted CV details with scraped LinkedIn profile.
    
    Returns:
    - match_status: 'Matched with LinkedIn profile' OR 'LinkedIn profile doesn\'t match'
    - match_score: 0 - 100
    - match_reason: Multi-point verification explanation
    """
    if not cv_data.get("linkedin_url") or cv_data["linkedin_url"] == "N/A":
        return ("LinkedIn profile doesn't match", 0, "No LinkedIn profile found in the uploaded CV.")

    if not linkedin_data or not linkedin_data.get("name"):
        return ("LinkedIn profile doesn't match", 10, "Failed to retrieve or verify LinkedIn profile information.")

    cv_name = cv_data.get("name", "").strip()
    li_name = linkedin_data.get("name", "").strip()

    # 1. Name Check
    name_sim = string_similarity(cv_name, li_name)
    name_matched = name_sim >= 0.70 or (cv_name.lower() in li_name.lower()) or (li_name.lower() in cv_name.lower())

    # 2. Professional / Experience Check
    cv_exp = (cv_data.get("experiences", "") + " " + cv_data.get("professional_background", "")).lower()
    li_exp = (linkedin_data.get("experience", "") + " " + linkedin_data.get("headline", "") + " " + linkedin_data.get("current_company", "")).lower()
    exp_overlap = token_overlap(cv_exp, li_exp)
    exp_matched = exp_overlap >= 0.15

    # 3. Education Check
    cv_edu = cv_data.get("educational_background", "").lower()
    li_edu = linkedin_data.get("education", "").lower()
    edu_overlap = token_overlap(cv_edu, li_edu)
    edu_matched = edu_overlap >= 0.15

    # 4. Skills Check
    cv_skills = cv_data.get("skills", "").lower()
    li_skills = " ".join(linkedin_data.get("skills", [])).lower()
    skills_overlap = token_overlap(cv_skills, li_skills)
    skills_matched = skills_overlap >= 0.15

    # Scoring breakdown (Max 100)
    score = 0
    reasons = []

    if name_matched:
        score += 45
        reasons.append(f"Name Match: CV name '{cv_name}' matches LinkedIn name '{li_name}' (similarity: {int(name_sim*100)}%).")
    else:
        reasons.append(f"Name Mismatch: CV name '{cv_name}' differs significantly from LinkedIn name '{li_name}'.")

    if exp_matched:
        score += 25
        reasons.append(f"Experience Match: Overlapping professional background and company history.")
    else:
        reasons.append("Experience Mismatch: No significant company or job role overlap detected.")

    if edu_matched:
        score += 15
        reasons.append(f"Education Match: Degree / institution records correspond.")
    else:
        reasons.append("Education: Minimal university / institution overlap.")

    if skills_matched:
        score += 15
        reasons.append("Skills Match: Strong alignment in core technologies.")
    else:
        reasons.append("Skills: Disjoint technology competencies.")

    # Strict Final Decision
    # To declare "Matched with LinkedIn profile", candidate name MUST match AND at least 2 other dimensions (score >= 60)
    if name_matched and score >= 60:
        status = "Matched with LinkedIn profile"
    else:
        status = "LinkedIn profile doesn't match"

    full_reason = f"Overall verification score: {score}/100.\n" + "\n".join(f"- {r}" for r in reasons)
    return status, score, full_reason

if __name__ == "__main__":
    cv = {
        "name": "Pritam Gangurde",
        "email": "pritamgangurde18@gmail.com",
        "linkedin_url": "https://www.linkedin.com/in/pritam-gangurde",
        "educational_background": "Late Sau KBJ College of Engineering, Nashik, Bachelor of Engineering",
        "professional_background": "Software Engineer & Full Stack Developer",
        "experiences": "SoftSpire Solutions Full Stack Developer Intern Python React",
        "skills": "Python, Java, React.js, MySQL, Docker"
    }

    li_matched = {
        "name": "Pritam Gangurde",
        "headline": "Software Engineer | Full Stack Developer",
        "current_company": "SoftSpire Solutions",
        "education": "Late Sau KBJ College of Engineering, Nashik",
        "experience": "Full Stack Developer at SoftSpire Solutions",
        "skills": ["Python", "JavaScript", "React.js", "MySQL"]
    }

    li_mismatched = {
        "name": "John Alexander Doe",
        "headline": "Senior Investment Banker at Goldman Sachs",
        "current_company": "Goldman Sachs",
        "education": "Harvard Business School",
        "experience": "Private equity analyst",
        "skills": ["Corporate Finance", "M&A"]
    }

    print("--- Test 1: MATCH SCENARIO ---")
    st1, sc1, r1 = cross_check_cv_and_linkedin(cv, li_matched)
    print(f"Status: {st1} | Score: {sc1}\nReason: {r1}\n")

    print("--- Test 2: MISMATCH SCENARIO ---")
    st2, sc2, r2 = cross_check_cv_and_linkedin(cv, li_mismatched)
    print(f"Status: {st2} | Score: {sc2}\nReason: {r2}\n")
