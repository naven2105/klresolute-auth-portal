"""
File: utils/session.py

Purpose:
- Handle session validation
- Enforce inactivity timeout using DB time (5 minutes)
"""

from db import get_db_connection


def validate_session(session_token):
    if not session_token:
        return None

    conn = get_db_connection()
    cur = conn.cursor()

    # ✅ Step 1: validate FIRST (5 minutes)
    cur.execute("""
        SELECT user_id
        FROM auth_sessions
        WHERE session_token = %s
        AND expires_at > NOW()
        AND last_activity_at > NOW() - INTERVAL '5 minutes'
    """, (session_token,))

    session = cur.fetchone()

    if not session:
        # cleanup
        cur.execute("""
            DELETE FROM auth_sessions
            WHERE session_token = %s
        """, (session_token,))
        conn.commit()

        cur.close()
        conn.close()
        return None

    user_id = session[0]

    # ✅ Step 2: update activity AFTER validation
    cur.execute("""
        UPDATE auth_sessions
        SET last_activity_at = NOW()
        WHERE session_token = %s
    """, (session_token,))
    conn.commit()

    cur.close()
    conn.close()

    return user_id