import sys
import os
import pymysql
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_connection import DB_CONFIG

with pymysql.connect(**DB_CONFIG) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, email, phone, match_status, match_score, created_at FROM candidates ORDER BY id ASC;")
        rows = cur.fetchall()
        print(f"\n{'='*95}")
        print(f"{'ID':<4} | {'NAME':<18} | {'EMAIL':<28} | {'STATUS':<30} | {'SCORE'}")
        print(f"{'='*95}")
        for r in rows:
            print(f"{r['id']:<4} | {r['name']:<18} | {r['email'] or 'N/A':<28} | {r['match_status']:<30} | {r['match_score']}%")
        print(f"{'='*95}\n")
