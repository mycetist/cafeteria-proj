from datetime import datetime, date, timedelta
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.api import student_bp
from app.extensions import db
from app.utils.decorators import student_required
from app.models import (
    User, Dish, Menu, MenuItem, Payment, Subscription,
    MealRecord, Allergy, Review, Notification, DishPurchase
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
        transaction_id=f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}{user_id}"
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
    
    # Get user to check balance
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    today = date.today()
    if subscription_type == 'weekly':
        days_to_add = 7
        amount = 700.00
        meals_to_add = 5
    else:
        days_to_add = 30
        amount = 2500.00
        meals_to_add = 20
    
    # Check if user has sufficient balance
    current_balance = float(user.balance) if user.balance else 0.00
    if current_balance < amount:
        return jsonify({
            'error': 'Недостаточно средств на балансе',
            'required': amount,
            'current_balance': current_balance,
            'shortage': amount - current_balance
        }), 402  # Payment Required
    
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
    
    # Deduct balance from user wallet
    if not user.deduct_balance(amount):
        return jsonify({'error': 'Ошибка при списании средств'}), 500
    
    payment = Payment(
        user_id=user_id,
        amount=amount,
        payment_type='subscription',
        status='completed',
        transaction_id=f"SUB{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}{user_id}"
    )
    db.session.add(payment)
    db.session.commit()
    
    notification = Notification(
        user_id=user_id,
        title='Абонемент активирован',
        message=f'{message} Списано с кошелька: {amount:.2f} ₽. Текущий баланс: {float(user.balance):.2f} ₽'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'message': 'Абонемент успешно создан',
        'subscription': subscription.to_dict(),
        'payment': payment.to_dict(),
        'remaining_balance': float(user.balance)
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
    
    # Validate meal_type
    if meal_type not in ['breakfast', 'lunch']:
        return jsonify({'error': 'Тип питания должен быть breakfast или lunch'}), 400
    
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
    
    # Check if user already claimed this meal type today (1 breakfast and 1 lunch per day limit)
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    existing_meal = MealRecord.query.filter(
        MealRecord.user_id == user_id,
        MealRecord.meal_type == meal_type,
        MealRecord.is_confirmed == True,
        MealRecord.received_at >= today_start,
        MealRecord.received_at <= today_end
    ).first()
    
    if existing_meal:
        meal_type_ru = 'завтрак' if meal_type == 'breakfast' else 'обед'
        return jsonify({
            'error': f'Вы уже получили {meal_type_ru} сегодня. Разрешается только 1 {meal_type_ru} в день.'
        }), 409
    
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


# NOTE: Notification endpoints removed - use common endpoints in app/api/common.py
# These are available to all authenticated users via /api/notifications


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


# ============ WALLET ENDPOINTS ============

@student_bp.route('/wallet', methods=['GET'])
@student_required
def get_wallet():
    """Get user's wallet balance and recent transactions"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    # Get recent transactions (payments and purchases)
    payments = Payment.query.filter_by(user_id=user_id).order_by(Payment.created_at.desc()).limit(10).all()
    purchases = DishPurchase.query.filter_by(user_id=user_id).order_by(DishPurchase.purchase_date.desc()).limit(10).all()
    
    transactions = []
    
    for payment in payments:
        transactions.append({
            'id': f'pay_{payment.id}',
            'type': 'topup' if payment.payment_type == 'topup' else payment.payment_type,
            'amount': float(payment.amount),
            'status': payment.status,
            'date': payment.created_at.isoformat() if payment.created_at else None,
            'description': 'Пополнение кошелька' if payment.payment_type == 'topup' else 
                          'Покупка абонемента' if payment.payment_type == 'subscription' else 'Оплата'
        })
    
    for purchase in purchases:
        dish = Dish.query.get(purchase.dish_id)
        transactions.append({
            'id': f'purchase_{purchase.id}',
            'type': 'dish_purchase',
            'amount': -float(purchase.price_paid),
            'status': 'completed',
            'date': purchase.purchase_date.isoformat() if purchase.purchase_date else None,
            'description': f'Покупка: {dish.name if dish else "Блюдо"}'
        })
    
    # Sort by date descending
    transactions.sort(key=lambda x: x['date'] if x['date'] else '', reverse=True)
    
    return jsonify({
        'wallet': {
            'balance': float(user.balance) if user.balance else 0.00,
            'user_id': user.id
        },
        'transactions': transactions[:20]  # Last 20 transactions
    }), 200


@student_bp.route('/wallet/topup', methods=['POST'])
@student_required
def topup_wallet():
    """Top up user's wallet balance"""
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
        if amount < 100:
            return jsonify({'error': 'Минимальная сумма пополнения 100 ₽'}), 400
        if amount > 50000:
            return jsonify({'error': 'Максимальная сумма пополнения 50000 ₽'}), 400
    except ValueError:
        return jsonify({'error': 'Неверная сумма'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    # Add balance to user
    user.add_balance(amount)
    
    # Create payment record for topup
    payment = Payment(
        user_id=user_id,
        amount=amount,
        payment_type='topup',
        status='completed',
        transaction_id=f"TOPUP{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}{user_id}"
    )
    
    db.session.add(payment)
    db.session.commit()
    
    # Create notification
    notification = Notification(
        user_id=user_id,
        title='Кошелек пополнен',
        message=f'Ваш кошелек успешно пополнен на {amount:.2f} ₽. Текущий баланс: {float(user.balance):.2f} ₽'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'message': 'Кошелек успешно пополнен',
        'payment': payment.to_dict(),
        'new_balance': float(user.balance)
    }), 201


# ============ DISH PURCHASE ENDPOINTS ============

@student_bp.route('/dishes/<int:dish_id>/reviews', methods=['GET'])
@student_required
def get_dish_reviews(dish_id):
    """Get all reviews for a specific dish"""
    dish = Dish.query.get(dish_id)
    if not dish:
        return jsonify({'error': 'Блюдо не найдено'}), 404
    
    reviews = Review.query.filter_by(dish_id=dish_id).order_by(Review.created_at.desc()).all()
    
    reviews_data = []
    for review in reviews:
        review_dict = review.to_dict()
        user = User.query.get(review.user_id)
        if user:
            review_dict['user_name'] = user.full_name
        reviews_data.append(review_dict)
    
    # Calculate average rating
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else None
    
    return jsonify({
        'dish': dish.to_dict(),
        'reviews': reviews_data,
        'average_rating': avg_rating,
        'reviews_count': len(reviews_data)
    }), 200


@student_bp.route('/dishes/<int:dish_id>/purchase', methods=['POST'])
@student_required
def purchase_dish(dish_id):
    """Purchase a specific dish using wallet balance"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    dish = Dish.query.get(dish_id)
    if not dish:
        return jsonify({'error': 'Блюдо не найдено'}), 404
    
    if not dish.is_available:
        return jsonify({'error': 'Блюдо временно недоступно'}), 400
    
    price = float(dish.price) if dish.price else 0
    if price <= 0:
        return jsonify({'error': 'Блюдо не продается'}), 400
    
    # Check if user has sufficient balance
    current_balance = float(user.balance) if user.balance else 0.00
    if current_balance < price:
        return jsonify({
            'error': 'Недостаточно средств на балансе',
            'required': price,
            'current_balance': current_balance,
            'shortage': price - current_balance
        }), 402  # Payment Required
    
    # Get optional menu association
    menu_id = data.get('menu_id')
    meal_type = data.get('meal_type', 'lunch')
    
    if menu_id:
        menu = Menu.query.get(menu_id)
        if not menu:
            return jsonify({'error': 'Меню не найдено'}), 404
        meal_type = menu.meal_type
    
    # NOTE: Allow multiple purchases of the same dish - no restriction!
    # Users can buy as many dishes as they want per day
    
    # Deduct balance
    if not user.deduct_balance(price):
        return jsonify({'error': 'Ошибка при списании средств'}), 500
    
    # Create dish purchase record
    purchase = DishPurchase(
        user_id=user_id,
        dish_id=dish_id,
        menu_id=menu_id,
        price_paid=price,
        meal_type=meal_type,
        is_used=False
    )
    
    db.session.add(purchase)
    db.session.commit()
    
    # Create notification
    notification = Notification(
        user_id=user_id,
        title='Блюдо приобретено',
        message=f'Вы приобрели "{dish.name}" за {price:.2f} ₽. Текущий баланс: {float(user.balance):.2f} ₽'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'message': 'Блюдо успешно приобретено',
        'purchase': purchase.to_dict(),
        'dish': dish.to_dict(),
        'remaining_balance': float(user.balance)
    }), 201


@student_bp.route('/purchases', methods=['GET'])
@student_required
def get_my_purchases():
    """Get current user's dish purchases"""
    user_id = get_jwt_identity()
    
    purchases = DishPurchase.query.filter_by(user_id=user_id).order_by(DishPurchase.purchase_date.desc()).all()
    
    purchases_data = []
    for purchase in purchases:
        purchase_dict = purchase.to_dict()
        dish = Dish.query.get(purchase.dish_id)
        if dish:
            purchase_dict['dish'] = dish.to_dict()
        purchases_data.append(purchase_dict)
    
    return jsonify({'purchases': purchases_data}), 200


@student_bp.route('/purchases/<int:purchase_id>/use', methods=['POST'])
@student_required
def use_purchase(purchase_id):
    """Mark a dish purchase as used (when receiving the meal)"""
    user_id = get_jwt_identity()
    
    purchase = DishPurchase.query.filter_by(id=purchase_id, user_id=user_id).first()
    if not purchase:
        return jsonify({'error': 'Покупка не найдена'}), 404
    
    if purchase.is_used:
        return jsonify({'error': 'Это блюдо уже было получено'}), 409
    
    meal_type = purchase.meal_type or 'lunch'
    
    # Check if user already claimed this meal type today (1 breakfast and 1 lunch per day limit)
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    existing_meal = MealRecord.query.filter(
        MealRecord.user_id == user_id,
        MealRecord.meal_type == meal_type,
        MealRecord.is_confirmed == True,
        MealRecord.received_at >= today_start,
        MealRecord.received_at <= today_end
    ).first()
    
    if existing_meal:
        meal_type_ru = 'завтрак' if meal_type == 'breakfast' else 'обед'
        return jsonify({
            'error': f'Вы уже получили {meal_type_ru} сегодня. Разрешается только 1 {meal_type_ru} в день.'
        }), 409
    
    purchase.mark_as_used()
    
    # Create meal record
    meal_record = MealRecord(
        user_id=user_id,
        menu_id=purchase.menu_id,
        meal_type=meal_type,
        is_confirmed=True,
        received_at=datetime.utcnow()
    )
    
    db.session.add(meal_record)
    db.session.commit()
    
    # Create notification
    dish = Dish.query.get(purchase.dish_id)
    notification = Notification(
        user_id=user_id,
        title='Питание получено',
        message=f'Вы получили "{dish.name if dish else "блюдо"}"'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'message': 'Блюдо отмечено как полученное',
        'purchase': purchase.to_dict(),
        'meal_record': meal_record.to_dict()
    }), 200


@student_bp.route('/meals/today-status', methods=['GET'])
@student_required
def get_today_meal_status():
    """Get today's meal claim status for breakfast and lunch"""
    user_id = get_jwt_identity()
    
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # Get today's confirmed meals
    today_meals = MealRecord.query.filter(
        MealRecord.user_id == user_id,
        MealRecord.is_confirmed == True,
        MealRecord.received_at >= today_start,
        MealRecord.received_at <= today_end
    ).all()
    
    breakfast_claimed = any(m.meal_type == 'breakfast' for m in today_meals)
    lunch_claimed = any(m.meal_type == 'lunch' for m in today_meals)
    
    # Get subscription status
    subscription = Subscription.query.filter_by(
        user_id=user_id,
        is_active=True
    ).first()
    
    has_subscription = subscription and subscription.is_valid() and subscription.meals_remaining > 0
    meals_remaining = subscription.meals_remaining if has_subscription else 0
    
    # Get unused purchases for today
    unused_purchases = DishPurchase.query.filter(
        DishPurchase.user_id == user_id,
        DishPurchase.is_used == False
    ).all()
    
    unused_breakfast_purchases = [p for p in unused_purchases if p.meal_type == 'breakfast']
    unused_lunch_purchases = [p for p in unused_purchases if p.meal_type == 'lunch' or p.meal_type is None]
    
    return jsonify({
        'today': today.isoformat(),
        'breakfast': {
            'claimed': breakfast_claimed,
            'can_claim': not breakfast_claimed and (has_subscription or len(unused_breakfast_purchases) > 0),
            'has_subscription': has_subscription,
            'has_purchase': len(unused_breakfast_purchases) > 0
        },
        'lunch': {
            'claimed': lunch_claimed,
            'can_claim': not lunch_claimed and (has_subscription or len(unused_lunch_purchases) > 0),
            'has_subscription': has_subscription,
            'has_purchase': len(unused_lunch_purchases) > 0
        },
        'meals_remaining': meals_remaining,
        'subscription_active': has_subscription
    }), 200
