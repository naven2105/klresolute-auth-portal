"""
File: auth/routes.py

Purpose:
- Define authentication routes
"""

from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from db import get_db_connection
from utils.otp import generate_otp, send_otp_email
from utils.session import validate_session

auth_bp = Blueprint("auth", __name__)


# --- Test Route ---
@auth_bp.route("/test", methods=["GET"])
def test():
    return {"message": "auth routes working"}, 200


# --- Login Page ---
@auth_bp.route("/login/<client_number>", methods=["GET"])
def login(client_number):
    expired = request.args.get("expired")
    return render_template(
        "login.html",
        client_number=client_number,
        expired=expired
    )


# --- Verify Page ---
@auth_bp.route("/verify", methods=["GET"])
def verify_page():
    contact = request.args.get("contact")
    client_number = request.args.get("client_number")

    return render_template(
        "verify.html",
        contact=contact,
        client_number=client_number
    )


# --- Request OTP ---
@auth_bp.route("/auth/request-otp", methods=["POST"])
def request_otp():
    contact = request.form.get("contact")
    client_number = request.form.get("client_number")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT client_id
        FROM clients
        WHERE client_number = %s
    """, (client_number,))
    
    client = cur.fetchone()

    if not client:
        return jsonify({"message": "Invalid client"}), 400

    client_id = client[0]

    cur.execute("""
        SELECT user_id
        FROM auth_users
        WHERE (email = %s OR phone = %s)
        AND client_id = %s
    """, (contact, contact, client_id))

    user = cur.fetchone()

    if not user:
        return jsonify({"message": "User not found"}), 404

    cur.execute("""
        SELECT COUNT(*)
        FROM auth_otp_codes
        WHERE contact = %s
        AND created_at > NOW() - INTERVAL '5 minutes'
    """, (contact,))

    if cur.fetchone()[0] >= 3:
        cur.close()
        conn.close()
        return jsonify({
            "message": "Too many requests. Please wait a few minutes."
        }), 429

    code = generate_otp()

    cur.execute("""
        INSERT INTO auth_otp_codes (client_id, contact, code, expires_at, attempt_count)
        VALUES (%s, %s, %s, NOW() + INTERVAL '5 minutes', 0)
    """, (client_id, contact, code))

    conn.commit()
    cur.close()
    conn.close()

    send_otp_email(contact, code)

    return redirect(url_for(
        "auth.verify_page",
        contact=contact,
        client_number=client_number
    ))


# --- Verify OTP ---
@auth_bp.route("/auth/verify-otp", methods=["POST"])
def verify_otp():
    contact = request.form.get("contact")
    code = request.form.get("code")
    client_number = request.form.get("client_number")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT otp_id, client_id, expires_at, used, attempt_count
        FROM auth_otp_codes
        WHERE contact = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (contact,))

    otp = cur.fetchone()

    if not otp:
        return render_template(
            "verify.html",
            contact=contact,
            client_number=client_number,
            error="No code found. Please request a new one."
        )

    otp_id, client_id, expires_at, used, attempt_count = otp

    if expires_at < datetime.utcnow():
        return render_template(
            "verify.html",
            contact=contact,
            client_number=client_number,
            error="Code expired. Please request a new one."
        )

    if used:
        return render_template(
            "verify.html",
            contact=contact,
            client_number=client_number,
            error="This code has already been used."
        )

    if attempt_count >= 3:
        return render_template(
            "verify.html",
            contact=contact,
            client_number=client_number,
            error="Too many incorrect attempts. Redirecting to login...",
            redirect_to_login=True
        )

    cur.execute("""
        SELECT otp_id
        FROM auth_otp_codes
        WHERE otp_id = %s AND code = %s
    """, (otp_id, code))

    valid = cur.fetchone()

    if not valid:
        cur.execute("""
            UPDATE auth_otp_codes
            SET attempt_count = attempt_count + 1
            WHERE otp_id = %s
        """, (otp_id,))

        conn.commit()

        remaining = 3 - (attempt_count + 1)

        return render_template(
            "verify.html",
            contact=contact,
            client_number=client_number,
            error=f"Invalid code. {remaining} attempt(s) remaining."
        )

    cur.execute("""
        UPDATE auth_otp_codes
        SET used = TRUE
        WHERE otp_id = %s
    """, (otp_id,))

    cur.execute("""
        SELECT user_id
        FROM auth_users
        WHERE (email = %s OR phone = %s)
        AND client_id = %s
    """, (contact, contact, client_id))

    user_id = cur.fetchone()[0]

    session_token = "sess_" + generate_otp(10)

    cur.execute("""
        INSERT INTO auth_sessions (user_id, session_token, expires_at, last_activity_at)
        VALUES (%s, %s, NOW() + INTERVAL '8 hours', NOW())
    """, (user_id, session_token))

    conn.commit()

    cur.close()
    conn.close()

    response = redirect("/dashboard")
    response.set_cookie("session_token", session_token, httponly=True)

    return response


# --- Dashboard (SYNC TIMER) ---
@auth_bp.route("/dashboard", methods=["GET"])
def dashboard():
    session_token = request.cookies.get("session_token")
    user_id = validate_session(session_token)

    conn = get_db_connection()
    cur = conn.cursor()

    # Get user
    cur.execute("""
        SELECT email, client_id
        FROM auth_users
        WHERE user_id = %s
    """, (user_id,))
    user = cur.fetchone()

    email, client_id = user

    # Get client
    cur.execute("""
        SELECT client_name
        FROM clients
        WHERE client_id = %s
    """, (client_id,))
    client = cur.fetchone()

    client_name = client[0] if client else "Unknown Client"

    # ✅ NEW: get last_activity_at
    cur.execute("""
        SELECT last_activity_at
        FROM auth_sessions
        WHERE session_token = %s
    """, (session_token,))
    session_data = cur.fetchone()

    last_activity_at = session_data[0]

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        email=email,
        client_name=client_name,
        last_activity_at=last_activity_at
    )


# --- Logout ---
@auth_bp.route("/logout", methods=["GET"])
def logout():
    session_token = request.cookies.get("session_token")

    if session_token:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM auth_sessions
            WHERE session_token = %s
        """, (session_token,))

        conn.commit()
        cur.close()
        conn.close()

    response = redirect("/login/test")
    response.delete_cookie("session_token")

    return response