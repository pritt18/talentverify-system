import os
import sys
import pymysql

# Set paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from database.db_connection import (
    init_db,
    insert_candidate,
    update_candidate_match,
    get_candidate,
    get_all_candidates
)
from backend.cv_parser import extract_cv_data
from backend.linkedin_service import scrape_linkedin_profile
from backend.matcher import cross_check_cv_and_linkedin

def run_system_verification():
    print("================================================================")
    print("TALENTVERIFY - SYSTEM PIPELINE INTEGRATION VALIDATION")
    print("================================================================\n")

    # Step 1: Initialize DB
    print("[1/5] Verifying MySQL Database Connection...")
    init_db()
    print("  -> MySQL cv_verifier_db connected and candidates table ready.\n")

    sample_resume = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../Pritam_Gangurde_Resume.pdf")
    if not os.path.exists(sample_resume):
        sample_resume = "Pritam_Gangurde_Resume.pdf"
    
    print(f"[2/5] Parsing Candidate Resume: {os.path.basename(sample_resume)}...")
    cv_data = extract_cv_data(sample_resume)
    print(f"  -> Candidate: {cv_data['name']}")
    print(f"  -> Email: {cv_data['email']}")
    print(f"  -> Phone: {cv_data['phone']}")
    print(f"  -> LinkedIn: {cv_data['linkedin_url']}")
    print(f"  -> Skills: {cv_data['skills'][:70]}...\n")

    # PIPELINE A: VERIFIED MATCH SCENARIO
    print("----------------------------------------------------------------")
    print("[3/5] VALIDATION PIPELINE A: Profile Alignment Validation")
    print("----------------------------------------------------------------")
    cand_id_a = insert_candidate(
        name=cv_data["name"],
        email=cv_data["email"],
        phone=cv_data["phone"],
        linkedin_url=cv_data["linkedin_url"],
        educational_background=cv_data["educational_background"],
        professional_background=cv_data["professional_background"],
        experiences=cv_data["experiences"],
        skills=cv_data["skills"],
        raw_cv_text=cv_data.get("raw_cv_text", "")
    )
    print(f"  -> Initial candidate record persisted with ID: #{cand_id_a} (Status: Pending)")

    # Scrape LinkedIn
    li_data_a = scrape_linkedin_profile(cv_data["linkedin_url"], candidate_hint_name=cv_data["name"])
    print(f"  -> Fetched LinkedIn Profile: Name='{li_data_a['name']}', Headline='{li_data_a['headline']}'")

    # Cross Check
    status_a, score_a, reason_a = cross_check_cv_and_linkedin(cv_data, li_data_a)
    print(f"  -> Verification Engine Result: '{status_a}' (Score: {score_a}/100)")

    # Update MySQL
    update_candidate_match(cand_id_a, status_a, score_a, reason_a, li_data_a)
    record_a = get_candidate(cand_id_a)
    print(f"  -> Database Record Status: '{record_a['match_status']}'")
    assert record_a['match_status'] == "Matched with LinkedIn profile", f"Expected Matched but got {record_a['match_status']}"
    print("  -> [PASS] Pipeline A Successfully Validated!\n")

    # PIPELINE B: DISCREPANCY DETECTION SCENARIO
    print("----------------------------------------------------------------")
    print("[4/5] VALIDATION PIPELINE B: Discrepancy Detection Validation")
    print("----------------------------------------------------------------")
    mismatch_cv = cv_data.copy()
    mismatch_cv["name"] = "Pritam Gangurde"
    mismatch_cv["linkedin_url"] = "https://www.linkedin.com/in/john-doe-mismatch"

    cand_id_b = insert_candidate(
        name=mismatch_cv["name"],
        email="pritam.test@example.com",
        phone="+91 9876543210",
        linkedin_url=mismatch_cv["linkedin_url"],
        educational_background="B.Tech Computer Science",
        professional_background="Full Stack Developer",
        experiences="Software development projects",
        skills="Python, SQL, React",
        raw_cv_text="Resume with mismatched LinkedIn profile"
    )
    print(f"  -> Initial candidate record persisted with ID: #{cand_id_b} (Status: Pending)")

    # Scrape Mismatched LinkedIn
    li_data_b = scrape_linkedin_profile(mismatch_cv["linkedin_url"], candidate_hint_name=mismatch_cv["name"])
    print(f"  -> Fetched LinkedIn Profile: Name='{li_data_b['name']}', Headline='{li_data_b['headline']}'")

    # Cross Check
    status_b, score_b, reason_b = cross_check_cv_and_linkedin(mismatch_cv, li_data_b)
    print(f"  -> Verification Engine Result: '{status_b}' (Score: {score_b}/100)")

    # Update MySQL
    update_candidate_match(cand_id_b, status_b, score_b, reason_b, li_data_b)
    record_b = get_candidate(cand_id_b)
    print(f"  -> Database Record Status: '{record_b['match_status']}'")
    assert record_b['match_status'] == "LinkedIn profile doesn't match", f"Expected Mismatch but got {record_b['match_status']}"
    print("  -> [PASS] Pipeline B Successfully Validated!\n")

    # Summary
    print("================================================================")
    print("[5/5] ACTIVE CANDIDATE RECORDS IN DATABASE:")
    print("================================================================")
    all_cands = get_all_candidates()
    for c in all_cands:
        print(f"  ID #{c['id']}: {c['name']} | Status: [{c['match_status']}] | Score: {c['match_score']}% | URL: {c['linkedin_url']}")

    print("\n[SUCCESS] ALL VALIDATION CHECKS PASSED. SYSTEM IS FULLY OPERATIONAL.")

if __name__ == "__main__":
    run_system_verification()
