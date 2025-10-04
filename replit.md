# NeuroBeat - AI-Powered Music Therapy Platform

## Overview

NeuroBeat is a clinical-grade neurorehabilitation platform that uses AI-driven rhythmic therapy to help patients with Parkinson's disease and stroke recovery. The system leverages auditory-motor entrainment principles, where patients synchronize movements to personalized beats to bypass damaged neural pathways and improve motor control, gait, speech, and fine motor skills.

The platform provides a complete clinical workflow: baseline assessments establish patient capabilities, clinicians prescribe personalized rhythmic therapy targets, patients participate in guided therapy sessions with real-time adaptation, and comprehensive progress tracking enables data-driven treatment adjustments.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask REST API with SQLAlchemy ORM and JWT authentication
- **API Server**: Runs on port 8000 (internal) with Flask development server
- **Database**: SQLite for development with configurable PostgreSQL support via DATABASE_URL
- **Authentication**: JWT tokens with Flask-JWT-Extended, bearer token authentication
- **Security**: 
  - Required environment secrets (SESSION_SECRET, JWT_SECRET_KEY)
  - CORS configured for Replit domains and localhost
  - Password hashing with Werkzeug
  - Token refresh mechanism for session persistence

### Frontend Architecture
- **Framework**: React 19 with Vite 7 build tool
- **Dev Server**: Runs on port 5000 (public-facing) with HMR enabled
- **API Integration**: Axios with interceptors for token management and automatic refresh
- **Proxy Configuration**: Vite proxies `/api` requests to backend on port 8000
- **State Management**: React Context API for authentication state
- **UI Libraries** (planned):
  - Tone.js for real-time audio synthesis and beat generation
  - Chart.js with react-chartjs-2 for progress visualization
  - React Router for navigation

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

## Recent Changes

### October 4, 2025 - Vercel to Replit Migration
- **Migration Completed**: Successfully migrated NeuroBeat from Vercel to Replit
- **Security Improvements**:
  - Removed hardcoded default secrets from codebase
  - Enforced required environment variables: SESSION_SECRET and JWT_SECRET_KEY
  - Application now fails fast if secrets are missing, preventing insecure deployments
- **Architecture Update**:
  - Dual-server setup: Flask REST API backend (port 8000) + Vite React frontend (port 5000)
  - Frontend on port 5000 (required by Replit for public access)
  - Backend on internal port 8000 with Vite proxy for API requests
- **Frontend Configuration**:
  - Installed Node.js 20 and all React dependencies
  - Configured Vite to allow all hosts for Replit proxy compatibility
  - Set up proper HMR (Hot Module Replacement) with WebSocket configuration
  - API proxy routes `/api` requests to backend server
- **Backend Configuration**:
  - Updated Flask CORS to allow Replit domains and localhost
  - Configured API to run on port 8000 via BACKEND_PORT environment variable
  - Both Flask backends (api_main.py and main.py) now require proper secrets
- **Workflow Setup**:
  - Unified startup script (start.sh) runs both servers simultaneously
  - Backend starts via `uv run python api_main.py` with proper Python environment
  - Frontend starts via `npm run dev` in frontend-react directory
  - Automatic cleanup on shutdown for both processes
- **Git Configuration**: 
  - Added comprehensive .gitignore for Python, Node.js, databases, and environment files
  - Excludes node_modules, .pythonlibs, instance/, and .env files
- **Application Status**: 
  - Both servers running without errors
  - API endpoints responding correctly (tested via curl)
  - Proxy routing working (frontend successfully forwards API requests to backend)
  - Ready for UI development

## Development Setup

### Required Environment Variables
The following secrets must be set in Replit Secrets before running:
- **SESSION_SECRET**: Strong random string for session encryption (32+ characters recommended)
- **JWT_SECRET_KEY**: Strong random string for JWT token signing (32+ characters recommended)

Optional environment variables:
- **DATABASE_URL**: PostgreSQL connection string (defaults to SQLite at `instance/neurobeat.db`)
- **BACKEND_PORT**: Backend server port (defaults to 8000)

### Running the Application
Execute the startup script: `bash start.sh`

This starts both servers:
1. Flask API backend on port 8000
2. Vite React frontend on port 5000 (accessible via Replit's webview)

### Key Files

**Backend:**
- **api_main.py**: REST API entry point
- **api/__init__.py**: Flask app factory with JWT and CORS configuration
- **api/auth/routes.py**: Authentication endpoints (login, register, refresh)
- **api/patients/routes.py**: Patient management endpoints
- **api/sessions/routes.py**: Therapy session endpoints
- **api/assessments/routes.py**: Assessment endpoints
- **api/models.py**: SQLAlchemy database models

**Legacy Backend** (template-based, may be deprecated):
- **main.py**: Old application entry point
- **app.py**: Old Flask app initialization
- **routes.py**: Old template-based routes

**Frontend:**
- **frontend-react/src/App.jsx**: React application root (currently Vite boilerplate)
- **frontend-react/src/services/api.js**: Axios API client with auth interceptors
- **frontend-react/src/context/AuthContext.jsx**: Authentication state management
- **frontend-react/vite.config.js**: Vite configuration with proxy setup

**Infrastructure:**
- **start.sh**: Unified startup script for both servers
- **pyproject.toml**: Python dependencies managed by uv
- **frontend-react/package.json**: Node.js dependencies

### Database
- Development database is SQLite stored at `instance/neurobeat.db`
- Database tables are automatically created on app startup via Flask-SQLAlchemy
- For production, set DATABASE_URL environment variable to PostgreSQL connection string