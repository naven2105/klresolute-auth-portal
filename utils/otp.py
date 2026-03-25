"""
File: utils/otp.py

Purpose:
- Generate OTP codes
- Send OTP via email
"""

import random
import string
import smtplib
import os
from email.mime.text import MIMEText


def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(to_email, code):
    smtp_server = "mail.klresolute.co.za"
    smtp_port = 465
    smtp_user = "admin@klresolute.co.za"
    smtp_password = os.getenv("EMAIL_PASSWORD")

    msg = MIMEText(f"Your login code is: {code}")
    msg["Subject"] = "Your Login Code"
    msg["From"] = smtp_user
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
    except Exception as e:
        print(f"Email send error: {e}")