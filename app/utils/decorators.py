from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User


def student_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        if not user.is_active:
            return jsonify({'error': 'Аккаунт неактивен'}), 403
        
        if user.role != 'student':
            return jsonify({'error': 'Требуется роль ученика'}), 403
        
        return fn(*args, **kwargs)
    return wrapper


def cook_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        if not user.is_active:
            return jsonify({'error': 'Аккаунт неактивен'}), 403
        
        if user.role != 'cook':
            return jsonify({'error': 'Требуется роль повара'}), 403
        
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        if not user.is_active:
            return jsonify({'error': 'Аккаунт неактивен'}), 403
        
        if user.role != 'admin':
            return jsonify({'error': 'Требуется роль администратора'}), 403
        
        return fn(*args, **kwargs)
    return wrapper
