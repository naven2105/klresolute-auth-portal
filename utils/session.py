"""
File: utils/session.py

Purpose:
- Handle session validation
- Enforce inactivity timeout using DB time
"""

from db import get_db_connection


def validate_session(session_token):
    if not session_token:
        return None

    conn = get_db_connection()
    cur = conn.cursor()

    # ✅ Validate session AND inactivity in DB
    cur.execute("""
        SELECT user_id
        FROM auth_sessions
        WHERE session_token = %s
        AND expires_at > NOW()
        AND last_activity_at > NOW() - INTERVAL '1 minute'
    """, (session_token,))

    session = cur.fetchone()

    if not session:
        # Optional: cleanup expired session
        cur.execute("""
            DELETE FROM auth_sessions
            WHERE session_token = %s
        """, (session_token,))
        conn.commit()

        cur.close()
        conn.close()
        return None

    user_id = session[0]

    # ✅ Update last activity (DB time)
    cur.execute("""
        UPDATE auth_sessions
        SET last_activity_at = NOW()
        WHERE session_token = %s
    """, (session_token,))
    conn.commit()

    cur.close()
    conn.close()

    return user_id