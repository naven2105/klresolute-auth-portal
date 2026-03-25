"""
File: auth/routes.py

Purpose:
- Define authentication routes
"""

from flask import Blueprint, render_template, request, jsonify

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

    # TEMP: just confirm data received
    return jsonify({
        "message": "OTP request received",
        "contact": contact,
        "client_number": client_number
    }), 200