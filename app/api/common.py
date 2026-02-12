from datetime import date
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import common_bp
from app.extensions import db
from app.models import User, Dish, Menu, MenuItem, Review, MealRecord, Subscription, Inventory, Notification


@common_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    profile_data = user.to_dict()
    
    if user.role == 'student':
        subscription = user.subscriptions.filter_by(is_active=True).first()
        if subscription:
            profile_data['subscription'] = subscription.to_dict()
        
        allergies = [a.to_dict() for a in user.allergies]
        profile_data['allergies'] = allergies
    
    return jsonify({'profile': profile_data}), 200


@common_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    if 'full_name' in data:
        user.full_name = data['full_name']
    
    if 'new_password' in data:
        current_password = data.get('current_password')
        if not current_password:
            return jsonify({'error': 'Текущий пароль обязателен'}), 400
        
        if not user.check_password(current_password):
            return jsonify({'error': 'Неверный текущий пароль'}), 401
        
        user.set_password(data['new_password'])
    
    db.session.commit()
    
    return jsonify({
        'message': 'Профиль обновлен',
        'profile': user.to_dict()
    }), 200


@common_bp.route('/dishes', methods=['GET'])
@jwt_required()
def get_available_dishes():
    dishes = Dish.query.filter_by(is_available=True).order_by(Dish.name).all()
    
    dishes_data = []
    for dish in dishes:
        dish_dict = dish.to_dict()
        
        reviews = Review.query.filter_by(dish_id=dish.id).all()
        if reviews:
            dish_dict['average_rating'] = round(
                sum(r.rating for r in reviews) / len(reviews), 1
            )
            dish_dict['reviews_count'] = len(reviews)
        else:
            dish_dict['average_rating'] = None
            dish_dict['reviews_count'] = 0
        
        dishes_data.append(dish_dict)
    
    return jsonify({'dishes': dishes_data}), 200


@common_bp.route('/dishes/<int:dish_id>', methods=['GET'])
@jwt_required()
def get_dish_details(dish_id):
    dish = Dish.query.get(dish_id)
    
    if not dish:
        return jsonify({'error': 'Блюдо не найдено'}), 404
    
    dish_data = dish.to_dict()
    
    reviews = Review.query.filter_by(dish_id=dish_id).order_by(
        Review.created_at.desc()
    ).all()
    
    reviews_data = []
    for review in reviews:
        review_dict = review.to_dict()
        user = User.query.get(review.user_id)
        if user:
            review_dict['user_name'] = user.full_name
        reviews_data.append(review_dict)
    
    dish_data['reviews'] = reviews_data
    
    if reviews:
        dish_data['average_rating'] = round(
            sum(r.rating for r in reviews) / len(reviews), 1
        )
    else:
        dish_data['average_rating'] = None
    
    return jsonify({'dish': dish_data}), 200


@common_bp.route('/menu/today', methods=['GET'])
@jwt_required()
def get_today_menu():
    today = date.today()
    meal_type = request.args.get('meal_type', 'lunch')
    
    menu = Menu.query.filter_by(
        menu_date=today,
        meal_type=meal_type,
        is_active=True
    ).first()
    
    if not menu:
        return jsonify({
            'menu': None,
            'dishes': [],
            'message': 'На сегодня меню недоступно'
        }), 200
    
    menu_items = MenuItem.query.filter_by(menu_id=menu.id).all()
    dishes = []
    
    for item in menu_items:
        dish = Dish.query.get(item.dish_id)
        if dish and dish.is_available:
            dish_data = dish.to_dict()
            
            reviews = Review.query.filter_by(dish_id=dish.id).all()
            if reviews:
                dish_data['average_rating'] = round(
                    sum(r.rating for r in reviews) / len(reviews), 1
                )
                dish_data['reviews_count'] = len(reviews)
            else:
                dish_data['average_rating'] = None
                dish_data['reviews_count'] = 0
            
            dishes.append(dish_data)
    
    return jsonify({
        'menu': menu.to_dict(),
        'dishes': dishes
    }), 200


@common_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    dashboard_data = {
        'user': user.to_dict(),
        'role': user.role
    }
    
    if user.role == 'student':
        subscription = user.subscriptions.filter_by(is_active=True).first()
        dashboard_data['subscription'] = subscription.to_dict() if subscription else None
        
        unread_count = len([n for n in user.notifications if not n.is_read])
        dashboard_data['unread_notifications'] = unread_count
        
        recent_meals = user.meal_records.order_by(
            MealRecord.received_at.desc()
        ).limit(5).all()
        
        # Include dish name from menu items
        recent_meals_data = []
        for meal in recent_meals:
            meal_dict = meal.to_dict()
            # Get dish name from menu items
            menu_items = MenuItem.query.filter_by(menu_id=meal.menu_id).first()
            if menu_items:
                dish = Dish.query.get(menu_items.dish_id)
                meal_dict['dish_name'] = dish.name if dish else 'Unknown'
            else:
                meal_dict['dish_name'] = 'Unknown'
            meal_dict['status'] = 'Получен' if meal.is_confirmed else 'Ожидает'
            recent_meals_data.append(meal_dict)
        
        dashboard_data['recent_meals'] = recent_meals_data
    
    elif user.role == 'cook':
        today = date.today()
        menu = Menu.query.filter_by(
            menu_date=today,
            meal_type='lunch',
            is_active=True
        ).first()
        
        if menu:
            meals_served = MealRecord.query.filter_by(
                menu_id=menu.id,
                is_confirmed=True
            ).count()
            dashboard_data['today_meals_served'] = meals_served
        else:
            dashboard_data['today_meals_served'] = 0
        
        low_stock = 0
        for item in Inventory.query.all():
            if item.is_low_stock():
                low_stock += 1
        dashboard_data['low_stock_items'] = low_stock
    
    elif user.role == 'admin':
        dashboard_data['total_students'] = User.query.filter_by(
            role='student'
        ).count()
        dashboard_data['total_cooks'] = User.query.filter_by(
            role='cook'
        ).count()
        dashboard_data['active_subscriptions'] = Subscription.query.filter_by(
            is_active=True
        ).count()
    
    return jsonify(dashboard_data), 200


# ============ NOTIFICATION ENDPOINTS (Available to all authenticated users) ============

@common_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get notifications for the current user - available to all authenticated users"""
    user_id = get_jwt_identity()
    
    unread = Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).order_by(Notification.created_at.desc()).all()
    
    read_limit = max(0, 20 - len(unread))
    read = Notification.query.filter_by(
        user_id=user_id,
        is_read=True
    ).order_by(Notification.created_at.desc()).limit(read_limit).all()
    
    notifications = unread + read
    
    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': len(unread)
    }), 200


@common_bp.route('/notifications/<int:notification_id>/read', methods=['PUT', 'POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """Mark a notification as read - available to all authenticated users"""
    user_id = get_jwt_identity()
    
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=user_id
    ).first()
    
    if not notification:
        return jsonify({'error': 'Уведомление не найдено'}), 404
    
    notification.mark_as_read()
    db.session.commit()
    
    return jsonify({'message': 'Уведомление отмечено как прочитанное'}), 200


@common_bp.route('/notifications/read-all', methods=['PUT', 'POST'])
@jwt_required()
def mark_all_notifications_read():
    """Mark all notifications as read - available to all authenticated users"""
    user_id = get_jwt_identity()
    
    Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    
    return jsonify({'message': 'Все уведомления отмечены как прочитанные'}), 200
