"""
File: auth/routes.py

Purpose:
- Define authentication routes
"""

from flask import Blueprint, render_template, request, jsonify
from db import get_db_connection
from utils.otp import generate_otp

auth_bp = Blueprint("auth", __name__)


# --- Test Route ---
@auth_bp.route("/test", methods=["GET"])
def test():
    return {"message": "auth routes working"}, 200


# --- Login Page ---
@auth_bp.route("/login/<client_number>", methods=["GET"])
def login(client_number):
    return render_template("login.html", client_number=client_number)


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

    # TEMP: return OTP (for testing only)
    return jsonify({
        "message": "OTP generated",
        "otp": code
    }), 200