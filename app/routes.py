from flask import render_template, Blueprint, g, redirect, url_for
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from app.models import User

pages_bp = Blueprint('pages', __name__)


@pages_bp.before_request
def load_user():
    g.current_user = None
    try:
        verify_jwt_in_request(optional=True, locations=['cookies', 'headers'])
        user_id = get_jwt_identity()
        if user_id:
            g.current_user = User.query.get(int(user_id))
    except Exception:
        pass


@pages_bp.route('/')
def index():
    if g.current_user:
        if g.current_user.role == 'admin':
            return redirect(url_for('pages.admin_dashboard'))
        elif g.current_user.role == 'cook':
            return redirect(url_for('pages.cook_dashboard'))
        else:
            return redirect(url_for('pages.student_dashboard'))
    return render_template('auth/login.html', current_user=None)


@pages_bp.route('/login')
def login_page():
    if g.current_user:
        return redirect(url_for('pages.index'))
    return render_template('auth/login.html', current_user=None)


@pages_bp.route('/register')
def register_page():
    if g.current_user:
        return redirect(url_for('pages.index'))
    return render_template('auth/register.html', current_user=None)


@pages_bp.route('/student/dashboard')
def student_dashboard():
    if not g.current_user or g.current_user.role != 'student':
        return redirect(url_for('pages.login_page'))
    return render_template('student/dashboard.html', current_user=g.current_user)


@pages_bp.route('/student/menu')
def student_menu():
    if not g.current_user or g.current_user.role != 'student':
        return redirect(url_for('pages.login_page'))
    return render_template('student/menu.html', current_user=g.current_user)


@pages_bp.route('/student/payment')
def student_payment():
    if not g.current_user or g.current_user.role != 'student':
        return redirect(url_for('pages.login_page'))
    return render_template('student/payment.html', current_user=g.current_user)


@pages_bp.route('/student/allergies')
def student_allergies():
    if not g.current_user or g.current_user.role != 'student':
        return redirect(url_for('pages.login_page'))
    return render_template('student/allergies.html', current_user=g.current_user)


@pages_bp.route('/student/reviews')
def student_reviews():
    if not g.current_user or g.current_user.role != 'student':
        return redirect(url_for('pages.login_page'))
    return render_template('student/reviews.html', current_user=g.current_user)


@pages_bp.route('/cook/dashboard')
def cook_dashboard():
    if not g.current_user or g.current_user.role != 'cook':
        return redirect(url_for('pages.login_page'))
    return render_template('cook/dashboard.html', current_user=g.current_user)


@pages_bp.route('/cook/meal-tracking')
def cook_meal_tracking():
    if not g.current_user or g.current_user.role != 'cook':
        return redirect(url_for('pages.login_page'))
    return render_template('cook/meal_tracking.html', current_user=g.current_user)


@pages_bp.route('/cook/inventory')
def cook_inventory():
    if not g.current_user or g.current_user.role != 'cook':
        return redirect(url_for('pages.login_page'))
    return render_template('cook/inventory.html', current_user=g.current_user)


@pages_bp.route('/cook/purchase-requests')
def cook_purchase_requests():
    if not g.current_user or g.current_user.role != 'cook':
        return redirect(url_for('pages.login_page'))
    return render_template('cook/purchase_requests.html', current_user=g.current_user)


@pages_bp.route('/admin/dashboard')
def admin_dashboard():
    if not g.current_user or g.current_user.role != 'admin':
        return redirect(url_for('pages.login_page'))
    return render_template('admin/dashboard.html', current_user=g.current_user)


@pages_bp.route('/admin/statistics')
def admin_statistics():
    if not g.current_user or g.current_user.role != 'admin':
        return redirect(url_for('pages.login_page'))
    return render_template('admin/statistics.html', current_user=g.current_user)


@pages_bp.route('/admin/purchase-approval')
def admin_purchase_approval():
    if not g.current_user or g.current_user.role != 'admin':
        return redirect(url_for('pages.login_page'))
    return render_template('admin/purchase_approval.html', current_user=g.current_user)


@pages_bp.route('/admin/reports')
def admin_reports():
    if not g.current_user or g.current_user.role != 'admin':
        return redirect(url_for('pages.login_page'))
    return render_template('admin/reports.html', current_user=g.current_user)


@pages_bp.route('/dashboard')
def dashboard():
    """Generic dashboard route that redirects based on user role"""
    if not g.current_user:
        return redirect(url_for('pages.login_page'))
    if g.current_user.role == 'admin':
        return redirect(url_for('pages.admin_dashboard'))
    elif g.current_user.role == 'cook':
        return redirect(url_for('pages.cook_dashboard'))
    else:
        return redirect(url_for('pages.student_dashboard'))
