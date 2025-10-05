from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from sqlalchemy.orm import DeclarativeBase
from datetime import timedelta
import os

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    session_secret = os.environ.get("SESSION_SECRET")
    if not session_secret:
        raise ValueError("SESSION_SECRET environment variable is required")
    
    app.config["SECRET_KEY"] = session_secret  # ✅ FIXED: Was hardcoded!
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///instance/neurobeat.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    jwt_secret = os.environ.get("JWT_SECRET_KEY")
    if not jwt_secret:
        raise ValueError("JWT_SECRET_KEY environment variable is required")
    
    app.config["JWT_SECRET_KEY"] = jwt_secret  # ✅ FIXED: Was hardcoded!
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
    
    repl_slug = os.environ.get("REPL_SLUG", "")
    repl_owner = os.environ.get("REPL_OWNER", "")
    
    allowed_origins = []
    if repl_slug and repl_owner:
        allowed_origins.append(f"https://{repl_slug}.{repl_owner}.repl.co")
        allowed_origins.append(f"https://{repl_slug}-5173.{repl_owner}.repl.co")
    
    # ✅ Added your Vercel URL
    allowed_origins.extend([
        "https://neuro-beats.vercel.app",  # Your production frontend
        "http://localhost:5173",
        "http://localhost:5000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5000"
    ])
    
    CORS(app, 
         resources={r"/api/*": {"origins": allowed_origins}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    db.init_app(app)
    jwt.init_app(app)
    
    with app.app_context():
        from api import models
        db.create_all()
    
    from api.auth import auth_bp
    from api.patients import patients_bp
    from api.sessions import sessions_bp
    from api.assessments import assessments_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(patients_bp, url_prefix='/api/patients')
    app.register_blueprint(sessions_bp, url_prefix='/api/sessions')
    app.register_blueprint(assessments_bp, url_prefix='/api/assessments')
    
    return app
