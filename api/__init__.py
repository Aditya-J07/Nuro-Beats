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
    
    app.config["SECRET_KEY"] = os.environ.get("SESSION_SECRET", "neurobeat-secret-key-dev")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///neurobeat.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", app.config["SECRET_KEY"])
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
    
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    CORS(app, 
         resources={r"/api/*": {"origins": frontend_url}},
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
