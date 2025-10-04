from flask import render_template, request, redirect, url_for, session, flash, jsonify
from app import app, db
from models import User, PatientProfile, ClinicianProfile, TherapySession, SessionMetrics, BaselineAssessment
from datetime import datetime, timedelta
import logging

@app.route('/')
def index():
    """Landing page - login/register interface"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            if user.user_type == 'patient':
                return redirect(url_for('patient_dashboard'))
            else:
                return redirect(url_for('clinician_dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            user_type = request.form['user_type']
            first_name = request.form['first_name']
            last_name = request.form['last_name']

            # Check if user already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'error')
                return redirect(url_for('index'))

            if User.query.filter_by(email=email).first():
                flash('Email already exists', 'error')
                return redirect(url_for('index'))

            # Create new user
            user = User(
                username=username,
                email=email,
                user_type=user_type,
                first_name=first_name,
                last_name=last_name
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # Get the user ID

            # Only allow clinician registration
            if user_type != 'clinician':
                flash('Only clinicians can register through this form.', 'error')
                return redirect(url_for('index'))

            license_number = request.form.get('license_number', '')
            specialization = request.form.get('specialization', '')
            clinician_profile = ClinicianProfile(
                user_id=user.id,
                license_number=license_number,
                specialization=specialization
            )
            db.session.add(clinician_profile)

            db.session.commit()

            # Auto-login the user after successful registration
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            flash(f'Welcome to NeuroBeat, {user.first_name}!', 'success')

            return redirect(url_for('clinician_dashboard'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'error')
            return redirect(url_for('index'))

    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    """User login"""
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        session['user_id'] = user.id
        session['user_type'] = user.user_type
        flash(f'Welcome back, {user.first_name}!', 'success')

        if user.user_type == 'patient':
            return redirect(url_for('patient_dashboard'))
        else:
            return redirect(url_for('clinician_dashboard'))
    else:
        flash('Invalid username or password', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/patient/dashboard')
def patient_dashboard():
    """Patient dashboard - main interface for patients"""
    if 'user_id' not in session or session.get('user_type') != 'patient':
        flash('Please log in as a patient to access this page.', 'error')
        return redirect(url_for('index'))

    user = User.query.get(session['user_id'])
    patient_profile = user.patient_profile

    if not patient_profile:
        flash('Patient profile not found.', 'error')
        return redirect(url_for('index'))

    # Get recent sessions
    recent_sessions = TherapySession.query.filter_by(
        patient_id=patient_profile.id
    ).order_by(TherapySession.start_time.desc()).limit(5).all()

    # Calculate progress metrics
    total_sessions = TherapySession.query.filter_by(
        patient_id=patient_profile.id, 
        completed=True
    ).count()

    avg_accuracy = db.session.query(db.func.avg(TherapySession.accuracy_score)).filter_by(
        patient_id=patient_profile.id,
        completed=True
    ).scalar() or 0

    return render_template('patient_dashboard.html', 
                         user=user, 
                         patient_profile=patient_profile,
                         recent_sessions=recent_sessions,
                         total_sessions=total_sessions,
                         avg_accuracy=round(avg_accuracy, 1))

@app.route('/clinician/dashboard')
def clinician_dashboard():
    """Clinician dashboard - patient management interface"""
    if 'user_id' not in session or session.get('user_type') != 'clinician':
        flash('Please log in as a clinician to access this page.', 'error')
        return redirect(url_for('index'))

    user = User.query.get(session['user_id'])
    clinician_profile = user.clinician_profile

    if not clinician_profile:
        flash('Clinician profile not found.', 'error')
        return redirect(url_for('index'))

    # Get assigned patients
    patients = PatientProfile.query.filter_by(assigned_clinician_id=user.id).all()

    # Get unassigned patients
    unassigned_patients = PatientProfile.query.filter_by(assigned_clinician_id=None).all()

    return render_template('clinician_dashboard.html',
                         user=user,
                         clinician_profile=clinician_profile,
                         patients=patients,
                         unassigned_patients=unassigned_patients)

@app.route('/session/start', methods=['POST'])
def start_session():
    """Start a new therapy session"""
    if 'user_id' not in session or session.get('user_type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        from beat_generator import BeatGenerator

        user = User.query.get(session['user_id'])
        patient_profile = user.patient_profile

        session_type = request.json.get('session_type', 'gait_trainer')
        initial_bpm = float(request.json.get('initial_bpm', 60))
        target_bpm = float(request.json.get('target_bpm', 70))

        # Generate beats for stroke patients
        beat_url = None
        if patient_profile.condition == 'stroke':
            beat_generator = BeatGenerator()

            # Get optimal BPM for stroke therapy
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

            # Generate therapeutic beat
            beat_url = beat_generator.generate_stroke_therapy_beat(session_type, initial_bpm, patient_condition)

            # Get optimal BPM suggestion
            optimal_bpm = beat_generator.get_optimal_bpm_for_stroke_therapy(session_type, patient_condition)
            if abs(initial_bpm - optimal_bpm) > 10:
                initial_bpm = optimal_bpm

        # Create new session
        therapy_session = TherapySession(
            patient_id=patient_profile.id,
            session_type=session_type,
            initial_bpm=initial_bpm,
            target_bpm=target_bpm,
            start_time=datetime.utcnow(),
            generated_beat_url=beat_url,
            affected_limb=request.json.get('affected_limb'),
            cognitive_load_level=int(request.json.get('cognitive_load_level', 1))
        )

        db.session.add(therapy_session)
        db.session.commit()

        return jsonify({
            'session_id': therapy_session.id,
            'initial_bpm': initial_bpm,
            'target_bpm': target_bpm,
            'session_type': session_type,
            'beat_url': beat_url,
            'stroke_specific': patient_profile.condition == 'stroke'
        })

    except Exception as e:
        logging.error(f"Error starting session: {str(e)}")
        return jsonify({'error': 'Failed to start session'}), 500

@app.route('/session/<int:session_id>')
def session_view(session_id):
    """Session interface for therapy"""
    if 'user_id' not in session or session.get('user_type') != 'patient':
        flash('Please log in as a patient to access this page.', 'error')
        return redirect(url_for('index'))

    therapy_session = TherapySession.query.get_or_404(session_id)
    user = User.query.get(session['user_id'])

    # Verify session belongs to current patient
    if therapy_session.patient.user_id != user.id:
        flash('Unauthorized access to session.', 'error')
        return redirect(url_for('patient_dashboard'))

    return render_template('session.html', therapy_session=therapy_session)

@app.route('/session/update', methods=['POST'])
def update_session():
    """Update session metrics in real-time"""
    if 'user_id' not in session or session.get('user_type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        session_id = int(request.json.get('session_id'))
        current_bpm = float(request.json.get('current_bpm'))
        sync_accuracy = float(request.json.get('sync_accuracy', 0))

        # Add session metric
        metric = SessionMetrics(
            session_id=session_id,
            current_bpm=current_bpm,
            sync_accuracy=sync_accuracy,
            timestamp=datetime.utcnow()
        )
        db.session.add(metric)

        # Calculate BPM adjustment based on accuracy
        adjustment_bpm = current_bpm
        if sync_accuracy < 70:  # If accuracy is low, slow down slightly
            adjustment_bpm = max(current_bpm - 2, 40)
        elif sync_accuracy > 90:  # If accuracy is high, speed up slightly
            adjustment_bpm = min(current_bpm + 1, 120)

        if adjustment_bpm != current_bpm:
            metric.adjustment_made = True

        db.session.commit()

        return jsonify({
            'adjusted_bpm': adjustment_bpm,
            'sync_accuracy': sync_accuracy
        })

    except Exception as e:
        logging.error(f"Error updating session: {str(e)}")
        return jsonify({'error': 'Failed to update session'}), 500

@app.route('/session/<int:session_id>/update', methods=['POST'])
def update_session_legacy(session_id):
    """Update session metrics in real-time"""
    if 'user_id' not in session or session.get('user_type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        current_bpm = float(request.json.get('current_bpm'))
        sync_accuracy = float(request.json.get('sync_accuracy', 0))

        # Add session metric
        metric = SessionMetrics(
            session_id=session_id,
            current_bpm=current_bpm,
            sync_accuracy=sync_accuracy,
            timestamp=datetime.utcnow()
        )
        db.session.add(metric)

        # Calculate BPM adjustment based on accuracy
        adjustment_bpm = current_bpm
        if sync_accuracy < 70:  # If accuracy is low, slow down slightly
            adjustment_bpm = max(current_bpm - 2, 40)
        elif sync_accuracy > 90:  # If accuracy is high, speed up slightly
            adjustment_bpm = min(current_bpm + 1, 120)

        if adjustment_bpm != current_bpm:
            metric.adjustment_made = True

        db.session.commit()

        return jsonify({
            'adjusted_bpm': adjustment_bpm,
            'sync_accuracy': sync_accuracy
        })

    except Exception as e:
        logging.error(f"Error updating session: {str(e)}")
        return jsonify({'error': 'Failed to update session'}), 500

@app.route('/session/<int:session_id>/complete', methods=['POST'])
def complete_session(session_id):
    """Complete a therapy session"""
    if 'user_id' not in session or session.get('user_type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        therapy_session = TherapySession.query.get_or_404(session_id)
        user = User.query.get(session['user_id'])

        # Verify session belongs to current patient
        if therapy_session.patient.user_id != user.id:
            return jsonify({'error': 'Unauthorized'}), 401

        # Update session completion data
        therapy_session.end_time = datetime.utcnow()
        therapy_session.completed = True
        therapy_session.duration_seconds = int(request.json.get('duration', 0))
        therapy_session.final_bpm = float(request.json.get('final_bpm', therapy_session.initial_bpm))
        therapy_session.accuracy_score = float(request.json.get('accuracy_score', 0))
        therapy_session.notes = request.json.get('notes', '')

        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        logging.error(f"Error completing session: {str(e)}")
        return jsonify({'error': 'Failed to complete session'}), 500

@app.route('/baseline/assessment', methods=['GET', 'POST'])
def baseline_assessment():
    """Baseline assessment interface - clinicians only"""
    if 'user_id' not in session or session.get('user_type') != 'clinician':
        flash('Please log in as a clinician to access this page.', 'error')
        return redirect(url_for('index'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        try:
            assessment_type = request.form['assessment_type']
            measured_value = float(request.form['measured_value'])
            notes = request.form.get('notes', '')

            # Clinician assessing a patient
            patient_id = int(request.form['patient_id'])
            assessed_by = user.id

            assessment = BaselineAssessment(
                patient_id=patient_id,
                assessment_type=assessment_type,
                measured_value=measured_value,
                notes=notes,
                assessed_by=assessed_by
            )

            db.session.add(assessment)

            # Update patient profile with baseline values
            patient_profile = PatientProfile.query.get(patient_id)
            if assessment_type == 'gait':
                patient_profile.baseline_cadence = measured_value
                patient_profile.target_cadence = measured_value * 1.1  # 10% improvement target
            elif assessment_type == 'tapping':
                patient_profile.baseline_tapping_speed = measured_value
            elif assessment_type == 'speech':
                patient_profile.baseline_speech_rate = measured_value
                patient_profile.target_speech_rate = measured_value * 1.15  # 15% improvement target
            elif assessment_type == 'balance':
                # Store balance score in notes for now, can add dedicated column later
                assessment.notes = f"Berg Balance Scale Score: {measured_value}/56. " + (notes or "")
            elif assessment_type == 'coordination':
                # Store coordination time in notes for now
                assessment.notes = f"Finger-to-Nose Time: {measured_value}s per repetition. " + (notes or "")
            elif assessment_type == 'cognitive':
                # Store cognitive score in notes for now
                assessment.notes = f"MoCA Score: {measured_value}/30. " + (notes or "")

            db.session.commit()
            flash('Baseline assessment recorded successfully!', 'success')

            return redirect(url_for('clinician_dashboard'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error recording assessment: {str(e)}")
            flash('Failed to record assessment. Please try again.', 'error')

    # For GET request or form errors - only clinicians can access
    patients = PatientProfile.query.filter_by(assigned_clinician_id=user.id).all()
    return render_template('baseline_assessment.html', patients=patients, user=user)

@app.route('/progress/<int:patient_id>')
def progress_view(patient_id):
    """Progress visualization page"""
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('index'))

    user = User.query.get(session['user_id'])
    patient_profile = PatientProfile.query.get_or_404(patient_id)

    # Check authorization
    if user.user_type == 'patient' and patient_profile.user_id != user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('patient_dashboard'))
    elif user.user_type == 'clinician' and patient_profile.assigned_clinician_id != user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('clinician_dashboard'))

    # Get session data for charts
    sessions = TherapySession.query.filter_by(
        patient_id=patient_id,
        completed=True
    ).order_by(TherapySession.start_time.asc()).all()

    return render_template('progress.html', 
                         patient_profile=patient_profile,
                         sessions=sessions,
                         user=user)

@app.route('/api/progress/<int:patient_id>')
def progress_data(patient_id):
    """API endpoint for progress chart data"""
    from flask import session as flask_session
    
    if 'user_id' not in flask_session:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get(flask_session['user_id'])
    patient_profile = PatientProfile.query.get_or_404(patient_id)

    # Check authorization
    if user.user_type == 'patient' and patient_profile.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 401
    elif user.user_type == 'clinician' and patient_profile.assigned_clinician_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 401

    # Get therapy_sessions for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    therapy_sessions = TherapySession.query.filter(
        TherapySession.patient_id == patient_id,
        TherapySession.completed == True,
        TherapySession.start_time >= thirty_days_ago
    ).order_by(TherapySession.start_time.asc()).all()

    # Prepare chart data
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
    })

@app.route('/create_patient', methods=['POST'])
def create_patient():
    """Create a new patient account by clinician"""
    if 'user_id' not in session or session.get('user_type') != 'clinician':
        flash('Please log in as a clinician to access this page.', 'error')
        return redirect(url_for('index'))

    try:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        condition = request.form['condition']

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('clinician_dashboard'))

        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('clinician_dashboard'))

        # Create new patient user
        user = User(
            username=username,
            email=email,
            user_type='patient',
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Get the user ID

        # Create patient profile with stroke-specific fields
        patient_profile = PatientProfile(
            user_id=user.id,
            condition=condition,
            assigned_clinician_id=session['user_id']
        )

        # Add stroke-specific fields if condition is stroke
        if condition == 'stroke':
            patient_profile.stroke_affected_side = request.form.get('stroke_affected_side')
            patient_profile.stroke_severity = request.form.get('stroke_severity')
            patient_profile.aphasia_type = request.form.get('aphasia_type')
            patient_profile.dysarthria_severity = request.form.get('dysarthria_severity')
            patient_profile.motor_impairment_level = request.form.get('motor_impairment_level')
            patient_profile.cognitive_status = request.form.get('cognitive_status')
            patient_profile.emotional_status = request.form.get('emotional_status')
            patient_profile.preferred_music_genre = request.form.get('preferred_music_genre')
            patient_profile.preferred_beat_sound = request.form.get('preferred_beat_sound', 'metronome')
        
        # Set initial baseline values from clinician input or defaults if not provided
        # This part needs to be integrated with the UI to allow clinicians to set these.
        # For now, assuming these might be set directly if available in the form or defaults.
        # The core change is that the patient cannot set these directly in a patient-initiated flow.
        if condition == 'stroke': # Example: setting baseline for stroke patients
            patient_profile.baseline_cadence = float(request.form.get('baseline_cadence', 120)) # Default cadence
            patient_profile.target_cadence = float(request.form.get('target_cadence', patient_profile.baseline_cadence * 1.1)) # Default target
            patient_profile.baseline_tapping_speed = float(request.form.get('baseline_tapping_speed', 5)) # Default tapping speed
            patient_profile.baseline_speech_rate = float(request.form.get('baseline_speech_rate', 150)) # Default speech rate
            patient_profile.target_speech_rate = float(request.form.get('target_speech_rate', patient_profile.baseline_speech_rate * 1.15)) # Default target speech rate
            # Add other baseline fields as needed, ensuring they are set by the clinician during patient creation or later.


        db.session.add(patient_profile)
        db.session.commit()
        flash(f'Patient {first_name} {last_name} created successfully and assigned to you!', 'success')

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating patient: {str(e)}")
        flash('Failed to create patient. Please try again.', 'error')

    return redirect(url_for('clinician_dashboard'))

@app.route('/assign_patient', methods=['POST'])
def assign_patient():
    """Assign patient to clinician"""
    if 'user_id' not in session or session.get('user_type') != 'clinician':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        patient_id = int(request.json.get('patient_id'))
        clinician_id = session['user_id']

        patient_profile = PatientProfile.query.get_or_404(patient_id)
        patient_profile.assigned_clinician_id = clinician_id

        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        logging.error(f"Error assigning patient: {str(e)}")
        return jsonify({'error': 'Failed to assign patient'}), 500

@app.route('/patient/<int:patient_id>/details')
def patient_details(patient_id):
    """Detailed patient view for clinicians"""
    if 'user_id' not in session or session.get('user_type') != 'clinician':
        flash('Please log in as a clinician to access this page.', 'error')
        return redirect(url_for('index'))

    user = User.query.get(session['user_id'])
    patient_profile = PatientProfile.query.get_or_404(patient_id)

    # Check if patient is assigned to this clinician
    if patient_profile.assigned_clinician_id != user.id:
        flash('Unauthorized access to patient details.', 'error')
        return redirect(url_for('clinician_dashboard'))

    # Get patient's recent sessions
    recent_sessions = TherapySession.query.filter_by(
        patient_id=patient_id
    ).order_by(TherapySession.start_time.desc()).limit(10).all()

    # Get baseline assessments
    assessments = BaselineAssessment.query.filter_by(
        patient_id=patient_id
    ).order_by(BaselineAssessment.created_at.desc()).all()

    # Calculate progress statistics
    total_sessions = TherapySession.query.filter_by(
        patient_id=patient_id, 
        completed=True
    ).count()

    avg_accuracy = db.session.query(db.func.avg(TherapySession.accuracy_score)).filter_by(
        patient_id=patient_id,
        completed=True
    ).scalar() or 0

    return render_template('patient_details.html',
                         patient_profile=patient_profile,
                         recent_sessions=recent_sessions,
                         assessments=assessments,
                         total_sessions=total_sessions,
                         avg_accuracy=round(avg_accuracy, 1),
                         user=user)

@app.route('/patient/<int:patient_id>/credentials')
def patient_credentials(patient_id):
    """View patient login credentials"""
    if 'user_id' not in session or session.get('user_type') != 'clinician':
        flash('Please log in as a clinician to access this page.', 'error')
        return redirect(url_for('index'))

    user = User.query.get(session['user_id'])
    patient_profile = PatientProfile.query.get_or_404(patient_id)

    # Check if patient is assigned to this clinician
    if patient_profile.assigned_clinician_id != user.id:
        flash('Unauthorized access to patient credentials.', 'error')
        return redirect(url_for('clinician_dashboard'))

    patient_user = patient_profile.user
    return render_template('patient_credentials.html',
                         patient_profile=patient_profile,
                         patient_user=patient_user,
                         user=user)