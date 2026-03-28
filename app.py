"""
File: app.py
Path: /app.py

Purpose:
- KLResolute Auth App
"""

from flask import Flask
from auth.routes import auth_bp

app = Flask(__name__)

app.register_blueprint(auth_bp)

if __name__ == "__main__":
    app.run(debug=True)