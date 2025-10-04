from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from api.auth import auth_bp
from api import db
from api.models import User, PatientProfile, ClinicianProfile
import logging

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        
        if not all([username, email, password, user_type, first_name, last_name]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        if user_type not in ['patient', 'clinician']:
            return jsonify({'error': 'Invalid user type'}), 400
        
        user = User(
            username=username,
            email=email,
            user_type=user_type,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        if user_type == 'clinician':
            license_number = data.get('license_number', '')
            specialization = data.get('specialization', '')
            clinician_profile = ClinicianProfile(
                user_id=user.id,
                license_number=license_number,
                specialization=specialization
            )
            db.session.add(clinician_profile)
        
        db.session.commit()
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Missing username or password'}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        profile = None
        if user.user_type == 'patient' and user.patient_profile:
            profile = user.patient_profile.to_dict()
        elif user.user_type == 'clinician' and user.clinician_profile:
            profile = user.clinician_profile.to_dict()
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'profile': profile,
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({'access_token': access_token}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        profile = None
        if user.user_type == 'patient' and user.patient_profile:
            profile = user.patient_profile.to_dict()
        elif user.user_type == 'clinician' and user.clinician_profile:
            profile = user.clinician_profile.to_dict()
        
        return jsonify({
            'user': user.to_dict(),
            'profile': profile
        }), 200
        
    except Exception as e:
        logging.error(f"Get current user error: {str(e)}")
        return jsonify({'error': 'Failed to get user'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({'message': 'Logout successful'}), 200
