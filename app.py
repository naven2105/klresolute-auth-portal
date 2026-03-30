"""
File: app.py

Purpose:
- Main Flask application
"""

from flask import Flask
from auth.routes import auth_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(auth_bp)

# ✅ Add this route
@app.route("/")
def home():
    return "KLResolute Authentication Service is running"


if __name__ == "__main__":
    app.run(debug=True)