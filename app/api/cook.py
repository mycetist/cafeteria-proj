from datetime import datetime, date
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.api import cook_bp
from app.extensions import db
from app.utils.decorators import cook_required
from app.models import (
    User, Dish, Menu, MenuItem, Inventory, Ingredient,
    MealRecord, PurchaseRequest, PurchaseItem, Notification, Allergy, Review, DishPurchase
)


@cook_bp.route('/meals/today', methods=['GET'])
@cook_required
def get_today_meals():
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
            'total_served': 0,
            'message': 'На сегодня меню недоступно'
        }), 200
    
    menu_items = MenuItem.query.filter_by(menu_id=menu.id).all()
    dishes = []
    total_served = 0
    
    for item in menu_items:
        dish = Dish.query.get(item.dish_id)
        if dish:
            served_count = MealRecord.query.filter_by(
                menu_id=menu.id,
                is_confirmed=True
            ).count()
            
            dish_data = dish.to_dict()
            dish_data['meals_served'] = served_count
            dishes.append(dish_data)
            total_served += served_count
    
    meal_records = MealRecord.query.filter_by(menu_id=menu.id).all()
    
    # Build meals data with user info
    meals_data = []
    for mr in meal_records:
        meal_dict = mr.to_dict()
        # Add user info
        user = User.query.get(mr.user_id)
        if user:
            meal_dict['user'] = {
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email
            }
        meals_data.append(meal_dict)
    
    return jsonify({
        'menu': menu.to_dict(),
        'dishes': dishes,
        'total_served': total_served,
        'meals': meals_data
    }), 200


@cook_bp.route('/meals/serve', methods=['POST'])
@cook_required
def serve_meal():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    meal_id = data.get('meal_id')
    user_id = data.get('user_id')
    meal_type = data.get('meal_type', 'lunch')
    menu_id = data.get('menu_id')
    
    # If meal_id provided, mark existing record as served
    if meal_id:
        meal_record = MealRecord.query.get(meal_id)
        if not meal_record:
            return jsonify({'error': 'Запись о питании не найдена'}), 404
        
        if meal_record.is_confirmed:
            return jsonify({'error': 'Питание уже выдано'}), 409
        
        meal_record.is_confirmed = True
        meal_record.received_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Питание отмечено как выданное',
            'meal_record': meal_record.to_dict()
        }), 200
    
    # Otherwise, need user_id and either menu_id or meal_type
    if not user_id:
        return jsonify({'error': 'user_id или meal_id обязательны'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    # Find or create menu for today
    today = date.today()
    if not menu_id:
        menu = Menu.query.filter_by(
            menu_date=today,
            meal_type=meal_type,
            is_active=True
        ).first()
        if not menu:
            # Create a basic menu if none exists
            menu = Menu(
                menu_date=today,
                meal_type=meal_type,
                is_active=True
            )
            db.session.add(menu)
            db.session.flush()
        menu_id = menu.id
    else:
        menu = Menu.query.get(menu_id)
        if not menu:
            return jsonify({'error': 'Меню не найдено'}), 404
        meal_type = menu.meal_type
    
    # NOTE: Allow multiple subscription meals per day
    # Removed the check that prevents serving multiple meals to the same user per day
    # Cooks can now serve multiple meals to users who have subscription meals remaining
    
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
        'message': 'Питание успешно выдано',
        'meal_record': meal_record.to_dict()
    }), 201


@cook_bp.route('/meals/search-student', methods=['GET'])
@cook_required
def search_student():
    try:
        query = request.args.get('q', '')

        if not query or len(query) < 2:
            return jsonify({'error': 'Поисковый запрос должен быть не менее 2 символов'}), 400

        # SQLite's LOWER() doesn't handle Cyrillic properly, so we fetch all students
        # and filter in Python for proper case-insensitive Unicode search
        query_lower = query.lower()
        
        all_students = User.query.filter_by(role='student').all()
        
        # Filter students by name or email (case-insensitive, Unicode-aware)
        # Handle potential None values for full_name and email
        students = []
        for s in all_students:
            full_name = (s.full_name or '').lower()
            email = (s.email or '').lower()
            if query_lower in full_name or query_lower in email:
                students.append(s)
            if len(students) >= 10:
                break
        
        results = []
        for student in students:
            student_data = student.to_dict()
            
            # Filter subscriptions in Python (student.subscriptions is a list, not a query)
            active_subscription = None
            for sub in student.subscriptions:
                if sub.is_active:
                    active_subscription = sub
                    break
            
            student_data['has_subscription'] = active_subscription is not None
            if active_subscription:
                student_data['meals_remaining'] = active_subscription.meals_remaining
            
            allergies = Allergy.query.filter_by(user_id=student.id).all()
            student_data['allergies'] = [a.allergy_type for a in allergies]
            
            results.append(student_data)
        
        return jsonify({'students': results}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Ошибка поиска: {str(e)}'}), 500


@cook_bp.route('/inventory', methods=['GET'])
@cook_required
def get_inventory():
    inventory_items = Inventory.query.all()
    
    inventory_data = []
    low_stock_count = 0
    
    for item in inventory_items:
        ingredient = Ingredient.query.get(item.ingredient_id)
        if ingredient:
            item_data = item.to_dict()
            # Include nested ingredient data for template compatibility
            item_data['ingredient'] = {
                'id': ingredient.id,
                'name': ingredient.name,
                'unit': ingredient.unit,
                'min_stock_level': float(ingredient.min_stock_level)
            }
            item_data['is_low_stock'] = item.is_low_stock()
            
            if item.is_low_stock():
                low_stock_count += 1
            
            inventory_data.append(item_data)
    
    return jsonify({
        'inventory': inventory_data,
        'low_stock_count': low_stock_count,
        'total_items': len(inventory_data)
    }), 200


@cook_bp.route('/inventory/<int:inventory_id>', methods=['PUT'])
@cook_required
def update_inventory(inventory_id):
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    inventory = Inventory.query.get(inventory_id)
    if not inventory:
        return jsonify({'error': 'Инвентарь не найден'}), 404
    
    new_quantity = data.get('quantity')
    if new_quantity is None:
        return jsonify({'error': 'quantity обязателен'}), 400
    
    try:
        new_quantity = float(new_quantity)
        if new_quantity < 0:
            return jsonify({'error': 'Количество не может быть отрицательным'}), 400
    except ValueError:
        return jsonify({'error': 'Неверное значение количества'}), 400
    
    old_quantity = inventory.quantity
    inventory.quantity = new_quantity
    inventory.last_updated = datetime.utcnow()
    
    db.session.commit()
    
    ingredient = Ingredient.query.get(inventory.ingredient_id)
    if ingredient and inventory.is_low_stock():
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            notification = Notification(
                user_id=admin.id,
                title='Низкий запас',
                message=f'{ingredient.name} заканчивается. Текущий запас: {new_quantity} {ingredient.unit}'
            )
            db.session.add(notification)
        db.session.commit()
    
    return jsonify({
        'message': 'Инвентарь обновлен',
        'inventory': inventory.to_dict(),
        'old_quantity': float(old_quantity),
        'new_quantity': new_quantity
    }), 200


@cook_bp.route('/inventory/<int:inventory_id>/adjust', methods=['POST'])
@cook_required
def adjust_inventory(inventory_id):
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    inventory = Inventory.query.get(inventory_id)
    if not inventory:
        return jsonify({'error': 'Инвентарь не найден'}), 404
    
    adjustment = data.get('adjustment')
    if adjustment is None:
        return jsonify({'error': 'adjustment обязателен'}), 400
    
    try:
        adjustment = float(adjustment)
    except ValueError:
        return jsonify({'error': 'Неверное значение'}), 400
    
    new_quantity = inventory.quantity + adjustment
    if new_quantity < 0:
        return jsonify({'error': 'Результат будет отрицательным'}), 400
    
    inventory.quantity = new_quantity
    inventory.last_updated = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Инвентарь скорректирован',
        'inventory': inventory.to_dict(),
        'adjustment': adjustment
    }), 200


@cook_bp.route('/purchase-requests', methods=['GET'])
@cook_required
def get_purchase_requests():
    user_id = get_jwt_identity()
    status = request.args.get('status')
    
    query = PurchaseRequest.query.filter_by(created_by=user_id)
    
    if status:
        query = query.filter_by(status=status)
    
    requests = query.order_by(PurchaseRequest.created_at.desc()).all()
    
    requests_data = []
    for req in requests:
        req_dict = req.to_dict()
        
        creator = User.query.get(req.created_by)
        if creator:
            req_dict['creator_name'] = creator.full_name
        
        if req.approved_by:
            approver = User.query.get(req.approved_by)
            if approver:
                req_dict['approver_name'] = approver.full_name
        
        items = []
        for item in req.purchase_items:
            item_dict = item.to_dict()
            ingredient = Ingredient.query.get(item.ingredient_id)
            if ingredient:
                item_dict['ingredient_name'] = ingredient.name
                item_dict['unit'] = ingredient.unit
            items.append(item_dict)
        
        req_dict['items'] = items
        req_dict['total_cost'] = sum(item.estimated_cost for item in req.purchase_items)
        
        requests_data.append(req_dict)
    
    return jsonify({'purchase_requests': requests_data}), 200


@cook_bp.route('/purchase-requests', methods=['POST'])
@cook_required
def create_purchase_request():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    items = data.get('items', [])
    if not items or not isinstance(items, list):
        return jsonify({'error': 'items массив обязателен'}), 400
    
    notes = data.get('notes', '')
    
    for item in items:
        if 'ingredient_id' not in item or 'quantity' not in item:
            return jsonify({'error': 'Каждый элемент должен иметь ingredient_id и quantity'}), 400
        
        ingredient = Ingredient.query.get(item['ingredient_id'])
        if not ingredient:
            return jsonify({'error': f"Ингредиент {item['ingredient_id']} не найден"}), 404
        
        try:
            quantity = float(item['quantity'])
            if quantity <= 0:
                return jsonify({'error': 'Количество должно быть положительным'}), 400
        except ValueError:
            return jsonify({'error': 'Неверное значение количества'}), 400
    
    purchase_request = PurchaseRequest(
        created_by=user_id,
        status='pending',
        notes=notes
    )
    
    db.session.add(purchase_request)
    db.session.flush()
    
    total_cost = 0
    for item_data in items:
        estimated_cost = float(item_data.get('estimated_cost', 10.0))
        
        purchase_item = PurchaseItem(
            request_id=purchase_request.id,
            ingredient_id=item_data['ingredient_id'],
            quantity=float(item_data['quantity']),
            estimated_cost=estimated_cost
        )
        
        db.session.add(purchase_item)
        total_cost += estimated_cost
    
    db.session.commit()
    
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        notification = Notification(
            user_id=admin.id,
            title='Новая заявка на закупку',
            message=f'Создана новая заявка на закупку. Предполагаемая стоимость: {total_cost:.2f} ₽'
        )
        db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Заявка на закупку создана',
        'purchase_request': purchase_request.to_dict(),
        'total_cost': total_cost
    }), 201


@cook_bp.route('/purchase-requests/<int:request_id>', methods=['DELETE'])
@cook_required
def delete_purchase_request(request_id):
    user_id = get_jwt_identity()
    
    purchase_request = PurchaseRequest.query.filter_by(
        id=request_id,
        created_by=user_id
    ).first()
    
    if not purchase_request:
        return jsonify({'error': 'Заявка не найдена'}), 404
    
    if purchase_request.status != 'pending':
        return jsonify({'error': 'Можно удалить только ожидающие заявки'}), 403
    
    db.session.delete(purchase_request)
    db.session.commit()
    
    return jsonify({'message': 'Заявка удалена'}), 200


@cook_bp.route('/dashboard-stats', methods=['GET'])
@cook_required
def get_dashboard_stats():
    today = date.today()
    
    menu = Menu.query.filter_by(
        menu_date=today,
        meal_type='lunch',
        is_active=True
    ).first()
    
    stats = {
        'today': today.isoformat(),
        'meals_served_today': 0,
        'active_menu': None,
        'low_stock_items': 0
    }
    
    if menu:
        stats['active_menu'] = menu.to_dict()
        stats['meals_served_today'] = MealRecord.query.filter_by(
            menu_id=menu.id,
            is_confirmed=True
        ).count()
    
    inventory_items = Inventory.query.all()
    for item in inventory_items:
        if item.is_low_stock():
            stats['low_stock_items'] += 1
    
    user_id = get_jwt_identity()
    stats['pending_purchase_requests'] = PurchaseRequest.query.filter_by(
        created_by=user_id,
        status='pending'
    ).count()
    
    return jsonify(stats), 200


@cook_bp.route('/reviews', methods=['GET'])
@cook_required
def get_all_reviews():
    """Get all reviews for all dishes - for cook to view feedback"""
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    reviews_data = []
    
    for review in reviews:
        review_dict = review.to_dict()
        dish = Dish.query.get(review.dish_id)
        if dish:
            review_dict['dish'] = dish.to_dict()
        user = User.query.get(review.user_id)
        if user:
            review_dict['user'] = {
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email
            }
        reviews_data.append(review_dict)
    
    return jsonify({'reviews': reviews_data}), 200


@cook_bp.route('/meals/purchases', methods=['GET'])
@cook_required
def get_today_purchases():
    """Get all dish purchases for today with user details - for cook to see what was purchased"""
    from datetime import date
    
    today = date.today()
    meal_type = request.args.get('meal_type', None)  # Optional filter by breakfast/lunch
    
    # Get purchases from today
    query = DishPurchase.query.filter(
        db.func.date(DishPurchase.purchase_date) == today
    )
    
    if meal_type:
        query = query.filter_by(meal_type=meal_type)
    
    purchases = query.order_by(DishPurchase.purchase_date.desc()).all()
    
    purchases_data = []
    for purchase in purchases:
        purchase_dict = purchase.to_dict()
        
        # Add user info
        user = User.query.get(purchase.user_id)
        if user:
            purchase_dict['user'] = {
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email
            }
            # Add allergies
            allergies = Allergy.query.filter_by(user_id=user.id).all()
            purchase_dict['user']['allergies'] = [a.allergy_type for a in allergies]
        
        # Add dish info
        dish = Dish.query.get(purchase.dish_id)
        if dish:
            purchase_dict['dish'] = dish.to_dict()
        
        # Add menu info
        if purchase.menu_id:
            menu = Menu.query.get(purchase.menu_id)
            if menu:
                purchase_dict['menu'] = menu.to_dict()
        
        purchases_data.append(purchase_dict)
    
    # Group by meal_type
    breakfast_purchases = [p for p in purchases_data if p.get('meal_type') == 'breakfast']
    lunch_purchases = [p for p in purchases_data if p.get('meal_type') == 'lunch' or not p.get('meal_type')]
    
    return jsonify({
        'purchases': purchases_data,
        'breakfast': breakfast_purchases,
        'lunch': lunch_purchases,
        'total_count': len(purchases_data),
        'used_count': len([p for p in purchases_data if p.get('is_used')]),
        'pending_count': len([p for p in purchases_data if not p.get('is_used')])
    }), 200


@cook_bp.route('/meals/student-purchases/<int:user_id>', methods=['GET'])
@cook_required
def get_student_purchases(user_id):
    """Get all dish purchases for a specific student"""
    from datetime import date
    
    today = date.today()
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    # Get today's purchases for this user
    purchases = DishPurchase.query.filter(
        DishPurchase.user_id == user_id,
        db.func.date(DishPurchase.purchase_date) == today
    ).order_by(DishPurchase.purchase_date.desc()).all()
    
    purchases_data = []
    for purchase in purchases:
        purchase_dict = purchase.to_dict()
        dish = Dish.query.get(purchase.dish_id)
        if dish:
            purchase_dict['dish'] = dish.to_dict()
        purchases_data.append(purchase_dict)
    
    # Also get subscription info
    subscription = user.subscriptions.filter_by(is_active=True).first()
    
    return jsonify({
        'user': {
            'id': user.id,
            'full_name': user.full_name,
            'email': user.email
        },
        'purchases': purchases_data,
        'subscription': subscription.to_dict() if subscription else None,
        'balance': float(user.balance) if user.balance else 0.00
    }), 200


@cook_bp.route('/meals/serve-purchase', methods=['POST'])
@cook_required
def serve_purchase():
    """Serve a dish purchase - mark as used and create meal record"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    purchase_id = data.get('purchase_id')
    user_id = data.get('user_id')
    
    if purchase_id:
        purchase = DishPurchase.query.get(purchase_id)
        if not purchase:
            return jsonify({'error': 'Покупка не найдена'}), 404
        
        if purchase.is_used:
            return jsonify({'error': 'Это блюдо уже было выдано'}), 409
        
        purchase.mark_as_used()
        user_id = purchase.user_id
        
    elif user_id:
        # Find unused purchase for this user today
        today = date.today()
        purchase = DishPurchase.query.filter(
            DishPurchase.user_id == user_id,
            DishPurchase.is_used == False,
            db.func.date(DishPurchase.purchase_date) == today
        ).first()
        
        if not purchase:
            return jsonify({'error': 'Нет неиспользованных покупок для этого пользователя'}), 404
        
        purchase.mark_as_used()
    else:
        return jsonify({'error': 'Необходим purchase_id или user_id'}), 400
    
    # Create meal record
    meal_record = MealRecord(
        user_id=user_id,
        menu_id=purchase.menu_id,
        meal_type=purchase.meal_type or 'lunch',
        is_confirmed=True,
        received_at=datetime.utcnow()
    )
    
    db.session.add(meal_record)
    db.session.commit()
    
    # Notify user
    dish = Dish.query.get(purchase.dish_id)
    notification = Notification(
        user_id=user_id,
        title='Питание выдано',
        message=f'Повар выдал вам "{dish.name if dish else "блюдо"}"'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'message': 'Блюдо успешно выдано',
        'purchase': purchase.to_dict(),
        'meal_record': meal_record.to_dict()
    }), 200
