"""
File: auth/routes.py

Purpose:
- Define authentication routes
"""

from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from db import get_db_connection
from utils.otp import generate_otp, send_otp_email

auth_bp = Blueprint("auth", __name__)


# --- Test Route ---
@auth_bp.route("/test", methods=["GET"])
def test():
    return {"message": "auth routes working"}, 200


# --- Login Page ---
@auth_bp.route("/login/<client_number>", methods=["GET"])
def login(client_number):
    return render_template("login.html", client_number=client_number)


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

    # 1. Resolve client_id
    cur.execute("""
        SELECT client_id
        FROM clients
        WHERE client_number = %s
    """, (client_number,))
    
    client = cur.fetchone()

    if not client:
        return jsonify({"message": "Invalid client"}), 400

    client_id = client[0]

    # 2. Check user exists
    cur.execute("""
        SELECT user_id
        FROM auth_users
        WHERE (email = %s OR phone = %s)
        AND client_id = %s
    """, (contact, contact, client_id))

    user = cur.fetchone()

    if not user:
        return jsonify({"message": "User not found"}), 404

    # 3. Generate OTP
    code = generate_otp()

    # 4. Store OTP
    cur.execute("""
        INSERT INTO auth_otp_codes (client_id, contact, code, expires_at)
        VALUES (%s, %s, %s, NOW() + INTERVAL '5 minutes')
    """, (client_id, contact, code))

    conn.commit()

    cur.close()
    conn.close()

    # 5. Send email
    send_otp_email(contact, code)

    # 6. Redirect to verify page
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

    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Get latest OTP
    cur.execute("""
        SELECT otp_id, client_id, expires_at, used
        FROM auth_otp_codes
        WHERE contact = %s AND code = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (contact, code))

    otp = cur.fetchone()

    if not otp:
        return jsonify({"message": "Invalid OTP"}), 400

    otp_id, client_id, expires_at, used = otp

    # 2. Check validity
    if used:
        return jsonify({"message": "OTP already used"}), 400

    if expires_at < datetime.utcnow():
        return jsonify({"message": "OTP expired"}), 400

    # 3. Mark as used
    cur.execute("""
        UPDATE auth_otp_codes
        SET used = TRUE
        WHERE otp_id = %s
    """, (otp_id,))

    # 4. Get user
    cur.execute("""
        SELECT user_id
        FROM auth_users
        WHERE (email = %s OR phone = %s)
        AND client_id = %s
    """, (contact, contact, client_id))

    user = cur.fetchone()

    if not user:
        return jsonify({"message": "User not found"}), 404

    user_id = user[0]

    # 5. Create session
    session_token = "sess_" + generate_otp(10)

    cur.execute("""
        INSERT INTO auth_sessions (user_id, session_token, expires_at, last_activity_at)
        VALUES (%s, %s, NOW() + INTERVAL '8 hours', NOW())
    """, (user_id, session_token))

    conn.commit()

    cur.close()
    conn.close()

    # Redirect to dashboard
    return redirect("/dashboard")


# --- Dashboard ---
@auth_bp.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("dashboard.html")