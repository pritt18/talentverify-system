import os
import json
import sqlite3
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
    "autocommit": True,
    "connect_timeout": 3
}

SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "candidates.db")

_DB_MODE = None

def get_db_mode() -> str:
    """Detect whether to use MySQL or SQLite fallback."""
    global _DB_MODE
    if _DB_MODE is not None:
        return _DB_MODE
    
    # Check if forced via env
    env_force = os.getenv("DB_TYPE", "").lower()
    if env_force == "sqlite":
        _DB_MODE = "sqlite"
        return _DB_MODE

    # Try connecting to MySQL
    try:
        conn = pymysql.connect(**DB_CONFIG)
        conn.close()
        _DB_MODE = "mysql"
        return _DB_MODE
    except Exception:
        # Check if root without database connects
        try:
            cfg = DB_CONFIG.copy()
            cfg.pop("database", None)
            conn = pymysql.connect(**cfg)
            conn.close()
            _DB_MODE = "mysql"
            return _DB_MODE
        except Exception:
            _DB_MODE = "sqlite"
            return _DB_MODE

def get_mysql_connection():
    return pymysql.connect(**DB_CONFIG)

def get_sqlite_connection():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Ensures database and candidates table exist across MySQL and SQLite."""
    mode = get_db_mode()
    if mode == "mysql":
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
    else:
        # SQLite fallback for cloud deployments without MySQL
        with get_sqlite_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    linkedin_url TEXT,
                    educational_background TEXT,
                    professional_background TEXT,
                    experiences TEXT,
                    skills TEXT,
                    raw_cv_text TEXT,
                    linkedin_scraped_data TEXT,
                    match_status TEXT NOT NULL DEFAULT 'Pending',
                    match_score INTEGER DEFAULT 0,
                    match_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

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
    mode = get_db_mode()
    if mode == "mysql":
        query = """
            INSERT INTO candidates (
                name, email, phone, linkedin_url, educational_background,
                professional_background, experiences, skills, raw_cv_text, match_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending');
        """
        with get_mysql_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    name, email, phone, linkedin_url, educational_background,
                    professional_background, experiences, skills, raw_cv_text
                ))
                return cur.lastrowid
    else:
        query = """
            INSERT INTO candidates (
                name, email, phone, linkedin_url, educational_background,
                professional_background, experiences, skills, raw_cv_text, match_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending');
        """
        with get_sqlite_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, (
                name, email, phone, linkedin_url, educational_background,
                professional_background, experiences, skills, raw_cv_text
            ))
            conn.commit()
            return cur.lastrowid

def update_candidate_match(
    candidate_id: int,
    match_status: str,
    match_score: int,
    match_reason: str,
    linkedin_scraped_data: Optional[Dict[str, Any]] = None
) -> bool:
    scraped_json = json.dumps(linkedin_scraped_data) if linkedin_scraped_data is not None else None
    mode = get_db_mode()
    if mode == "mysql":
        query = """
            UPDATE candidates
            SET match_status = %s,
                match_score = %s,
                match_reason = %s,
                linkedin_scraped_data = %s
            WHERE id = %s;
        """
        with get_mysql_connection() as conn:
            with conn.cursor() as cur:
                affected = cur.execute(query, (
                    match_status,
                    match_score,
                    match_reason,
                    scraped_json,
                    candidate_id
                ))
                return affected > 0
    else:
        query = """
            UPDATE candidates
            SET match_status = ?,
                match_score = ?,
                match_reason = ?,
                linkedin_scraped_data = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """
        with get_sqlite_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, (
                match_status,
                match_score,
                match_reason,
                scraped_json,
                candidate_id
            ))
            conn.commit()
            return cur.rowcount > 0

def get_candidate(candidate_id: int) -> Optional[Dict[str, Any]]:
    mode = get_db_mode()
    if mode == "mysql":
        with get_mysql_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM candidates WHERE id = %s;", (candidate_id,))
                return cur.fetchone()
    else:
        with get_sqlite_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM candidates WHERE id = ?;", (candidate_id,))
            row = cur.fetchone()
            return dict(row) if row else None

def get_all_candidates() -> List[Dict[str, Any]]:
    mode = get_db_mode()
    if mode == "mysql":
        with get_mysql_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM candidates ORDER BY id DESC;")
                return cur.fetchall()
    else:
        with get_sqlite_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM candidates ORDER BY id DESC;")
            rows = cur.fetchall()
            return [dict(r) for r in rows]

if __name__ == "__main__":
    init_db()
    print(f"Database initialized in [{get_db_mode().upper()}] mode successfully.")
