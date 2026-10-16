-- MySQL Schema for TalentVerify Candidate Verification Platform
-- Database: cv_verifier_db

CREATE DATABASE IF NOT EXISTS cv_verifier_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cv_verifier_db;

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
