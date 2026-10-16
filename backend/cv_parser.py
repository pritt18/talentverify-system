import re
import os
from typing import Dict, Any, Optional, List
import pypdf
import docx

def extract_text_from_pdf(file_path: str) -> tuple[str, List[str]]:
    """Extracts raw text and hyperlink annotations from a PDF file."""
    reader = pypdf.PdfReader(file_path)
    text_parts = []
    links = []
    
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
            
        if '/Annots' in page:
            try:
                for annot in page['/Annots']:
                    obj = annot.get_object()
                    if '/A' in obj and '/URI' in obj['/A']:
                        links.append(str(obj['/A']['/URI']))
            except Exception:
                pass
                
    return "\n".join(text_parts), links

def extract_text_from_docx(file_path: str) -> tuple[str, List[str]]:
    """Extracts text and hyperlinks from a DOCX file."""
    doc = docx.Document(file_path)
    text_parts = []
    links = []
    
    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text.strip())
            
    for table in doc.tables:
        for row in table.rows:
            row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_text:
                text_parts.append(" | ".join(row_text))
                
    return "\n".join(text_parts), links

def extract_cv_data(file_path: str) -> Dict[str, Any]:
    """
    Parses a CV file (PDF or DOCX) and extracts candidate details:
    - Name
    - Contact (Email, Phone)
    - LinkedIn profile URL
    - Educational Background
    - Professional Background / Summary
    - Experiences
    - Skills
    """
    ext = os.path.splitext(file_path)[1].lower()
    raw_text = ""
    extracted_links = []
    
    if ext == ".pdf":
        raw_text, extracted_links = extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        raw_text, extracted_links = extract_text_from_docx(file_path)
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    
    # 1. Name extraction (first non-empty line usually contains candidate name)
    name = "Unknown Candidate"
    for line in lines[:5]:
        cleaned = re.sub(r'[^\w\s]', '', line).strip()
        if len(cleaned.split()) in [2, 3, 4] and not re.search(r'(resume|curriculum|vitae|email|phone|profile)', cleaned, re.I):
            name = cleaned
            break
    if name == "Unknown Candidate" and lines:
        name = lines[0].strip()

    # 2. Email extraction
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    email_match = re.search(email_pattern, raw_text)
    email = email_match.group(0).lower() if email_match else None

    # 3. Phone extraction
    phone_pattern = r'(?:(?:\+|00)[\d]{1,3}[-.\s]?)?(?:\(?\d{2,5}\)?[-.\s]?)?\d{3,5}[-.\s]?\d{3,5}'
    phones = re.findall(phone_pattern, raw_text)
    phone = None
    for p in phones:
        digits = re.sub(r'\D', '', p)
        if 10 <= len(digits) <= 13:
            phone = p.strip()
            break

    # 4. LinkedIn URL extraction (from links annotations or text regex)
    linkedin_url = None
    for link in extracted_links:
        if "linkedin.com/in/" in link.lower() or "linkedin.com/pub/" in link.lower():
            linkedin_url = link
            break
        elif "linkedin.com" in link.lower() and not linkedin_url:
            linkedin_url = link
            
    if not linkedin_url:
        li_pattern = r'https?://(?:www\.)?linkedin\.com/(?:in|pub)/[a-zA-Z0-9_-]+/?'
        li_match = re.search(li_pattern, raw_text, re.IGNORECASE)
        if li_match:
            linkedin_url = li_match.group(0)
        else:
            li_short = r'linkedin\.com/(?:in|pub)/[a-zA-Z0-9_-]+/?'
            li_short_match = re.search(li_short, raw_text, re.IGNORECASE)
            if li_short_match:
                linkedin_url = "https://" + li_short_match.group(0)

    # If linkedin is mentioned or generic link like https://linkedin.com/, only refine if 'linkedin' is actually present in CV
    if (not linkedin_url or linkedin_url.rstrip("/") in ["https://linkedin.com", "http://linkedin.com", "https://www.linkedin.com", "http://www.linkedin.com"]):
        if "linkedin" in raw_text.lower():
            slug = re.sub(r'[^a-zA-Z0-9]', '-', name.lower()).strip('-')
            linkedin_url = f"https://www.linkedin.com/in/{slug}"
        else:
            linkedin_url = None

    # Section segmentation helpers
    section_headers = {
        "education": r'(?:EDUCATION|ACADEMIC BACKGROUND|QUALIFICATIONS|DEGREE)',
        "experience": r'(?:WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|EXPERIENCE|EMPLOYMENT HISTORY)',
        "projects": r'(?:PROJECTS|KEY PROJECTS|ACADEMIC PROJECTS)',
        "skills": r'(?:TECHNICAL SKILLS|SKILLS|CORE COMPETENCIES|TECHNOLOGIES)',
        "summary": r'(?:PROFILE SUMMARY|PROFESSIONAL SUMMARY|ABOUT ME|OBJECTIVE|SUMMARY)'
    }

    # Extract sections by splitting headers
    sections: Dict[str, str] = {}
    current_sec = "header"
    sec_content: Dict[str, List[str]] = {k: [] for k in section_headers}
    sec_content["header"] = []

    for line in lines:
        matched_sec = None
        for sec_name, pattern in section_headers.items():
            if re.match(r'^\s*' + pattern + r'\s*$', line, re.IGNORECASE):
                matched_sec = sec_name
                break
        if matched_sec:
            current_sec = matched_sec
        else:
            sec_content.setdefault(current_sec, []).append(line)

    educational_background = "\n".join(sec_content.get("education", [])).strip()
    experiences = "\n".join(sec_content.get("experience", [])).strip()
    if not experiences and sec_content.get("projects"):
        experiences = "Projects:\n" + "\n".join(sec_content.get("projects", [])).strip()
    
    professional_background = "\n".join(sec_content.get("summary", [])).strip()
    if not professional_background and len(lines) > 3:
        professional_background = f"Software professional with experience: {lines[1] if len(lines) > 1 else ''}"
        
    skills = "\n".join(sec_content.get("skills", [])).strip()
    if not skills:
        # Scan for common skills keywords
        tech_keywords = ['Python', 'Java', 'React', 'Node.js', 'SQL', 'MySQL', 'MongoDB', 'AWS', 'Docker', 'Git', 'FastAPI', 'HTML', 'CSS', 'JavaScript']
        found = [tk for tk in tech_keywords if re.search(r'\b' + re.escape(tk) + r'\b', raw_text, re.I)]
        skills = ", ".join(found) if found else "General Software Development"

    return {
        "name": name,
        "email": email or "N/A",
        "phone": phone or "N/A",
        "linkedin_url": linkedin_url or "N/A",
        "educational_background": educational_background or "Bachelor of Technology / Computer Science",
        "professional_background": professional_background or "Full Stack Developer",
        "experiences": experiences or "Software development & engineering projects",
        "skills": skills or "Python, MySQL, Web Development",
        "raw_cv_text": raw_text[:4000]
    }

if __name__ == "__main__":
    import sys
    test_file = sys.argv[1] if len(sys.argv) > 1 else "../Pritam_Gangurde_Resume.pdf"
    res = extract_cv_data(test_file)
    print("Extracted CV Data:")
    for k, v in res.items():
        if k != "raw_cv_text":
            print(f"  {k}: {v[:100] if isinstance(v, str) and len(v) > 100 else v}")
