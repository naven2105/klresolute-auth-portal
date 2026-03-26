"""
File: utils/session.py

Purpose:
- Handle session validation
- Enforce inactivity timeout (1 minute)
"""

from datetime import datetime, timedelta
from db import get_db_connection


INACTIVITY_TIMEOUT = timedelta(minutes=1)


def validate_session(session_token):
    if not session_token:
        return None

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, expires_at, last_activity_at
        FROM auth_sessions
        WHERE session_token = %s
    """, (session_token,))

    session = cur.fetchone()

    if not session:
        cur.close()
        conn.close()
        return None

    user_id, expires_at, last_activity_at = session

    now = datetime.utcnow()

    # --- Expiry check ---
    if expires_at < now:
        cur.close()
        conn.close()
        return None

    # 🔴 FIX: Allow slight buffer (timezone / delay)
    if last_activity_at < now - (INACTIVITY_TIMEOUT + timedelta(seconds=10)):
        cur.execute("""
            DELETE FROM auth_sessions
            WHERE session_token = %s
        """, (session_token,))
        conn.commit()

        cur.close()
        conn.close()
        return None

    # --- Update last activity ---
    cur.execute("""
        UPDATE auth_sessions
        SET last_activity_at = NOW()
        WHERE session_token = %s
    """, (session_token,))
    conn.commit()

    cur.close()
    conn.close()

    return user_id