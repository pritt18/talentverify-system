import os
import json
import pymysql
from pymysql.cursors import DictCursor
from typing import Optional, Dict, Any, List

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "cv_verifier_db"),
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": True
}

def get_connection():
    """Create and return a MySQL connection."""
    return pymysql.connect(**DB_CONFIG)

def init_db():
    """Ensures database and candidates table exist."""
    # Attempt connecting directly to the database first
    try:
        with pymysql.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
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
                """)
                return
    except Exception:
        pass

    # If database didn't exist, connect as root without database name and create it
    root_config = DB_CONFIG.copy()
    db_name = root_config.pop("database", "cv_verifier_db")
    
    with pymysql.connect(**root_config) as conn:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cur.execute(f"USE `{db_name}`;")
            cur.execute("""
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
            """)

def insert_candidate(
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    educational_background: Optional[str] = None,
    professional_background: Optional[str] = None,
    experiences: Optional[str] = None,
    skills: Optional[str] = None,
    raw_cv_text: Optional[str] = None
) -> int:
    """Inserts an extracted candidate profile with initial Pending match status."""
    query = """
        INSERT INTO candidates (
            name, email, phone, linkedin_url, educational_background,
            professional_background, experiences, skills, raw_cv_text, match_status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending');
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (
                name, email, phone, linkedin_url, educational_background,
                professional_background, experiences, skills, raw_cv_text
            ))
            return cur.lastrowid

def update_candidate_match(
    candidate_id: int,
    match_status: str,
    match_score: int,
    match_reason: str,
    linkedin_scraped_data: Optional[Dict[str, Any]] = None
) -> bool:
    """Updates candidate match result after cross-referencing with LinkedIn."""
    query = """
        UPDATE candidates
        SET match_status = %s,
            match_score = %s,
            match_reason = %s,
            linkedin_scraped_data = %s
        WHERE id = %s;
    """
    scraped_json = json.dumps(linkedin_scraped_data) if linkedin_scraped_data is not None else None
    with get_connection() as conn:
        with conn.cursor() as cur:
            affected = cur.execute(query, (
                match_status,
                match_score,
                match_reason,
                scraped_json,
                candidate_id
            ))
            return affected > 0

def get_candidate(candidate_id: int) -> Optional[Dict[str, Any]]:
    """Fetch single candidate record by ID."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM candidates WHERE id = %s;", (candidate_id,))
            return cur.fetchone()

def get_all_candidates() -> List[Dict[str, Any]]:
    """Fetch all candidate records ordered by newest first."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM candidates ORDER BY id DESC;")
            return cur.fetchall()

if __name__ == "__main__":
    init_db()
    print("Database connection & initialization successful.")
