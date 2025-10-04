from flask import Blueprint

patients_bp = Blueprint('patients', __name__)

from api.patients import routes
