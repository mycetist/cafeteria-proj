from datetime import datetime, date, timedelta
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.api import student_bp
from app.extensions import db
from app.utils.decorators import student_required
from app.models import (
    User, Dish, Menu, MenuItem, Payment, Subscription,
    MealRecord, Allergy, Review, Notification
)


@student_bp.route('/menu', methods=['GET'])
@student_required
def get_current_menu():
    today = date.today()
    meal_type = request.args.get('meal_type', 'lunch')
    
    menu = Menu.query.filter_by(
        menu_date=today,
        meal_type=meal_type,
        is_active=True
    ).first()
    
    if not menu:
        return jsonify({'menu': None, 'message': 'На сегодня меню недоступно'}), 200
    
    menu_items = MenuItem.query.filter_by(menu_id=menu.id).all()
    dishes = []
    
    for item in menu_items:
        dish = Dish.query.get(item.dish_id)
        if dish and dish.is_available:
            dish_data = dish.to_dict()
            reviews = Review.query.filter_by(dish_id=dish.id).all()
            if reviews:
                dish_data['average_rating'] = sum(r.rating for r in reviews) / len(reviews)
                dish_data['reviews_count'] = len(reviews)
            else:
                dish_data['average_rating'] = None
                dish_data['reviews_count'] = 0
            dishes.append(dish_data)
    
    # Include items with dish data for template compatibility
    menu_data = menu.to_dict()
    menu_data['items'] = []
    for item in menu_items:
        dish = Dish.query.get(item.dish_id)
        if dish and dish.is_available:
            item_data = item.to_dict()
            item_data['dish'] = dish.to_dict()
            menu_data['items'].append(item_data)
    
    return jsonify({
        'menu': menu_data,
        'dishes': dishes
    }), 200


@student_bp.route('/menu/<string:menu_date>', methods=['GET'])
@student_required
def get_menu_by_date(menu_date):
    try:
        target_date = datetime.strptime(menu_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Неверный формат даты. Используйте ГГГГ-ММ-ДД'}), 400
    
    meal_type = request.args.get('meal_type', 'lunch')
    
    menu = Menu.query.filter_by(
        menu_date=target_date,
        meal_type=meal_type,
        is_active=True
    ).first()
    
    if not menu:
        return jsonify({'menu': None, 'message': 'На эту дату меню недоступно'}), 200
    
    menu_items = MenuItem.query.filter_by(menu_id=menu.id).all()
    dishes = []
    
    for item in menu_items:
        dish = Dish.query.get(item.dish_id)
        if dish and dish.is_available:
            dishes.append(dish.to_dict())
    
    # Include items with dish data for template compatibility
    menu_data = menu.to_dict()
    menu_data['items'] = []
    for item in menu_items:
        dish = Dish.query.get(item.dish_id)
        if dish and dish.is_available:
            item_data = item.to_dict()
            item_data['dish'] = dish.to_dict()
            menu_data['items'].append(item_data)
    
    return jsonify({
        'menu': menu_data,
        'dishes': dishes
    }), 200


@student_bp.route('/payment', methods=['POST'])
@student_required
def create_payment():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    amount = data.get('amount')
    if not amount:
        return jsonify({'error': 'Сумма обязательна'}), 400
    
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'error': 'Сумма должна быть положительной'}), 400
    except ValueError:
        return jsonify({'error': 'Неверная сумма'}), 400
    
    payment = Payment(
        user_id=user_id,
        amount=amount,
        payment_type='single',
        status='completed',
        transaction_id=f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{user_id}"
    )
    
    db.session.add(payment)
    db.session.commit()
    
    notification = Notification(
        user_id=user_id,
        title='Оплата успешна',
        message=f'Ваш платеж на сумму {amount:.2f} ₽ успешно обработан.'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'message': 'Оплата успешна',
        'payment': payment.to_dict()
    }), 201


@student_bp.route('/subscription', methods=['GET'])
@student_required
def get_subscription():
    user_id = get_jwt_identity()
    
    subscription = Subscription.query.filter_by(
        user_id=user_id,
        is_active=True
    ).first()
    
    if not subscription:
        return jsonify({'subscription': None}), 200
    
    return jsonify({'subscription': subscription.to_dict()}), 200


@student_bp.route('/subscription', methods=['POST'])
@student_required
def create_subscription():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    subscription_type = data.get('subscription_type')
    if subscription_type not in ['weekly', 'monthly']:
        return jsonify({'error': 'Тип абонемента должен быть weekly или monthly'}), 400
    
    today = date.today()
    if subscription_type == 'weekly':
        days_to_add = 7
        amount = 700.00
        meals_to_add = 5
    else:
        days_to_add = 30
        amount = 2500.00
        meals_to_add = 20
    
    existing = Subscription.query.filter_by(user_id=user_id, is_active=True).first()
    
    if existing:
        # Extend existing subscription
        existing.end_date = existing.end_date + timedelta(days=days_to_add)
        existing.meals_remaining = existing.meals_remaining + meals_to_add
        existing.subscription_type = subscription_type
        subscription = existing
        message = f'Абонемент продлён до {existing.end_date}. Всего обедов: {existing.meals_remaining}'
    else:
        # Create new subscription
        end_date = today + timedelta(days=days_to_add)
        subscription = Subscription(
            user_id=user_id,
            subscription_type=subscription_type,
            start_date=today,
            end_date=end_date,
            is_active=True,
            meals_remaining=meals_to_add
        )
        db.session.add(subscription)
        message = f'Ваш {subscription_type} абонемент активен до {end_date}.'
    
    payment = Payment(
        user_id=user_id,
        amount=amount,
        payment_type='subscription',
        status='completed',
        transaction_id=f"SUB{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{user_id}"
    )
    db.session.add(payment)
    db.session.commit()
    
    notification = Notification(
        user_id=user_id,
        title='Абонемент активирован',
        message=message
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'message': 'Абонемент успешно создан',
        'subscription': subscription.to_dict(),
        'payment': payment.to_dict()
    }), 201


@student_bp.route('/meal/confirm', methods=['POST'])
@student_required
def confirm_meal():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    meal_type = data.get('meal_type', 'lunch')
    menu_id = data.get('menu_id')
    
    # If menu_id not provided, find today's menu for the meal type
    if not menu_id:
        today = date.today()
        menu = Menu.query.filter_by(
            menu_date=today,
            meal_type=meal_type,
            is_active=True
        ).first()
        
        if not menu:
            return jsonify({'error': 'Меню на сегодня не найдено'}), 404
        menu_id = menu.id
    else:
        menu = Menu.query.get(menu_id)
        if not menu:
            return jsonify({'error': 'Меню не найдено'}), 404
        meal_type = menu.meal_type
    
    # Check for existing confirmation today
    today = date.today()
    existing = MealRecord.query.filter(
        MealRecord.user_id == user_id,
        MealRecord.meal_type == meal_type,
        db.func.date(MealRecord.received_at) == today,
        MealRecord.is_confirmed == True
    ).first()
    
    if existing:
        return jsonify({'error': 'Вы уже подтвердили получение питания сегодня'}), 409
    
    subscription = Subscription.query.filter_by(
        user_id=user_id,
        is_active=True
    ).first()
    
    has_valid_subscription = subscription and subscription.is_valid() and subscription.meals_remaining > 0
    
    if has_valid_subscription:
        subscription.meals_remaining -= 1
        if subscription.meals_remaining <= 0:
            subscription.is_active = False
    else:
        today = date.today()
        recent_payment = Payment.query.filter(
            Payment.user_id == user_id,
            Payment.payment_type == 'single',
            Payment.status == 'completed',
            db.func.date(Payment.created_at) == today
        ).first()
        
        if not recent_payment:
            return jsonify({'error': 'Нет действующего абонемента или оплаты'}), 403
    
    meal_record = MealRecord(
        user_id=user_id,
        menu_id=menu_id,
        meal_type=meal_type,
        is_confirmed=True,
        received_at=datetime.utcnow()
    )
    
    db.session.add(meal_record)
    db.session.commit()
    
    return jsonify({
        'message': 'Питание успешно подтверждено',
        'meal_record': meal_record.to_dict()
    }), 201


@student_bp.route('/allergies', methods=['GET'])
@student_required
def get_allergies():
    user_id = get_jwt_identity()
    
    allergies = Allergy.query.filter_by(user_id=user_id).all()
    return jsonify({
        'allergies': [a.to_dict() for a in allergies]
    }), 200


@student_bp.route('/allergies', methods=['POST'])
@student_required
def add_allergy():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    allergy_type = data.get('allergy_type')
    if not allergy_type:
        return jsonify({'error': 'allergy_type обязателен'}), 400
    
    existing = Allergy.query.filter_by(
        user_id=user_id,
        allergy_type=allergy_type
    ).first()
    
    if existing:
        return jsonify({'error': 'Эта аллергия уже записана'}), 409
    
    allergy = Allergy(
        user_id=user_id,
        allergy_type=allergy_type,
        notes=data.get('notes', '')
    )
    
    db.session.add(allergy)
    db.session.commit()
    
    return jsonify({
        'message': 'Аллергия успешно добавлена',
        'allergy': allergy.to_dict()
    }), 201


@student_bp.route('/allergies/<int:allergy_id>', methods=['DELETE'])
@student_required
def delete_allergy(allergy_id):
    user_id = get_jwt_identity()
    
    allergy = Allergy.query.filter_by(
        id=allergy_id,
        user_id=user_id
    ).first()
    
    if not allergy:
        return jsonify({'error': 'Аллергия не найдена'}), 404
    
    db.session.delete(allergy)
    db.session.commit()
    
    return jsonify({'message': 'Аллергия удалена'}), 200


@student_bp.route('/reviews', methods=['GET'])
@student_required
def get_reviews():
    user_id = get_jwt_identity()
    
    reviews = Review.query.filter_by(user_id=user_id).all()
    reviews_data = []
    
    for review in reviews:
        review_dict = review.to_dict()
        dish = Dish.query.get(review.dish_id)
        if dish:
            # Include full dish object for template compatibility
            review_dict['dish'] = dish.to_dict()
        reviews_data.append(review_dict)
    
    return jsonify({'reviews': reviews_data}), 200


@student_bp.route('/reviews', methods=['POST'])
@student_required
def add_review():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    dish_id = data.get('dish_id')
    rating = data.get('rating')
    comment = data.get('comment', '').strip()
    
    if not dish_id:
        return jsonify({'error': 'dish_id обязателен'}), 400
    
    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'error': 'Оценка должна быть от 1 до 5'}), 400
    
    if not comment:
        return jsonify({'error': 'Комментарий обязателен'}), 400
    
    dish = Dish.query.get(dish_id)
    if not dish:
        return jsonify({'error': 'Блюдо не найдено'}), 404
    
    # Check for existing review - block duplicates
    existing = Review.query.filter_by(
        user_id=user_id,
        dish_id=dish_id
    ).first()
    
    if existing:
        return jsonify({'error': 'Вы уже оставили отзыв на это блюдо. Вы можете удалить его и оставить новый.'}), 409
    
    review = Review(
        user_id=user_id,
        dish_id=dish_id,
        rating=rating,
        comment=comment
    )
    
    db.session.add(review)
    db.session.commit()
    
    return jsonify({
        'message': 'Отзыв добавлен',
        'review': review.to_dict()
    }), 201


@student_bp.route('/reviews/<int:review_id>', methods=['DELETE'])
@student_required
def delete_review(review_id):
    user_id = get_jwt_identity()
    
    review = Review.query.filter_by(
        id=review_id,
        user_id=user_id
    ).first()
    
    if not review:
        return jsonify({'error': 'Отзыв не найден'}), 404
    
    db.session.delete(review)
    db.session.commit()
    
    return jsonify({'message': 'Отзыв удалён'}), 200


@student_bp.route('/notifications', methods=['GET'])
@student_required
def get_notifications():
    user_id = get_jwt_identity()
    
    unread = Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).order_by(Notification.created_at.desc()).all()
    
    read = Notification.query.filter_by(
        user_id=user_id,
        is_read=True
    ).order_by(Notification.created_at.desc()).limit(20 - len(unread)).all()
    
    notifications = unread + read
    
    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': len(unread)
    }), 200


@student_bp.route('/notifications/<int:notification_id>/read', methods=['PUT', 'POST'])
@student_required
def mark_notification_read(notification_id):
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


@student_bp.route('/notifications/read-all', methods=['PUT', 'POST'])
@student_required
def mark_all_notifications_read():
    user_id = get_jwt_identity()
    
    Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    
    return jsonify({'message': 'Все уведомления отмечены как прочитанные'}), 200


@student_bp.route('/meals/my', methods=['GET'])
@student_required
def get_my_meals():
    """Get current user's meal records"""
    user_id = get_jwt_identity()
    
    meals = MealRecord.query.filter_by(user_id=user_id).order_by(MealRecord.received_at.desc()).limit(30).all()
    
    meals_data = []
    for meal in meals:
        meal_dict = meal.to_dict()
        if meal.menu_id:
            menu = Menu.query.get(meal.menu_id)
            if menu:
                menu_items = MenuItem.query.filter_by(menu_id=menu.id).all()
                if menu_items:
                    dish = Dish.query.get(menu_items[0].dish_id)
                    if dish:
                        meal_dict['dish_name'] = dish.name
        meals_data.append(meal_dict)
    
    return jsonify({'meals': meals_data}), 200
