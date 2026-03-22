"""
App Entry Point
KLResolute Auth Portal
file / path = app.py

Purpose:
- Start Flask app
- Register routes
- Provide base endpoints
"""

from flask import Flask
from auth.routes import auth_bp


def create_app():
    app = Flask(__name__)

    # Basic config (expand later)
    app.config["SECRET_KEY"] = "dev-secret-key"

    # Register blueprints
    app.register_blueprint(auth_bp)

    return app


app = create_app()


# --- Basic Test Route ---
@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


# --- Run App ---
if __name__ == "__main__":
    app.run(debug=True)