from flask import Blueprint

assessments_bp = Blueprint('assessments', __name__)

from api.assessments import routes
