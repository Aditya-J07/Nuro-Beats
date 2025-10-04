from flask import Blueprint

sessions_bp = Blueprint('sessions', __name__)

from api.sessions import routes
