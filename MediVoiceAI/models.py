from datetime import datetime, timedelta
import random
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(30), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    medicines = db.relationship("Medicine", backref="user", lazy=True, cascade="all, delete-orphan")
    dosage_logs = db.relationship("DosageLog", backref="user", lazy=True, cascade="all, delete-orphan")
    otps = db.relationship("OTP", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_otp(self, purpose="login", validity_minutes=10):
        # Invalidate past unused OTPs for this user & purpose
        OTP.query.filter_by(user_id=self.id, purpose=purpose, is_used=False).update({"is_used": True})
        
        code = f"{random.randint(100000, 999999)}"
        expires_at = datetime.utcnow() + timedelta(minutes=validity_minutes)
        otp = OTP(user_id=self.id, code=code, purpose=purpose, expires_at=expires_at)
        db.session.add(otp)
        db.session.commit()
        return otp

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class OTP(db.Model):
    __tablename__ = "otps"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(20), default="login")  # 'login' or 'register'
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    def is_valid(self):
        return (not self.is_used) and (datetime.utcnow() <= self.expires_at)


class Medicine(db.Model):
    __tablename__ = "medicines"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    generic_name = db.Column(db.String(150), nullable=True)
    category = db.Column(db.String(80), default="General")
    dosage_amount = db.Column(db.String(50), nullable=False)  # e.g. "500"
    dosage_unit = db.Column(db.String(30), default="mg")       # e.g. "mg", "ml", "tablets"
    dosage_limit = db.Column(db.String(100), default="4 doses/day")
    frequency = db.Column(db.String(100), default="Daily")
    doses_per_day = db.Column(db.Integer, default=1)
    reminder_time = db.Column(db.String(255), nullable=False)  # e.g. "09:00 AM" or "08:00 AM, 08:00 PM"
    start_date = db.Column(db.String(30), nullable=False)
    end_date = db.Column(db.String(30), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    logs = db.relationship("DosageLog", backref="medicine", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "generic_name": self.generic_name,
            "category": self.category,
            "dosage_amount": self.dosage_amount,
            "dosage_unit": self.dosage_unit,
            "dosage_limit": self.dosage_limit,
            "frequency": self.frequency,
            "doses_per_day": self.doses_per_day,
            "reminder_time": self.reminder_time,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "notes": self.notes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class DosageLog(db.Model):
    __tablename__ = "dosage_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey("medicines.id"), nullable=False)
    scheduled_date = db.Column(db.String(20), nullable=False)  # YYYY-MM-DD
    scheduled_time = db.Column(db.String(20), nullable=False)  # e.g. "08:00 AM"
    status = db.Column(db.String(20), default="pending")        # 'taken', 'skipped', 'pending'
    action_time = db.Column(db.DateTime, nullable=True)
    dosage_recorded = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "medicine_id": self.medicine_id,
            "medicine_name": self.medicine.name if self.medicine else "",
            "scheduled_date": self.scheduled_date,
            "scheduled_time": self.scheduled_time,
            "status": self.status,
            "action_time": self.action_time.strftime("%I:%M %p") if self.action_time else None,
            "dosage_recorded": self.dosage_recorded,
            "notes": self.notes
        }
