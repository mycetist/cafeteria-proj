from flask import Blueprint

auth_bp = Blueprint('auth', __name__)
student_bp = Blueprint('student', __name__)
cook_bp = Blueprint('cook', __name__)
admin_bp = Blueprint('admin', __name__)
common_bp = Blueprint('common', __name__)

from app.api import auth, student, cook, admin, common