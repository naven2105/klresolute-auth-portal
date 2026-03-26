"""
File: utils/session.py

Purpose:
- Handle session validation
- Return user_id if session is valid
"""

from datetime import datetime
from db import get_db_connection


def validate_session(session_token):
    if not session_token:
        return None

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, expires_at
        FROM auth_sessions
        WHERE session_token = %s
    """, (session_token,))

    session = cur.fetchone()

    if not session:
        cur.close()
        conn.close()
        return None

    user_id, expires_at = session

    if expires_at < datetime.utcnow():
        cur.close()
        conn.close()
        return None

    cur.close()
    conn.close()

    return user_id