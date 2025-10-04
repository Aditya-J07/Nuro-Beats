from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.assessments import assessments_bp
from api import db
from api.models import User, PatientProfile, BaselineAssessment, TherapySession
from datetime import datetime, timedelta
import logging

@assessments_bp.route('', methods=['POST'])
@jwt_required()
def create_assessment():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.user_type != 'clinician':
            return jsonify({'error': 'Only clinicians can create assessments'}), 403
        
        data = request.get_json()
        
        patient_id = int(data.get('patient_id'))
        assessment_type = data.get('assessment_type')
        measured_value = float(data.get('measured_value'))
        notes = data.get('notes', '')
        
        assessment = BaselineAssessment(
            patient_id=patient_id,
            assessment_type=assessment_type,
            measured_value=measured_value,
            notes=notes,
            assessed_by=current_user_id
        )
        
        db.session.add(assessment)
        
        patient_profile = PatientProfile.query.get(patient_id)
        if assessment_type == 'gait':
            patient_profile.baseline_cadence = measured_value
            patient_profile.target_cadence = measured_value * 1.1
        elif assessment_type == 'tapping':
            patient_profile.baseline_tapping_speed = measured_value
        elif assessment_type == 'speech':
            patient_profile.baseline_speech_rate = measured_value
            patient_profile.target_speech_rate = measured_value * 1.15
        elif assessment_type == 'balance':
            assessment.notes = f"Berg Balance Scale Score: {measured_value}/56. " + (notes or "")
        elif assessment_type == 'coordination':
            assessment.notes = f"Finger-to-Nose Time: {measured_value}s per repetition. " + (notes or "")
        elif assessment_type == 'cognitive':
            assessment.notes = f"MoCA Score: {measured_value}/30. " + (notes or "")
        
        db.session.commit()
        
        return jsonify({
            'message': 'Assessment recorded successfully',
            'assessment': assessment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Create assessment error: {str(e)}")
        return jsonify({'error': 'Failed to create assessment'}), 500

@assessments_bp.route('/patient/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_patient_assessments(patient_id):
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        patient_profile = PatientProfile.query.get_or_404(patient_id)
        
        if user.user_type == 'patient' and patient_profile.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        elif user.user_type == 'clinician' and patient_profile.assigned_clinician_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        assessments = BaselineAssessment.query.filter_by(patient_id=patient_id).order_by(
            BaselineAssessment.created_at.desc()
        ).all()
        
        return jsonify({
            'assessments': [a.to_dict() for a in assessments]
        }), 200
        
    except Exception as e:
        logging.error(f"Get assessments error: {str(e)}")
        return jsonify({'error': 'Failed to get assessments'}), 500

@assessments_bp.route('/progress/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_progress(patient_id):
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        patient_profile = PatientProfile.query.get_or_404(patient_id)
        
        if user.user_type == 'patient' and patient_profile.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        elif user.user_type == 'clinician' and patient_profile.assigned_clinician_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        therapy_sessions = TherapySession.query.filter(
            TherapySession.patient_id == patient_id,
            TherapySession.completed == True,
            TherapySession.start_time >= thirty_days_ago
        ).order_by(TherapySession.start_time.asc()).all()
        
        dates = []
        accuracy_scores = []
        bpm_values = []
        
        for therapy_session in therapy_sessions:
            dates.append(therapy_session.start_time.strftime('%Y-%m-%d'))
            accuracy_scores.append(therapy_session.accuracy_score or 0)
            bpm_values.append(therapy_session.final_bpm or therapy_session.initial_bpm)
        
        return jsonify({
            'dates': dates,
            'accuracy_scores': accuracy_scores,
            'bpm_values': bpm_values,
            'baseline_cadence': patient_profile.baseline_cadence,
            'target_cadence': patient_profile.target_cadence
        }), 200
        
    except Exception as e:
        logging.error(f"Get progress error: {str(e)}")
        return jsonify({'error': 'Failed to get progress'}), 500
