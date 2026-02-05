from datetime import datetime, date, timedelta
from flask import request, jsonify, make_response
from flask_jwt_extended import get_jwt_identity
from io import BytesIO
from app.api import admin_bp
from app.extensions import db
from app.utils.decorators import admin_required
from app.models import (
    User, Dish, Menu, MenuItem, Payment, Subscription,
    MealRecord, Inventory, Ingredient, PurchaseRequest,
    PurchaseItem, Review, Notification
)


@admin_bp.route('/statistics/payments', methods=['GET'])
@admin_required
def get_payment_statistics():
    days = request.args.get('days', 30, type=int)
    start_date = date.today() - timedelta(days=days)
    
    total_payments = Payment.query.filter(
        Payment.created_at >= start_date
    ).count()
    
    total_revenue = db.session.query(
        db.func.sum(Payment.amount)
    ).filter(
        Payment.created_at >= start_date,
        Payment.status == 'completed'
    ).scalar() or 0
    
    single_revenue = db.session.query(
        db.func.sum(Payment.amount)
    ).filter(
        Payment.created_at >= start_date,
        Payment.payment_type == 'single',
        Payment.status == 'completed'
    ).scalar() or 0
    
    subscription_revenue = db.session.query(
        db.func.sum(Payment.amount)
    ).filter(
        Payment.created_at >= start_date,
        Payment.payment_type == 'subscription',
        Payment.status == 'completed'
    ).scalar() or 0
    
    daily_revenue = []
    for i in range(days):
        day = date.today() - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        
        day_total = db.session.query(
            db.func.sum(Payment.amount)
        ).filter(
            Payment.created_at.between(day_start, day_end),
            Payment.status == 'completed'
        ).scalar() or 0
        
        daily_revenue.append({
            'date': day.isoformat(),
            'revenue': float(day_total)
        })
    
    daily_revenue.reverse()
    
    return jsonify({
        'total_payments': total_payments,
        'total_revenue': float(total_revenue),
        'single_revenue': float(single_revenue),
        'subscription_revenue': float(subscription_revenue),
        'daily_revenue': daily_revenue
    }), 200


@admin_bp.route('/statistics/attendance', methods=['GET'])
@admin_required
def get_attendance_statistics():
    days = request.args.get('days', 30, type=int)
    start_date = date.today() - timedelta(days=days)
    
    total_meals = MealRecord.query.filter(
        MealRecord.received_at >= start_date,
        MealRecord.is_confirmed == True
    ).count()
    
    breakfast_count = MealRecord.query.filter(
        MealRecord.received_at >= start_date,
        MealRecord.is_confirmed == True,
        MealRecord.meal_type == 'breakfast'
    ).count()
    
    lunch_count = MealRecord.query.filter(
        MealRecord.received_at >= start_date,
        MealRecord.is_confirmed == True,
        MealRecord.meal_type == 'lunch'
    ).count()
    
    daily_attendance = []
    for i in range(min(days, 30)):
        day = date.today() - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        
        day_count = MealRecord.query.filter(
            MealRecord.received_at.between(day_start, day_end),
            MealRecord.is_confirmed == True
        ).count()
        
        daily_attendance.append({
            'date': day.isoformat(),
            'count': day_count
        })
    
    daily_attendance.reverse()
    
    return jsonify({
        'total_meals': total_meals,
        'breakfast_count': breakfast_count,
        'lunch_count': lunch_count,
        'daily_attendance': daily_attendance
    }), 200


@admin_bp.route('/statistics/dashboard', methods=['GET'])
@admin_required
def get_dashboard_statistics():
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    
    total_students = User.query.filter_by(role='student').count()
    total_cooks = User.query.filter_by(role='cook').count()
    active_subscriptions = Subscription.query.filter_by(is_active=True).count()
    
    today_meals = MealRecord.query.filter(
        MealRecord.received_at >= today_start
    ).count()
    
    today_revenue = db.session.query(
        db.func.sum(Payment.amount)
    ).filter(
        Payment.created_at >= today_start,
        Payment.status == 'completed'
    ).scalar() or 0
    
    pending_requests = PurchaseRequest.query.filter_by(status='pending').count()
    
    low_stock_count = 0
    inventory_items = Inventory.query.all()
    for item in inventory_items:
        if item.is_low_stock():
            low_stock_count += 1
    
    week_ago = today - timedelta(days=7)
    week_revenue = db.session.query(
        db.func.sum(Payment.amount)
    ).filter(
        Payment.created_at >= week_ago,
        Payment.status == 'completed'
    ).scalar() or 0
    
    week_meals = MealRecord.query.filter(
        MealRecord.received_at >= week_ago
    ).count()
    
    return jsonify({
        'users': {
            'total_students': total_students,
            'total_cooks': total_cooks,
            'active_subscriptions': active_subscriptions
        },
        'today': {
            'meals_served': today_meals,
            'revenue': float(today_revenue)
        },
        'week': {
            'meals_served': week_meals,
            'revenue': float(week_revenue)
        },
        'alerts': {
            'pending_purchase_requests': pending_requests,
            'low_stock_items': low_stock_count
        }
    }), 200


@admin_bp.route('/purchase-requests', methods=['GET'])
@admin_required
def get_all_purchase_requests():
    status = request.args.get('status')
    
    query = PurchaseRequest.query
    
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
        req_dict['total_cost'] = sum(
            item.estimated_cost for item in req.purchase_items
        )
        
        requests_data.append(req_dict)
    
    return jsonify({'purchase_requests': requests_data}), 200


@admin_bp.route('/purchase-requests/<int:request_id>', methods=['PUT'])
@admin_required
def update_purchase_request(request_id):
    admin_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    purchase_request = PurchaseRequest.query.get(request_id)
    if not purchase_request:
        return jsonify({'error': 'Заявка не найдена'}), 404
    
    if purchase_request.status != 'pending':
        return jsonify({'error': 'Можно обновить только ожидающие заявки'}), 400
    
    status = data.get('status')
    if status not in ['approved', 'rejected']:
        return jsonify({'error': 'Статус должен быть approved или rejected'}), 400
    
    purchase_request.status = status
    purchase_request.approved_by = admin_id
    purchase_request.approved_at = datetime.utcnow()
    
    if status == 'approved':
        for item in purchase_request.purchase_items:
            inventory = Inventory.query.filter_by(
                ingredient_id=item.ingredient_id
            ).first()
            
            if inventory:
                inventory.quantity += item.quantity
                inventory.last_updated = datetime.utcnow()
    
    db.session.commit()
    
    notification = Notification(
        user_id=purchase_request.created_by,
        title=f'Заявка {status}',
        message=f'Ваша заявка на закупку была {status}.'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'message': f'Заявка {status}',
        'purchase_request': purchase_request.to_dict()
    }), 200


@admin_bp.route('/reports/meals', methods=['GET'])
@admin_required
def get_meal_report():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    format_type = request.args.get('format', 'json')
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        start_date = date.today() - timedelta(days=30)
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        end_date = date.today()
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    meal_records = MealRecord.query.filter(
        MealRecord.received_at.between(start_datetime, end_datetime),
        MealRecord.is_confirmed == True
    ).all()
    
    total_meals = len(meal_records)
    
    meal_type_counts = {}
    for record in meal_records:
        meal_type_counts[record.meal_type] = meal_type_counts.get(
            record.meal_type, 0
        ) + 1
    
    daily_counts = {}
    for record in meal_records:
        day = record.received_at.date().isoformat()
        daily_counts[day] = daily_counts.get(day, 0) + 1
    
    student_counts = {}
    for record in meal_records:
        student_counts[record.user_id] = student_counts.get(
            record.user_id, 0
        ) + 1
    
    top_students = []
    for user_id, count in sorted(
        student_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]:
        user = User.query.get(user_id)
        if user:
            top_students.append({
                'student_id': user_id,
                'student_name': user.full_name,
                'meals_count': count
            })
    
    report_data = {
        'report_type': 'meal_consumption',
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'summary': {
            'total_meals': total_meals,
            'meal_type_breakdown': meal_type_counts,
            'average_per_day': round(total_meals / max((end_date - start_date).days, 1), 2)
        },
        'daily_breakdown': [
            {'date': d, 'count': c} for d, c in sorted(daily_counts.items())
        ],
        'top_consumers': top_students
    }
    
    if format_type == 'csv':
        output = BytesIO()
        import csv
        writer = csv.writer(output)
        writer.writerow(['Дата', 'Тип', 'Количество'])
        for day, count in sorted(daily_counts.items()):
            writer.writerow([day, 'all', count])
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=meal_report_{start_date}_to_{end_date}.csv'
        return response
    
    return jsonify(report_data), 200


@admin_bp.route('/reports/expenses', methods=['GET'])
@admin_required
def get_expense_report():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    format_type = request.args.get('format', 'json')
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        start_date = date.today() - timedelta(days=30)
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        end_date = date.today()
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    payments = Payment.query.filter(
        Payment.created_at.between(start_datetime, end_datetime),
        Payment.status == 'completed'
    ).all()
    
    total_revenue = sum(p.amount for p in payments)
    
    revenue_by_type = {}
    for payment in payments:
        ptype = payment.payment_type
        revenue_by_type[ptype] = revenue_by_type.get(ptype, 0) + payment.amount
    
    daily_revenue = {}
    for payment in payments:
        day = payment.created_at.date().isoformat()
        daily_revenue[day] = daily_revenue.get(day, 0) + payment.amount
    
    purchase_requests = PurchaseRequest.query.filter(
        PurchaseRequest.approved_at.between(start_datetime, end_datetime),
        PurchaseRequest.status == 'approved'
    ).all()
    
    total_expenses = sum(
        sum(item.estimated_cost for item in pr.purchase_items)
        for pr in purchase_requests
    )
    
    report_data = {
        'report_type': 'financial',
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'revenue': {
            'total': float(total_revenue),
            'by_type': {k: float(v) for k, v in revenue_by_type.items()},
            'daily': [
                {'date': d, 'amount': float(a)}
                for d, a in sorted(daily_revenue.items())
            ]
        },
        'expenses': {
            'total': float(total_expenses),
            'purchase_requests_count': len(purchase_requests)
        },
        'net': float(total_revenue - total_expenses)
    }
    
    if format_type == 'csv':
        output = BytesIO()
        import csv
        writer = csv.writer(output)
        writer.writerow(['Дата', 'Выручка'])
        for day, amount in sorted(daily_revenue.items()):
            writer.writerow([day, amount])
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=expense_report_{start_date}_to_{end_date}.csv'
        return response
    
    return jsonify(report_data), 200


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    role = request.args.get('role')
    search = request.args.get('search', '')
    
    query = User.query
    
    if role:
        query = query.filter_by(role=role)
    
    if search:
        query = query.filter(
            db.or_(
                User.email.ilike(f'%{search}%'),
                User.full_name.ilike(f'%{search}%')
            )
        )
    
    users = query.order_by(User.created_at.desc()).all()
    
    users_data = []
    for user in users:
        user_dict = user.to_dict()
        
        if user.role == 'student':
            subscription = Subscription.query.filter_by(
                user_id=user.id,
                is_active=True
            ).first()
            if subscription:
                user_dict['subscription'] = subscription.to_dict()
        
        users_data.append(user_dict)
    
    return jsonify({'users': users_data}), 200


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    if 'role' in data:
        if data['role'] in ['student', 'cook', 'admin']:
            user.role = data['role']
        else:
            return jsonify({'error': 'Неверная роль'}), 400
    
    if 'full_name' in data:
        user.full_name = data['full_name']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Пользователь обновлен',
        'user': user.to_dict()
    }), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    current_user_id = get_jwt_identity()
    
    if user_id == current_user_id:
        return jsonify({'error': 'Нельзя удалить себя'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'Пользователь удален'}), 200


@admin_bp.route('/menu', methods=['POST'])
@admin_required
def create_menu():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    menu_date_str = data.get('menu_date')
    meal_type = data.get('meal_type', 'lunch')
    dish_ids = data.get('dish_ids', [])
    
    if not menu_date_str:
        return jsonify({'error': 'menu_date обязателен'}), 400
    
    try:
        menu_date = datetime.strptime(menu_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Неверный формат даты. Используйте ГГГГ-ММ-ДД'}), 400
    
    existing = Menu.query.filter_by(
        menu_date=menu_date,
        meal_type=meal_type
    ).first()
    
    if existing:
        MenuItem.query.filter_by(menu_id=existing.id).delete()
        menu = existing
    else:
        menu = Menu(
            menu_date=menu_date,
            meal_type=meal_type,
            is_active=True
        )
        db.session.add(menu)
        db.session.flush()
    
    for dish_id in dish_ids:
        dish = Dish.query.get(dish_id)
        if dish:
            menu_item = MenuItem(menu_id=menu.id, dish_id=dish_id)
            db.session.add(menu_item)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Меню создано',
        'menu': menu.to_dict()
    }), 201


@admin_bp.route('/menu/<int:menu_id>', methods=['DELETE'])
@admin_required
def delete_menu(menu_id):
    menu = Menu.query.get(menu_id)
    if not menu:
        return jsonify({'error': 'Меню не найдено'}), 404
    
    db.session.delete(menu)
    db.session.commit()
    
    return jsonify({'message': 'Меню удалено'}), 200


@admin_bp.route('/dishes', methods=['GET'])
@admin_required
def get_dishes():
    category = request.args.get('category')
    available_only = request.args.get('available_only', 'false').lower() == 'true'
    
    query = Dish.query
    
    if category:
        query = query.filter_by(category=category)
    
    if available_only:
        query = query.filter_by(is_available=True)
    
    dishes = query.order_by(Dish.name).all()
    
    dishes_data = []
    for dish in dishes:
        dish_dict = dish.to_dict()
        
        reviews = Review.query.filter_by(dish_id=dish.id).all()
        if reviews:
            dish_dict['average_rating'] = sum(r.rating for r in reviews) / len(reviews)
            dish_dict['reviews_count'] = len(reviews)
        else:
            dish_dict['average_rating'] = None
            dish_dict['reviews_count'] = 0
        
        dishes_data.append(dish_dict)
    
    return jsonify({'dishes': dishes_data}), 200


@admin_bp.route('/dishes', methods=['POST'])
@admin_required
def create_dish():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    name = data.get('name')
    price = data.get('price')
    category = data.get('category')
    
    if not name or not price or not category:
        return jsonify({'error': 'name, price и category обязательны'}), 400
    
    dish = Dish(
        name=name,
        description=data.get('description', ''),
        price=float(price),
        category=category,
        image_url=data.get('image_url', ''),
        is_available=data.get('is_available', True)
    )
    
    db.session.add(dish)
    db.session.commit()
    
    return jsonify({
        'message': 'Блюдо создано',
        'dish': dish.to_dict()
    }), 201


@admin_bp.route('/dishes/<int:dish_id>', methods=['PUT'])
@admin_required
def update_dish(dish_id):
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    dish = Dish.query.get(dish_id)
    if not dish:
        return jsonify({'error': 'Блюдо не найдено'}), 404
    
    if 'name' in data:
        dish.name = data['name']
    if 'description' in data:
        dish.description = data['description']
    if 'price' in data:
        dish.price = float(data['price'])
    if 'category' in data:
        dish.category = data['category']
    if 'image_url' in data:
        dish.image_url = data['image_url']
    if 'is_available' in data:
        dish.is_available = data['is_available']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Блюдо обновлено',
        'dish': dish.to_dict()
    }), 200


@admin_bp.route('/ingredients', methods=['GET'])
@admin_required
def get_ingredients():
    ingredients = Ingredient.query.order_by(Ingredient.name).all()
    return jsonify({
        'ingredients': [i.to_dict() for i in ingredients]
    }), 200


@admin_bp.route('/ingredients', methods=['POST'])
@admin_required
def create_ingredient():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    name = data.get('name')
    unit = data.get('unit')
    
    if not name or not unit:
        return jsonify({'error': 'name и unit обязательны'}), 400
    
    existing = Ingredient.query.filter_by(name=name).first()
    if existing:
        return jsonify({'error': 'Ингредиент с таким названием уже существует'}), 409
    
    ingredient = Ingredient(
        name=name,
        unit=unit,
        min_stock_level=data.get('min_stock_level', 10.0)
    )
    
    db.session.add(ingredient)
    db.session.flush()
    
    inventory = Inventory(
        ingredient_id=ingredient.id,
        quantity=0
    )
    db.session.add(inventory)
    db.session.commit()
    
    return jsonify({
        'message': 'Ингредиент создан',
        'ingredient': ingredient.to_dict()
    }), 201


@admin_bp.route('/send-notification', methods=['POST'])
@admin_required
def send_notification():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    title = data.get('title')
    message = data.get('message')
    user_ids = data.get('user_ids', [])
    role = data.get('role')
    
    if not title or not message:
        return jsonify({'error': 'title и message обязательны'}), 400
    
    if role:
        users = User.query.filter_by(role=role).all()
        for user in users:
            notification = Notification(
                user_id=user.id,
                title=title,
                message=message
            )
            db.session.add(notification)
    elif user_ids:
        for user_id in user_ids:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message
            )
            db.session.add(notification)
    else:
        return jsonify({'error': 'Укажите role или user_ids'}), 400
    
    db.session.commit()
    
    return jsonify({'message': 'Уведомление отправлено'}), 201
