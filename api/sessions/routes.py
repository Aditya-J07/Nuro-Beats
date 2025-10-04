from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.sessions import sessions_bp
from api import db
from api.models import User, TherapySession, SessionMetrics
from beat_generator import BeatGenerator
from datetime import datetime
import logging

@sessions_bp.route('/start', methods=['POST'])
@jwt_required()
def start_session():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.user_type != 'patient':
            return jsonify({'error': 'Only patients can start sessions'}), 403
        
        patient_profile = user.patient_profile
        
        data = request.get_json()
        session_type = data.get('session_type', 'gait_trainer')
        initial_bpm = float(data.get('initial_bpm', 60))
        target_bpm = float(data.get('target_bpm', 70))
        
        beat_url = None
        if patient_profile.condition == 'stroke':
            beat_generator = BeatGenerator()
            
            patient_condition = {
                'affected_side': patient_profile.stroke_affected_side,
                'severity': patient_profile.stroke_severity,
                'aphasia_type': patient_profile.aphasia_type,
                'dysarthria_severity': patient_profile.dysarthria_severity,
                'motor_impairment': patient_profile.motor_impairment_level,
                'cognitive_status': patient_profile.cognitive_status,
                'emotional_status': patient_profile.emotional_status,
                'preferred_genre': patient_profile.preferred_music_genre,
                'preferred_sound': patient_profile.preferred_beat_sound or 'metronome'
            }
            
            beat_url = beat_generator.generate_stroke_therapy_beat(session_type, int(initial_bpm), patient_condition)
            optimal_bpm = beat_generator.get_optimal_bpm_for_stroke_therapy(session_type, patient_condition)
            
            if abs(initial_bpm - optimal_bpm) > 10:
                initial_bpm = optimal_bpm
        
        therapy_session = TherapySession(
            patient_id=patient_profile.id,
            session_type=session_type,
            initial_bpm=initial_bpm,
            target_bpm=target_bpm,
            start_time=datetime.utcnow(),
            generated_beat_url=beat_url,
            affected_limb=data.get('affected_limb'),
            cognitive_load_level=int(data.get('cognitive_load_level', 1))
        )
        
        db.session.add(therapy_session)
        db.session.commit()
        
        return jsonify({
            'session': therapy_session.to_dict(),
            'stroke_specific': patient_profile.condition == 'stroke'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Start session error: {str(e)}")
        return jsonify({'error': 'Failed to start session'}), 500

@sessions_bp.route('/<int:session_id>', methods=['GET'])
@jwt_required()
def get_session(session_id):
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        therapy_session = TherapySession.query.get_or_404(session_id)
        
        if user.user_type == 'patient' and therapy_session.patient.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'session': therapy_session.to_dict()}), 200
        
    except Exception as e:
        logging.error(f"Get session error: {str(e)}")
        return jsonify({'error': 'Failed to get session'}), 500

@sessions_bp.route('/<int:session_id>/update', methods=['POST'])
@jwt_required()
def update_session(session_id):
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if user.user_type != 'patient':
            return jsonify({'error': 'Only patients can update sessions'}), 403
        
        therapy_session = TherapySession.query.get_or_404(session_id)
        
        if therapy_session.patient.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        current_bpm = float(data.get('current_bpm'))
        sync_accuracy = float(data.get('sync_accuracy', 0))
        
        metric = SessionMetrics(
            session_id=session_id,
            current_bpm=current_bpm,
            sync_accuracy=sync_accuracy,
            timestamp=datetime.utcnow()
        )
        
        adjustment_bpm = current_bpm
        if sync_accuracy < 70:
            adjustment_bpm = max(current_bpm - 2, 40)
        elif sync_accuracy > 90:
            adjustment_bpm = min(current_bpm + 1, 120)
        
        if adjustment_bpm != current_bpm:
            metric.adjustment_made = True
        
        db.session.add(metric)
        db.session.commit()
        
        return jsonify({
            'adjusted_bpm': adjustment_bpm,
            'sync_accuracy': sync_accuracy
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update session error: {str(e)}")
        return jsonify({'error': 'Failed to update session'}), 500

@sessions_bp.route('/<int:session_id>/complete', methods=['POST'])
@jwt_required()
def complete_session(session_id):
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if user.user_type != 'patient':
            return jsonify({'error': 'Only patients can complete sessions'}), 403
        
        therapy_session = TherapySession.query.get_or_404(session_id)
        
        if therapy_session.patient.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        therapy_session.end_time = datetime.utcnow()
        therapy_session.completed = True
        therapy_session.duration_seconds = int(data.get('duration', 0))
        therapy_session.final_bpm = float(data.get('final_bpm', therapy_session.initial_bpm))
        therapy_session.accuracy_score = float(data.get('accuracy_score', 0))
        therapy_session.notes = data.get('notes', '')
        
        db.session.commit()
        
        return jsonify({
            'message': 'Session completed successfully',
            'session': therapy_session.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Complete session error: {str(e)}")
        return jsonify({'error': 'Failed to complete session'}), 500
