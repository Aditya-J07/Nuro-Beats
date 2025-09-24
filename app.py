import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging for production
if os.environ.get("VERCEL"):
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def create_app():
    """Application factory pattern for better deployment compatibility"""
    app = Flask(__name__)
    
    # Security: Require SESSION_SECRET in production
    session_secret = os.environ.get("SESSION_SECRET")
    if not session_secret:
        if os.environ.get("VERCEL"):
            raise ValueError("SESSION_SECRET environment variable is required for production deployment")
        else:
            session_secret = "neurobeat-secret-key-dev"
            logging.warning("Using default secret key for development only")
    
    app.secret_key = session_secret
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Database configuration
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        if os.environ.get("VERCEL"):
            raise ValueError("DATABASE_URL environment variable is required for production deployment")
        else:
            database_url = "sqlite:///neurobeat.db"
    
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions
    db.init_app(app)
    
    return app

# Create the app instance
app = create_app()

# Initialize database tables (only in development or on first run)
if not os.environ.get("VERCEL") or os.environ.get("INIT_DB"):
    with app.app_context():
        # Import models to ensure tables are created
        import models  # noqa: F401
        try:
            db.create_all()
            logging.info("Database tables created successfully")
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
            if not os.environ.get("VERCEL"):
                raise
