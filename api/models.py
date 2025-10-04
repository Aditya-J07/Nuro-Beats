from datetime import datetime
from api import db
from werkzeug.security import generate_password_hash, check_password_hash
import json

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    patient_profile = db.relationship('PatientProfile', foreign_keys='PatientProfile.user_id', backref='user', uselist=False)
    clinician_profile = db.relationship('ClinicianProfile', backref='user', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'user_type': self.user_type,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class PatientProfile(db.Model):
    __tablename__ = 'patient_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    condition = db.Column(db.String(50), nullable=False)
    baseline_cadence = db.Column(db.Float)
    baseline_tapping_speed = db.Column(db.Float)
    baseline_speech_rate = db.Column(db.Float)
    target_cadence = db.Column(db.Float)
    target_speech_rate = db.Column(db.Float)
    assigned_clinician_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    stroke_affected_side = db.Column(db.String(20))
    stroke_severity = db.Column(db.String(20))
    aphasia_type = db.Column(db.String(30))
    dysarthria_severity = db.Column(db.String(20))
    motor_impairment_level = db.Column(db.String(20))
    cognitive_status = db.Column(db.String(20))
    emotional_status = db.Column(db.String(30))
    preferred_music_genre = db.Column(db.String(50))
    preferred_beat_sound = db.Column(db.String(20), default='metronome')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sessions = db.relationship('TherapySession', backref='patient', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'condition': self.condition,
            'baseline_cadence': self.baseline_cadence,
            'baseline_tapping_speed': self.baseline_tapping_speed,
            'baseline_speech_rate': self.baseline_speech_rate,
            'target_cadence': self.target_cadence,
            'target_speech_rate': self.target_speech_rate,
            'assigned_clinician_id': self.assigned_clinician_id,
            'stroke_affected_side': self.stroke_affected_side,
            'stroke_severity': self.stroke_severity,
            'aphasia_type': self.aphasia_type,
            'dysarthria_severity': self.dysarthria_severity,
            'motor_impairment_level': self.motor_impairment_level,
            'cognitive_status': self.cognitive_status,
            'emotional_status': self.emotional_status,
            'preferred_music_genre': self.preferred_music_genre,
            'preferred_beat_sound': self.preferred_beat_sound,
        }

class ClinicianProfile(db.Model):
    __tablename__ = 'clinician_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    license_number = db.Column(db.String(50))
    specialization = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'license_number': self.license_number,
            'specialization': self.specialization
        }

class TherapySession(db.Model):
    __tablename__ = 'therapy_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient_profiles.id'), nullable=False)
    session_type = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    initial_bpm = db.Column(db.Float, nullable=False)
    final_bpm = db.Column(db.Float)
    target_bpm = db.Column(db.Float, nullable=False)
    duration_seconds = db.Column(db.Integer)
    accuracy_score = db.Column(db.Float)
    completed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    
    affected_limb = db.Column(db.String(20))
    speech_clarity_score = db.Column(db.Float)
    cognitive_load_level = db.Column(db.Integer)
    emotional_response = db.Column(db.String(20))
    generated_beat_url = db.Column(db.String(500))
    
    metrics_data = db.Column(db.Text)
    
    def set_metrics(self, metrics_dict):
        self.metrics_data = json.dumps(metrics_dict)
    
    def get_metrics(self):
        if self.metrics_data:
            return json.loads(self.metrics_data)
        return {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'session_type': self.session_type,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'initial_bpm': self.initial_bpm,
            'final_bpm': self.final_bpm,
            'target_bpm': self.target_bpm,
            'duration_seconds': self.duration_seconds,
            'accuracy_score': self.accuracy_score,
            'completed': self.completed,
            'notes': self.notes,
            'affected_limb': self.affected_limb,
            'speech_clarity_score': self.speech_clarity_score,
            'cognitive_load_level': self.cognitive_load_level,
            'emotional_response': self.emotional_response,
            'generated_beat_url': self.generated_beat_url
        }

class SessionMetrics(db.Model):
    __tablename__ = 'session_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('therapy_sessions.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    current_bpm = db.Column(db.Float, nullable=False)
    sync_accuracy = db.Column(db.Float)
    adjustment_made = db.Column(db.Boolean, default=False)
    
    session = db.relationship('TherapySession', backref='metrics')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'current_bpm': self.current_bpm,
            'sync_accuracy': self.sync_accuracy,
            'adjustment_made': self.adjustment_made
        }

class BaselineAssessment(db.Model):
    __tablename__ = 'baseline_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient_profiles.id'), nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False)
    measured_value = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    assessed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    patient = db.relationship('PatientProfile', backref='assessments')
    assessor = db.relationship('User', foreign_keys=[assessed_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'assessment_type': self.assessment_type,
            'measured_value': self.measured_value,
            'notes': self.notes,
            'assessed_by': self.assessed_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
