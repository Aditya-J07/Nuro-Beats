# NeuroBeat - AI-Powered Music Therapy Platform

## Overview

NeuroBeat is a clinical-grade neurorehabilitation platform that uses AI-driven rhythmic therapy to help patients with Parkinson's disease and stroke recovery. The system leverages auditory-motor entrainment principles, where patients synchronize movements to personalized beats to bypass damaged neural pathways and improve motor control, gait, speech, and fine motor skills.

The platform provides a complete clinical workflow: baseline assessments establish patient capabilities, clinicians prescribe personalized rhythmic therapy targets, patients participate in guided therapy sessions with real-time adaptation, and comprehensive progress tracking enables data-driven treatment adjustments.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web application with SQLAlchemy ORM for database operations
- **Database**: SQLite for development with configurable PostgreSQL support via environment variables
- **Session Management**: Flask sessions with server-side storage for user authentication
- **Security**: Werkzeug password hashing for secure credential storage

### Frontend Architecture
- **Template Engine**: Jinja2 templating with Bootstrap dark theme for responsive UI
- **JavaScript Libraries**: 
  - Tone.js for real-time audio synthesis and beat generation
  - Chart.js for progress visualization and metrics display
  - Feather Icons for consistent iconography
- **Real-time Features**: JavaScript-based session management with periodic server updates

### Data Model Design
- **User Management**: Dual-role system supporting patients and clinicians with profile-specific data
- **Patient Profiles**: Condition tracking (Parkinson's/stroke), baseline measurements, and clinician assignments
- **Session Tracking**: Therapy sessions with real-time metrics, duration tracking, and accuracy scoring
- **Assessment System**: Baseline assessments for gait, tapping, and speech capabilities

### Audio Processing Architecture
- **Beat Generation**: Client-side Tone.js synthesizer for responsive audio feedback
- **Adaptive Tempo**: Real-time BPM adjustment based on patient performance
- **Session Types**: Multiple therapy modes including gait training, speech rhythm, and fine motor exercises

### Clinical Workflow Design
- **Assessment Phase**: Multi-modal baseline testing (gait, tapping, speech)
- **Prescription Phase**: Clinician-defined target parameters and therapy goals  
- **Therapy Phase**: Interactive sessions with visual feedback and real-time adaptation
- **Monitoring Phase**: Progress tracking with detailed analytics and trend visualization

## External Dependencies

### Core Libraries
- **Flask**: Web framework for application routing and request handling
- **SQLAlchemy**: Database ORM for data persistence and relationships
- **Werkzeug**: Security utilities for password hashing and request processing

### Frontend Assets
- **Bootstrap**: UI framework with dark theme styling from Replit CDN
- **Tone.js**: Web Audio API wrapper for audio synthesis and timing
- **Chart.js**: Data visualization library for progress charts and metrics
- **Feather Icons**: Scalable vector icon library for UI elements

### Development Dependencies
- **Python Standard Library**: Logging, datetime, and JSON processing
- **Browser APIs**: Web Audio API for sound generation, device sensors for motion tracking

### Database Configuration
- **SQLite**: Default local database for development and testing
- **PostgreSQL**: Production database support via DATABASE_URL environment variable
- **Connection Pooling**: Configured with automatic reconnection and health checks