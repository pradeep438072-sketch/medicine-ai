import os
import re
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, abort
)
from werkzeug.utils import secure_filename

from config import Config
from database import db
from models import User, OTP, Medicine, DosageLog
from ai.ocr_reader import analyze_medicine_image
from ai.medicine_detector import get_medicine_suggestions, DISCLAIMER_TEXT
from ai.voice_assistant import process_voice_command

app = Flask(__name__)
app.config.from_object(Config)

# Ensure instance and upload directories exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.instance_path, exist_ok=True)

db.init_app(app)

# Helper: Login requirement decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# -------------------------------------------------------------
# 1. USER AUTHENTICATION & OTP
# -------------------------------------------------------------

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        if not identifier or not password:
            flash("Please provide both email/phone and password.", "error")
            return render_template("login.html")

        # Match either email or phone
        user = User.query.filter(
            (User.email == identifier) | (User.phone == identifier)
        ).first()

        if not user or not user.check_password(password):
            flash("Invalid credentials. Please check your email/phone and password.", "error")
            return render_template("login.html")

        # Create OTP and store pending user ID in session
        otp = user.generate_otp(purpose="login")
        session["pending_user_id"] = user.id
        session["pending_recipient"] = user.email or user.phone

        # Simulated dispatch
        print(f"[AUTH] Sent OTP {otp.code} to {session['pending_recipient']}")
        flash(f"Security code sent to {session['pending_recipient']}. Please enter it to complete sign in.", "info")
        return redirect(url_for("verify_otp"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Name, email, and password are required.", "error")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("register.html")

        # Check existing user
        if User.query.filter_by(email=email).first():
            flash("An account with this email address already exists.", "error")
            return render_template("register.html")

        if phone and User.query.filter_by(phone=phone).first():
            flash("An account with this phone number already exists.", "error")
            return render_template("register.html")

        new_user = User(name=name, email=email, phone=phone)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Seed initial starter demo medicines
        seed_starter_medicines(new_user.id)

        otp = new_user.generate_otp(purpose="register")
        session["pending_user_id"] = new_user.id
        session["pending_recipient"] = email or phone

        flash(f"Account created! Security code sent to {session['pending_recipient']}.", "success")
        return redirect(url_for("verify_otp"))

    return render_template("register.html")


@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    pending_user_id = session.get("pending_user_id")
    if not pending_user_id:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("login"))

    user = User.query.get(pending_user_id)
    if not user:
        session.pop("pending_user_id", None)
        return redirect(url_for("login"))

    # Fetch current active OTP for demo display convenience
    latest_otp = OTP.query.filter_by(user_id=user.id, is_used=False).order_by(OTP.created_at.desc()).first()

    if request.method == "POST":
        code = request.form.get("otp_code", "").strip()

        if not latest_otp or not latest_otp.is_valid():
            flash("The security code has expired or is invalid. Please request a new one.", "error")
            return render_template("otp.html", recipient=session.get("pending_recipient"), demo_otp=None)

        if latest_otp.code == code:
            latest_otp.is_used = True
            db.session.commit()

            # Establish authenticated session
            session.pop("pending_user_id", None)
            session.pop("pending_recipient", None)
            session["user_id"] = user.id
            session["user_name"] = user.name
            session.permanent = True

            flash(f"Welcome to MediVoice AI, {user.name}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Incorrect 6-digit code. Please verify and try again.", "error")

    demo_code = latest_otp.code if (latest_otp and latest_otp.is_valid()) else None
    return render_template("otp.html", recipient=session.get("pending_recipient"), demo_otp=demo_code)


@app.route("/resend-otp", methods=["POST"])
def resend_otp():
    pending_user_id = session.get("pending_user_id")
    if not pending_user_id:
        flash("Session expired.", "warning")
        return redirect(url_for("login"))

    user = User.query.get(pending_user_id)
    if user:
        otp = user.generate_otp(purpose="login")
        print(f"[AUTH RESEND] New OTP {otp.code} for user {user.id}")
        flash(f"A fresh security code has been sent.", "info")

    return redirect(url_for("verify_otp"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for("login"))


# -------------------------------------------------------------
# 2. DASHBOARD & DOSAGE TRACKING
# -------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    user = User.query.get(session["user_id"])
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Load active medicines
    active_medicines = Medicine.query.filter_by(user_id=user.id, is_active=True).all()

    # Ensure dosage logs exist for today
    today_schedule = sync_today_dosage_logs(user.id, active_medicines, today_str)

    # Compute Dosage Tracking statistics (Section 8)
    taken_count = sum(1 for item in today_schedule if item["status"] == "taken")
    skipped_count = sum(1 for item in today_schedule if item["status"] == "skipped")
    pending_count = sum(1 for item in today_schedule if item["status"] == "pending")
    total_doses = len(today_schedule)
    remaining_count = pending_count

    stats = {
        "total": total_doses,
        "taken": taken_count,
        "pending": pending_count,
        "skipped": skipped_count,
        "remaining": remaining_count
    }

    return render_template(
        "dashboard.html",
        user=user,
        active_medicines=active_medicines,
        today_schedule=today_schedule,
        stats=stats
    )


def sync_today_dosage_logs(user_id, active_medicines, today_str):
    """
    Ensure every active medicine has a DosageLog row for each scheduled time today.
    """
    items = []
    for med in active_medicines:
        times = [t.strip() for t in med.reminder_time.split(",") if t.strip()]
        for t in times:
            log = DosageLog.query.filter_by(
                user_id=user_id,
                medicine_id=med.id,
                scheduled_date=today_str,
                scheduled_time=t
            ).first()

            if not log:
                log = DosageLog(
                    user_id=user_id,
                    medicine_id=med.id,
                    scheduled_date=today_str,
                    scheduled_time=t,
                    status="pending"
                )
                db.session.add(log)
                db.session.commit()

            items.append({
                "log_id": log.id,
                "id": med.id,
                "name": med.name,
                "category": med.category,
                "dosage_amount": med.dosage_amount,
                "dosage_unit": med.dosage_unit,
                "frequency": med.frequency,
                "scheduled_time": t,
                "status": log.status,
                "notes": med.notes
            })

    # Sort items by scheduled time
    return items


# -------------------------------------------------------------
# 3. MEDICINE MANAGEMENT
# -------------------------------------------------------------

@app.route("/medicines")
@login_required
def medicines_list():
    user_id = session["user_id"]
    active = Medicine.query.filter_by(user_id=user_id, is_active=True).order_by(Medicine.created_at.desc()).all()
    previous = Medicine.query.filter_by(user_id=user_id, is_active=False).order_by(Medicine.created_at.desc()).all()
    return render_template("medicines.html", active_medicines=active, previous_medicines=previous)


@app.route("/medicines/add", methods=["GET", "POST"])
@login_required
def add_medicine_page():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "General").strip()
        generic_name = request.form.get("generic_name", "").strip()
        dosage_amount = request.form.get("dosage_amount", "").strip()
        dosage_unit = request.form.get("dosage_unit", "mg").strip()
        dosage_limit = request.form.get("dosage_limit", "Max 4 doses/day").strip()
        frequency = request.form.get("frequency", "Daily").strip()
        doses_per_day = int(request.form.get("doses_per_day", 1))
        reminder_time = request.form.get("reminder_time", "08:00 AM").strip()
        start_date = request.form.get("start_date", datetime.now().strftime("%Y-%m-%d")).strip()
        end_date = request.form.get("end_date", "").strip()
        notes = request.form.get("notes", "").strip()

        if not name or not dosage_amount or not reminder_time:
            flash("Please fill in the required fields (Name, Dosage, Reminder Time).", "error")
            return render_template("add_medicine.html")

        med = Medicine(
            user_id=session["user_id"],
            name=name,
            generic_name=generic_name,
            category=category,
            dosage_amount=dosage_amount,
            dosage_unit=dosage_unit,
            dosage_limit=dosage_limit,
            frequency=frequency,
            doses_per_day=doses_per_day,
            reminder_time=reminder_time,
            start_date=start_date,
            end_date=end_date if end_date else None,
            notes=notes,
            is_active=True
        )
        db.session.add(med)
        db.session.commit()

        flash(f"Medicine '{name}' successfully added!", "success")
        return redirect(url_for("medicines_list"))

    return render_template("add_medicine.html")


@app.route("/medicines/<int:med_id>")
@login_required
def medicine_details_page(med_id):
    med = Medicine.query.filter_by(id=med_id, user_id=session["user_id"]).first_or_404()
    logs = DosageLog.query.filter_by(medicine_id=med.id).order_by(DosageLog.scheduled_date.desc(), DosageLog.scheduled_time.desc()).limit(15).all()
    return render_template("medicine_details.html", med=med, logs=logs)


@app.route("/medicines/<int:med_id>/edit", methods=["GET", "POST"])
@login_required
def edit_medicine_page(med_id):
    med = Medicine.query.filter_by(id=med_id, user_id=session["user_id"]).first_or_404()

    if request.method == "POST":
        med.name = request.form.get("name", "").strip()
        med.category = request.form.get("category", "General").strip()
        med.generic_name = request.form.get("generic_name", "").strip()
        med.dosage_amount = request.form.get("dosage_amount", "").strip()
        med.dosage_unit = request.form.get("dosage_unit", "mg").strip()
        med.dosage_limit = request.form.get("dosage_limit", "").strip()
        med.frequency = request.form.get("frequency", "").strip()
        med.doses_per_day = int(request.form.get("doses_per_day", 1))
        med.reminder_time = request.form.get("reminder_time", "").strip()
        med.start_date = request.form.get("start_date", "").strip()
        end_date = request.form.get("end_date", "").strip()
        med.end_date = end_date if end_date else None
        med.notes = request.form.get("notes", "").strip()
        med.is_active = bool(request.form.get("is_active"))

        db.session.commit()
        flash(f"Medicine '{med.name}' updated successfully.", "success")
        return redirect(url_for("medicine_details_page", med_id=med.id))

    return render_template("edit_medicine.html", med=med)


@app.route("/medicines/<int:med_id>/delete", methods=["POST"])
@login_required
def delete_medicine(med_id):
    med = Medicine.query.filter_by(id=med_id, user_id=session["user_id"]).first_or_404()
    name = med.name
    db.session.delete(med)
    db.session.commit()
    flash(f"Medicine '{name}' has been deleted.", "info")
    return redirect(url_for("medicines_list"))


@app.route("/medicines/<int:med_id>/toggle", methods=["POST"])
@login_required
def toggle_active_medicine(med_id):
    med = Medicine.query.filter_by(id=med_id, user_id=session["user_id"]).first_or_404()
    med.is_active = not med.is_active
    db.session.commit()
    status_str = "activated" if med.is_active else "archived"
    flash(f"Medicine '{med.name}' is now {status_str}.", "info")
    return redirect(url_for("medicines_list"))


# -------------------------------------------------------------
# 4. REMINDER STATUS & NOTIFICATION APIS
# -------------------------------------------------------------

@app.route("/api/reminders/today")
@login_required
def api_today_reminders():
    user_id = session["user_id"]
    today_str = datetime.now().strftime("%Y-%m-%d")
    active = Medicine.query.filter_by(user_id=user_id, is_active=True).all()
    schedule = sync_today_dosage_logs(user_id, active, today_str)
    return jsonify({"status": "success", "reminders": schedule})


@app.route("/api/reminders/<int:log_id>/status", methods=["POST"])
@login_required
def api_update_reminder_status(log_id):
    data = request.get_json() or {}
    new_status = data.get("status", "pending").lower()

    if new_status not in ["taken", "skipped", "pending"]:
        return jsonify({"status": "error", "message": "Invalid status."}), 400

    log = DosageLog.query.filter_by(id=log_id, user_id=session["user_id"]).first()
    if not log:
        return jsonify({"status": "error", "message": "Log entry not found."}), 404

    log.status = new_status
    log.action_time = datetime.utcnow()
    db.session.commit()

    return jsonify({"status": "success", "log": log.to_dict()})


# -------------------------------------------------------------
# 5. CAMERA-BASED MEDICINE DETECTION (OCR / AI)
# -------------------------------------------------------------

@app.route("/camera")
@login_required
def camera_scan():
    return render_template("camera.html")


@app.route("/api/camera/scan", methods=["POST"])
@login_required
def api_camera_scan():
    if "image" not in request.files:
        return jsonify({"status": "error", "message": "No image provided."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "No image selected."}), 400

    filename = secure_filename(f"scan_{datetime.utcnow().timestamp()}_{file.filename}")
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    # Execute OCR analysis
    result = analyze_medicine_image(
        image_path=save_path,
        tesseract_cmd=app.config.get("TESSERACT_CMD", "tesseract"),
        gemini_api_key=app.config.get("GEMINI_API_KEY")
    )

    return jsonify(result)


# -------------------------------------------------------------
# 7. AI MEDICINE SUGGESTIONS
# -------------------------------------------------------------

@app.route("/suggestions", methods=["GET", "POST"])
@login_required
def suggestions_page():
    result = None
    symptoms = ""
    if request.method == "POST":
        symptoms = request.form.get("symptoms", "").strip()
        if symptoms:
            result = get_medicine_suggestions(symptoms)

    return render_template("suggestions.html", result=result, symptoms=symptoms, disclaimer=DISCLAIMER_TEXT)


# -------------------------------------------------------------
# 9. VOICE ASSISTANT
# -------------------------------------------------------------

@app.route("/assistant")
@login_required
def voice_assistant_page():
    return render_template("assistant.html")


@app.route("/api/voice/command", methods=["POST"])
@login_required
def api_voice_command():
    data = request.get_json() or {}
    command = data.get("command", "")
    
    user = User.query.get(session["user_id"])
    today_str = datetime.now().strftime("%Y-%m-%d")
    medicines = Medicine.query.filter_by(user_id=user.id).all()
    today_logs = DosageLog.query.filter_by(user_id=user.id, scheduled_date=today_str).all()

    # Run Python-based Voice Assistant
    response_payload = process_voice_command(user, command, medicines, today_logs)
    return jsonify(response_payload)


# -------------------------------------------------------------
# 11. MEDICINE HISTORY
# -------------------------------------------------------------

@app.route("/history")
@login_required
def history_page():
    user_id = session["user_id"]
    query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip().lower()
    date_filter = request.args.get("date", "").strip()

    stmt = DosageLog.query.filter_by(user_id=user_id)

    if status_filter:
        stmt = stmt.filter(DosageLog.status == status_filter)

    if date_filter:
        stmt = stmt.filter(DosageLog.scheduled_date == date_filter)

    logs = stmt.order_by(DosageLog.scheduled_date.desc(), DosageLog.scheduled_time.desc()).all()

    # Search filter by medicine name if provided
    if query:
        logs = [l for l in logs if l.medicine and (query.lower() in l.medicine.name.lower())]

    return render_template(
        "history.html",
        logs=logs,
        query=query,
        current_status=status_filter,
        selected_date=date_filter
    )


# -------------------------------------------------------------
# PROFILE
# -------------------------------------------------------------

@app.route("/profile")
@login_required
def profile_page():
    user = User.query.get(session["user_id"])
    return render_template("profile.html", user=user)


# -------------------------------------------------------------
# DATABASE INITIALIZATION & SEED
# -------------------------------------------------------------

def seed_starter_medicines(user_id):
    """
    Populate a new patient account with a realistic starting regimen.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    sample_meds = [
        Medicine(
            user_id=user_id,
            name="Paracetamol",
            generic_name="Acetaminophen",
            category="Pain & Fever",
            dosage_amount="500",
            dosage_unit="mg",
            dosage_limit="Max 4000 mg / 24 hours",
            frequency="Daily",
            doses_per_day=2,
            reminder_time="08:00 AM, 08:00 PM",
            start_date=today,
            notes="Take with plenty of water after meals.",
            is_active=True
        ),
        Medicine(
            user_id=user_id,
            name="Amoxicillin",
            generic_name="Amoxicillin Trihydrate",
            category="Antibiotic",
            dosage_amount="500",
            dosage_unit="mg",
            dosage_limit="1500 mg / day",
            frequency="Every 8 hours",
            doses_per_day=3,
            reminder_time="09:00 AM, 02:00 PM, 09:00 PM",
            start_date=today,
            notes="Complete prescribed 7-day course.",
            is_active=True
        ),
        Medicine(
            user_id=user_id,
            name="Atorvastatin",
            generic_name="Atorvastatin Calcium",
            category="Cardiac",
            dosage_amount="20",
            dosage_unit="mg",
            dosage_limit="Max 40 mg / day",
            frequency="Once daily at bedtime",
            doses_per_day=1,
            reminder_time="10:00 PM",
            start_date=today,
            notes="Take with or without food before sleeping.",
            is_active=True
        )
    ]
    db.session.add_all(sample_meds)
    db.session.commit()


with app.app_context():
    db.create_all()
    # If no users exist, create default demo patient
    if not User.query.first():
        demo_user = User(
            name="Sarah Connor",
            email="patient@medivoice.ai",
            phone="+1234567890"
        )
        demo_user.set_password("password123")
        db.session.add(demo_user)
        db.session.commit()
        seed_starter_medicines(demo_user.id)
        print("[INIT] Created demo patient: patient@medivoice.ai / password123")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
