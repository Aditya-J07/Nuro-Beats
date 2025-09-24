from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
import json

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'patient' or 'clinician'
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient_profile = db.relationship('PatientProfile', foreign_keys='PatientProfile.user_id', backref='user', uselist=False)
    clinician_profile = db.relationship('ClinicianProfile', backref='user', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PatientProfile(db.Model):
    __tablename__ = 'patient_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    condition = db.Column(db.String(50), nullable=False)  # 'parkinsons' or 'stroke'
    baseline_cadence = db.Column(db.Float)  # steps per minute
    baseline_tapping_speed = db.Column(db.Float)  # taps per minute
    baseline_speech_rate = db.Column(db.Float)  # syllables per minute
    target_cadence = db.Column(db.Float)
    target_speech_rate = db.Column(db.Float)
    assigned_clinician_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Stroke-specific fields
    stroke_affected_side = db.Column(db.String(20))  # 'left', 'right', 'bilateral'
    stroke_severity = db.Column(db.String(20))  # 'mild', 'moderate', 'severe'
    aphasia_type = db.Column(db.String(30))  # 'broca', 'wernicke', 'global', 'none'
    dysarthria_severity = db.Column(db.String(20))  # 'mild', 'moderate', 'severe', 'none'
    motor_impairment_level = db.Column(db.String(20))  # 'mild', 'moderate', 'severe'
    cognitive_status = db.Column(db.String(20))  # 'normal', 'mild_impairment', 'moderate_impairment'
    emotional_status = db.Column(db.String(30))  # 'stable', 'mild_depression', 'anxiety', 'mixed'
    preferred_music_genre = db.Column(db.String(50))
    preferred_beat_sound = db.Column(db.String(20), default='metronome')  # metronome, drum, soft_bell, wooden_block, piano  # Patient's preferred music style
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('TherapySession', backref='patient', lazy=True)

class ClinicianProfile(db.Model):
    __tablename__ = 'clinician_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    license_number = db.Column(db.String(50))
    specialization = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # No direct relationship - will query manually for assigned patients

class TherapySession(db.Model):
    __tablename__ = 'therapy_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient_profiles.id'), nullable=False)
    session_type = db.Column(db.String(50), nullable=False)  # 'gait_trainer', 'speech_rhythm', 'upper_limb_motor', 'melodic_intonation', 'cognitive_rhythm'
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    initial_bpm = db.Column(db.Float, nullable=False)
    final_bpm = db.Column(db.Float)
    target_bpm = db.Column(db.Float, nullable=False)
    duration_seconds = db.Column(db.Integer)
    accuracy_score = db.Column(db.Float)  # 0-100 percentage
    completed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    
    # Stroke-specific fields
    affected_limb = db.Column(db.String(20))  # For motor sessions
    speech_clarity_score = db.Column(db.Float)  # For speech sessions
    cognitive_load_level = db.Column(db.Integer)  # 1-5 scale for cognitive sessions
    emotional_response = db.Column(db.String(20))  # 'positive', 'neutral', 'negative'
    generated_beat_url = db.Column(db.String(500))  # URL to generated beat audio
    
    # JSON field to store session metrics
    metrics_data = db.Column(db.Text)  # JSON string
    
    def set_metrics(self, metrics_dict):
        self.metrics_data = json.dumps(metrics_dict)
    
    def get_metrics(self):
        if self.metrics_data:
            return json.loads(self.metrics_data)
        return {}

class SessionMetrics(db.Model):
    __tablename__ = 'session_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('therapy_sessions.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    current_bpm = db.Column(db.Float, nullable=False)
    sync_accuracy = db.Column(db.Float)  # 0-100 percentage
    adjustment_made = db.Column(db.Boolean, default=False)
    
    # Relationships
    session = db.relationship('TherapySession', backref='metrics')

class BaselineAssessment(db.Model):
    __tablename__ = 'baseline_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient_profiles.id'), nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False)  # 'gait', 'tapping', 'speech'
    measured_value = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    assessed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('PatientProfile', backref='assessments')
    assessor = db.relationship('User', foreign_keys=[assessed_by])
