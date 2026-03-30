"""
File: auth_middleware.py
Path: /auth_middleware.py

Purpose:
- Validate session from shared auth system
"""

from functools import wraps
from flask import request, redirect
from db import get_db_connection


def require_auth(client_name="dumela_fire"):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):

            session_token = request.cookies.get("session_token")

            if not session_token:
                return redirect("https://auth1.klresolute.co.za/login/27620469153")

            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT user_id, client_id, expires_at
                FROM auth_sessions
                WHERE session_token = %s
            """, (session_token,))

            session = cur.fetchone()

            cur.close()
            conn.close()

            if not session:
                return redirect("https://auth1.klresolute.co.za/login/27620469153")

            user_id, client_id, expires_at = session

            if client_id != client_name:
                return redirect("https://auth1.klresolute.co.za/login/27620469153")

            return f(*args, **kwargs)

        return wrapper
    return decorator