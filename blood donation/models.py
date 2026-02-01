from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    city = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    
    # Health & Habits
    bp = db.Column(db.Boolean, default=False)
    sugar = db.Column(db.Boolean, default=False)
    heart_disease = db.Column(db.Boolean, default=False)
    asthma = db.Column(db.Boolean, default=False)
    smoking = db.Column(db.Boolean, default=False)
    drinking = db.Column(db.Boolean, default=False)
    
    last_donation_date = db.Column(db.Date, nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=True) # Admin approval
    qr_code_data = db.Column(db.String(500), nullable=True) # Data for QR ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Security & Tracking
    last_active = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    is_locked = db.Column(db.Boolean, default=False)
    risk_score = db.Column(db.Float, default=0.0)

    # Manual backrefs definition to avoid collisions if any
    # (Using overlaps or strictly defining in one place is better)

    def get_id(self):
        return f"user_{self.id}"

class Hospital(db.Model):
    __tablename__ = 'hospitals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    blood_stock = db.Column(db.JSON, default={})
    is_approved = db.Column(db.Boolean, default=True)

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='SuperAdmin')

    def get_id(self):
        return f"admin_{self.id}"

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    id = db.Column(db.Integer, primary_key=True)
    donation_gap_days = db.Column(db.Integer, default=90)
    emergency_radius_km = db.Column(db.Float, default=50.0)
    admin_contact_email = db.Column(db.String(100), default='admin@lifelink.com')

class AIConfig(db.Model):
    __tablename__ = 'ai_config'
    id = db.Column(db.Integer, primary_key=True)
    weight_blood_group = db.Column(db.Float, default=40.0)
    weight_distance = db.Column(db.Float, default=30.0)
    weight_recency = db.Column(db.Float, default=20.0)
    weight_health = db.Column(db.Float, default=10.0)

class BloodRequest(db.Model):
    __tablename__ = 'blood_requests'
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    patient_name = db.Column(db.String(100), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    hospital_name = db.Column(db.String(100), nullable=False)
    hospital_location = db.Column(db.String(255), nullable=True)
    req_latitude = db.Column(db.Float, nullable=False)
    req_longitude = db.Column(db.Float, nullable=False)
    urgency_level = db.Column(db.String(20), default='Medium')
    contact_number = db.Column(db.String(15), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Removed duplicate created_at and relationship (User.requests is sufficient if defined there or backref)
    requester = db.relationship('User', backref='requests')

    @property
    def status_color(self):
        return '#eee' if self.status == 'Pending' else '#d4edda'

class DonationHistory(db.Model):
    __tablename__ = 'donation_history'
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    donation_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.String(200), nullable=True)
    
    donor = db.relationship('User', backref='history')

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

