# ⚡ TalentVerify - Candidate Verification & Profile Intelligence Platform

An enterprise-grade automated candidate background verification platform engineered with **n8n workflow automation**, **Python microservices**, and a **MySQL relational store**.

---

## 📌 Platform Overview

**TalentVerify** streamlines recruitment and candidate background vetting by automating the ingestion of resumes, extracting verified credential entities, validating candidate details against live LinkedIn profiles, and recording an immutable audit trail in a relational database.

### Core Capabilities:
- **Intelligent Ingestion:** Supports PDF and DOCX resume parsing with heuristic entity extraction (Name, Contact Details, LinkedIn URL, Academic History, Professional Experience, and Technical Skills).
- **Relational Persistence:** Automatically records candidate profiles in MySQL with status tracking (`Pending` ➔ `Matched with LinkedIn profile` / `LinkedIn profile doesn't match`).
- **Profile Cross-Referencing:** Scrapes and parses public LinkedIn profile attributes and evaluates background credentials using multi-factor token alignment and fuzzy scoring.
- **Workflow Orchestration:** Powered by a unified n8n automation workflow connecting webhooks, parsing microservices, database transactions, and client responses.
- **Modern Executive Dashboard:** Clean, responsive web interface for resume ingestion, live pipeline progress tracking, and database repository browsing.

---

## 🏗️ Architecture & Data Flow

```text
       ┌─────────────────────────────────────────────────────────────┐
       │             Candidate Verification Portal                   │
       │             (HTML5 / Modern CSS3 / Vanilla JS)              │
       └──────────────────────────────┬──────────────────────────────┘
                                      │  Uploads Resume (PDF / DOCX)
                                      ▼
       ┌─────────────────────────────────────────────────────────────┐
       │         n8n Orchestration Engine / Python REST API          │
       │         POST /api/upload-cv                                 │
       └──────────────────────────────┬──────────────────────────────┘
                                      │
             ┌────────────────────────┼────────────────────────┐
             ▼                        ▼                        ▼
     [1. Entity Extractor]   [2. Database Ledger]    [3. LinkedIn Enricher]
    Extracts Name, Email,    Inserts record into     Retrieves public profile,
    Phone, LinkedIn URL,     `candidates` table with headline, experience,
    Education & Skills.      status = 'Pending'.     education & skills.
             │                        │                        │
             └────────────────────────┴────────┬───────────────┘
                                               │
                                               ▼
                             ┌──────────────────────────────────┐
                             │    4. Cross-Verification Engine  │
                             │    - Name similarity matching    │
                             │    - Professional history check  │
                             │    - Academic institution match  │
                             │    - Technical competency match  │
                             └─────────────────┬────────────────┘
                                               │
                      ┌────────────────────────┴────────────────────────┐
                      ▼                                                 ▼
             If Score ≥ 60%                                    If Score < 60%
     UPDATE candidates SET match_status =              UPDATE candidates SET match_status =
     'Matched with LinkedIn profile'                   "LinkedIn profile doesn't match"
                      │                                                 │
                      └────────────────────────┬────────────────────────┘
                                               ▼
                             ┌──────────────────────────────────┐
                             │  Audit Ledger Updated & Response │
                             │  Returned to Dashboard           │
                             └──────────────────────────────────┘
```

---

## 🗄️ Relational Database Architecture

**Database:** `cv_verifier_db`  
**Table:** `candidates`

```sql
CREATE TABLE IF NOT EXISTS candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) DEFAULT NULL,
    phone VARCHAR(50) DEFAULT NULL,
    linkedin_url VARCHAR(500) DEFAULT NULL,
    educational_background TEXT DEFAULT NULL,
    professional_background TEXT DEFAULT NULL,
    experiences TEXT DEFAULT NULL,
    skills TEXT DEFAULT NULL,
    raw_cv_text MEDIUMTEXT DEFAULT NULL,
    linkedin_scraped_data JSON DEFAULT NULL,
    match_status VARCHAR(100) NOT NULL DEFAULT 'Pending',
    match_score INT DEFAULT 0,
    match_reason TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Verification Status Indicators:
- **`Matched with LinkedIn profile`**: Background entities and credentials align with candidate profile.
- **`LinkedIn profile doesn't match`**: Discrepancies detected or no LinkedIn profile found.
- **`Pending`**: Ingestion underway prior to verification engine evaluation.

---

## ⚙️ Technology Stack

| Layer | Component | Functionality |
| :--- | :--- | :--- |
| **Workflow Engine** | **n8n** | End-to-end orchestration workflow connecting webhooks, data transformers, database nodes, and scrapers. |
| **Backend Microservices** | **Python (FastAPI + PyMySQL)** | Document ingestion, heuristic entity parsing, fuzzy matching algorithms, and database management. |
| **Database** | **MySQL (MariaDB)** | ACID-compliant relational data store for candidate records, audit trails, and status logs. |
| **Frontend Portal** | **HTML5 + Modern CSS3 + Vanilla JS** | Modern user interface with resume dropzone, real-time pipeline tracker, and live repository table. |

---

## 🚀 Running the Project Locally

### 1. Start MySQL Database
Ensure MySQL service is active (via XAMPP or native service on port `3306`):
```powershell
C:\xampp\mysql\bin\mysqld.exe --defaults-file=C:\xampp\mysql\bin\my.ini --standalone
```

### 2. Initialize Database & Tables
```powershell
python database/db_connection.py
```

### 3. Launch Backend & Web Portal
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser at:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

### 4. Run System Validation Pipeline
```powershell
python backend/test_cv_matcher.py
```

### 5. Inspect Stored Database Records
```powershell
python database/show_candidates.py
```

---

## 🔄 n8n Workflow Specification

The production workflow file is exported at:
📁 **`n8n_cv_matcher_workflow.json`**

### Pipeline Nodes:
1. **CV Upload Webhook**: Accepts multipart/form-data resume submissions.
2. **Extract CV Information**: Invokes parsing microservice to extract structured entities.
3. **Save Candidate to MySQL (Pending)**: Inserts initial candidate profile into database.
4. **Scrape LinkedIn Profile**: Retrieves candidate LinkedIn profile record.
5. **Cross Check CV vs LinkedIn**: Executes JavaScript verification logic assessing name, experience, education, and skills.
6. **Update MySQL Match Status**: Updates record status to `Matched with LinkedIn profile` or `"LinkedIn profile doesn't match"`.
7. **Respond to Webhook**: Emits structured response to client.
