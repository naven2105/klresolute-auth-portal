"""
App Entry Point
KLResolute Auth Portal
file / path = app.py

Purpose:
- Start Flask app
- Register routes
- Provide base endpoints
- Apply global middleware (session protection)
"""

from flask import Flask, request, redirect

from auth.routes import auth_bp
from utils.session import validate_session


def create_app():
    app = Flask(__name__)

    # Basic config (expand later)
    app.config["SECRET_KEY"] = "dev-secret-key"

    # Register blueprints
    app.register_blueprint(auth_bp)

    # --- Middleware: Protect Routes ---
    @app.before_request
    def protect_routes():
        # ✅ Protect ALL dashboard routes
        if request.path.startswith("/dashboard"):
            session_token = request.cookies.get("session_token")
            user_id = validate_session(session_token)

            if not user_id:
                return redirect("/login/test")

    return app


app = create_app()


# --- Basic Test Route ---
@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


# --- Run App ---
if __name__ == "__main__":
    app.run(debug=True)