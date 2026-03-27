"""
File: app.py
Path: /app.py

Purpose:
- Dumela Fire Service App (Phase 1)
- Insert + list service jobs
"""

from flask import Flask, render_template, request, redirect
from db import get_db_connection
from auth_middleware import require_auth

app = Flask(__name__)


# --- Create Job (Form) ---
@app.route("/jobs/new", methods=["GET"])
@require_auth("dumela_fire")
def new_job():
    return render_template("new_job.html")


# --- Insert Job ---
@app.route("/jobs", methods=["POST"])
@require_auth("dumela_fire")
def create_job():
    data = request.form

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO dumela_fire_service_jobs (
            customer_company_name,
            service_address,
            contact_person_name,
            contact_phone,
            contact_email,
            scheduled_service_date,
            account_manager_name,
            assigned_technician_name,
            status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data.get("customer_company_name"),
        data.get("service_address"),
        data.get("contact_person_name"),
        data.get("contact_phone"),
        data.get("contact_email"),
        data.get("scheduled_service_date"),
        data.get("account_manager_name"),
        data.get("assigned_technician_name"),
        "scheduled"
    ))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/jobs")


# --- List Jobs ---
@app.route("/jobs", methods=["GET"])
@require_auth("dumela_fire")
def list_jobs():

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            customer_company_name,
            service_address,
            contact_person_name,
            contact_phone,
            contact_email,
            scheduled_service_date,
            account_manager_name,
            assigned_technician_name,
            status,
            created_at
        FROM dumela_fire_service_jobs
        ORDER BY created_at DESC
    """)

    jobs = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("jobs.html", jobs=jobs)


if __name__ == "__main__":
    app.run(debug=True)