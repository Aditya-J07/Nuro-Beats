from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.patients import patients_bp
from api import db
from api.models import User, PatientProfile, ClinicianProfile, TherapySession
import logging

@patients_bp.route('', methods=['POST'])
@jwt_required()
def create_patient():
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or current_user.user_type != 'clinician':
            return jsonify({'error': 'Only clinicians can create patient accounts'}), 403
        
        data = request.get_json()
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        condition = data.get('condition')
        
        if not all([username, email, password, first_name, last_name, condition]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        user = User(
            username=username,
            email=email,
            user_type='patient',
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        patient_profile = PatientProfile(
            user_id=user.id,
            condition=condition,
            assigned_clinician_id=current_user_id
        )
        
        if condition == 'stroke':
            patient_profile.stroke_affected_side = data.get('stroke_affected_side')
            patient_profile.stroke_severity = data.get('stroke_severity')
            patient_profile.aphasia_type = data.get('aphasia_type')
            patient_profile.dysarthria_severity = data.get('dysarthria_severity')
            patient_profile.motor_impairment_level = data.get('motor_impairment_level')
            patient_profile.cognitive_status = data.get('cognitive_status')
            patient_profile.emotional_status = data.get('emotional_status')
            patient_profile.preferred_music_genre = data.get('preferred_music_genre')
            patient_profile.preferred_beat_sound = data.get('preferred_beat_sound', 'metronome')
            patient_profile.baseline_cadence = float(data.get('baseline_cadence', 120))
            patient_profile.target_cadence = float(data.get('target_cadence', patient_profile.baseline_cadence * 1.1))
            patient_profile.baseline_tapping_speed = float(data.get('baseline_tapping_speed', 5))
            patient_profile.baseline_speech_rate = float(data.get('baseline_speech_rate', 150))
        
        db.session.add(patient_profile)
        db.session.commit()
        
        return jsonify({
            'message': 'Patient created successfully',
            'user': user.to_dict(),
            'profile': patient_profile.to_dict(),
            'credentials': {
                'username': username,
                'password': password
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Create patient error: {str(e)}")
        return jsonify({'error': 'Failed to create patient'}), 500

@patients_bp.route('', methods=['GET'])
@jwt_required()
def get_patients():
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        if current_user.user_type == 'clinician':
            assigned_patients = PatientProfile.query.filter_by(assigned_clinician_id=current_user_id).all()
            unassigned_patients = PatientProfile.query.filter_by(assigned_clinician_id=None).all()
            
            return jsonify({
                'assigned_patients': [
                    {**p.to_dict(), 'user': User.query.get(p.user_id).to_dict()} 
                    for p in assigned_patients
                ],
                'unassigned_patients': [
                    {**p.to_dict(), 'user': User.query.get(p.user_id).to_dict()} 
                    for p in unassigned_patients
                ]
            }), 200
        else:
            return jsonify({'error': 'Access denied'}), 403
            
    except Exception as e:
        logging.error(f"Get patients error: {str(e)}")
        return jsonify({'error': 'Failed to get patients'}), 500

@patients_bp.route('/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_patient(patient_id):
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        patient_profile = PatientProfile.query.get_or_404(patient_id)
        
        if current_user.user_type == 'patient' and patient_profile.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        elif current_user.user_type == 'clinician' and patient_profile.assigned_clinician_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        user = User.query.get(patient_profile.user_id)
        
        recent_sessions = TherapySession.query.filter_by(
            patient_id=patient_id,
            completed=True
        ).order_by(TherapySession.start_time.desc()).limit(5).all()
        
        total_sessions = TherapySession.query.filter_by(
            patient_id=patient_id,
            completed=True
        ).count()
        
        avg_accuracy = db.session.query(db.func.avg(TherapySession.accuracy_score)).filter_by(
            patient_id=patient_id,
            completed=True
        ).scalar() or 0
        
        return jsonify({
            'user': user.to_dict(),
            'profile': patient_profile.to_dict(),
            'recent_sessions': [s.to_dict() for s in recent_sessions],
            'stats': {
                'total_sessions': total_sessions,
                'avg_accuracy': round(avg_accuracy, 1)
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get patient error: {str(e)}")
        return jsonify({'error': 'Failed to get patient'}), 500
