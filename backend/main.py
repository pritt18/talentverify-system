import os
import shutil
import tempfile
from typing import Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

import sys
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

app = FastAPI(
    title="Candidate Verification & Profile Intelligence API",
    description="Enterprise API for resume parsing, database persistence, LinkedIn scraping, and verification matching.",
    version="1.0.0"
)

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure database exists on startup
@app.on_event("startup")
def on_startup():
    try:
        init_db()
        print("[Startup] MySQL Database & Candidates Table initialized.")
    except Exception as e:
        print(f"[Startup Warning] Could not initialize MySQL: {e}")

# Models for n8n webhook delegation
class ParseRequest(BaseModel):
    raw_text: Optional[str] = None
    file_path: Optional[str] = None

class LinkedInScrapeRequest(BaseModel):
    linkedin_url: str
    candidate_name: Optional[str] = None

class CrossCheckRequest(BaseModel):
    cv_data: Dict[str, Any]
    linkedin_data: Dict[str, Any]

@app.get("/api/health")
def health_check():
    """Health check endpoint confirming backend and MySQL availability."""
    db_status = "connected"
    candidate_count = 0
    try:
        candidates = get_all_candidates()
        candidate_count = len(candidates)
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    return {
        "status": "healthy",
        "service": "n8n-cv-matcher-backend",
        "database": db_status,
        "total_candidates": candidate_count
    }

@app.post("/api/upload-cv")
async def upload_cv(
    file: UploadFile = File(...),
    custom_linkedin: Optional[str] = Form(None)
):
    """
    Main End-to-End Workflow Endpoint:
    1. Receives CV file (PDF or DOCX).
    2. Extracts Candidate Details (Name, Contact, Education, Experience, Skills, LinkedIn).
    3. Saves candidate to MySQL database with 'Pending' match status.
    4. Scrapes LinkedIn profile information.
    5. Cross-checks CV vs LinkedIn and determines match status.
    6. Updates MySQL with 'Matched with LinkedIn profile' or 'LinkedIn profile doesn\'t match'.
    7. Returns complete execution result.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx", ".doc", ".txt"]:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, or TXT CV files are supported.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_cv:
        shutil.copyfileobj(file.file, temp_cv)
        temp_cv_path = temp_cv.name

    try:
        # Step 1: Extract CV details
        cv_data = extract_cv_data(temp_cv_path)
        
        # Override LinkedIn if explicitly passed
        if custom_linkedin and custom_linkedin.strip():
            cv_data["linkedin_url"] = custom_linkedin.strip()

        # Step 2: Save to MySQL database (Initial state: Pending)
        candidate_id = insert_candidate(
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

        # Step 3: Scrape LinkedIn profile
        linkedin_profile = scrape_linkedin_profile(
            cv_data["linkedin_url"],
            candidate_hint_name=cv_data["name"]
        )

        # Step 4: Cross-check CV against LinkedIn profile
        match_status, match_score, match_reason = cross_check_cv_and_linkedin(cv_data, linkedin_profile)

        # Step 5: Update MySQL with final verification decision
        update_candidate_match(
            candidate_id=candidate_id,
            match_status=match_status,
            match_score=match_score,
            match_reason=match_reason,
            linkedin_scraped_data=linkedin_profile
        )

        # Fetch final database record
        saved_record = get_candidate(candidate_id)

        return {
            "success": True,
            "candidate_id": candidate_id,
            "filename": file.filename,
            "extracted_cv": cv_data,
            "linkedin_data": linkedin_profile,
            "match_result": {
                "status": match_status,
                "score": match_score,
                "reason": match_reason
            },
            "database_record": saved_record
        }

    finally:
        if os.path.exists(temp_cv_path):
            try:
                os.remove(temp_cv_path)
            except Exception:
                pass

@app.get("/api/candidates")
def list_candidates():
    """Retrieve all candidates saved in MySQL."""
    try:
        candidates = get_all_candidates()
        return {"success": True, "count": len(candidates), "candidates": candidates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/candidates/{candidate_id}")
def get_single_candidate(candidate_id: int):
    """Retrieve specific candidate details."""
    candidate = get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"success": True, "candidate": candidate}

# Modular n8n Webhook Integration Endpoints:
@app.post("/api/webhook/cv-parse")
def webhook_cv_parse(req: ParseRequest):
    """Endpoint callable by n8n HTTP Request node to parse raw text or CV file."""
    if req.file_path and os.path.exists(req.file_path):
        parsed = extract_cv_data(req.file_path)
    else:
        # Save raw text to temporary txt file and parse
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as tf:
            tf.write(req.raw_text or "")
            temp_path = tf.name
        parsed = extract_cv_data(temp_path)
        os.remove(temp_path)
    return {"success": True, "data": parsed}

@app.post("/api/webhook/linkedin-scrape")
def webhook_linkedin_scrape(req: LinkedInScrapeRequest):
    """Endpoint callable by n8n HTTP Request node to scrape LinkedIn profile."""
    scraped = scrape_linkedin_profile(req.linkedin_url, candidate_hint_name=req.candidate_name)
    return {"success": True, "data": scraped}

@app.post("/api/webhook/cross-check")
def webhook_cross_check(req: CrossCheckRequest):
    """Endpoint callable by n8n to cross-check CV and LinkedIn data."""
    status, score, reason = cross_check_cv_and_linkedin(req.cv_data, req.linkedin_data)
    return {
        "success": True,
        "match_status": status,
        "match_score": score,
        "match_reason": reason
    }

# Serve Frontend static files directly at root (after API routes)
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
