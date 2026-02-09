#!/usr/bin/env python3
from app import create_app, db
from app.models import (
    User, Dish, Ingredient, Inventory, DishIngredient,
    Menu, MenuItem
)
from datetime import date, datetime, timedelta
import bcrypt


def create_admin_user():
    admin = User.query.filter_by(email='admin@cafeteria.com').first()
    if not admin:
        admin = User(
            email='admin@cafeteria.com',
            full_name='Администратор',
            role='admin',
            is_active=True
        )
        salt = bcrypt.gensalt()
        admin.password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), salt).decode('utf-8')
        db.session.add(admin)
    return admin


def create_cook_user():
    cook = User.query.filter_by(email='cook@cafeteria.com').first()
    if not cook:
        cook = User(
            email='cook@cafeteria.com',
            full_name='Шеф-повар',
            role='cook',
            is_active=True
        )
        salt = bcrypt.gensalt()
        cook.password_hash = bcrypt.hashpw('cook123'.encode('utf-8'), salt).decode('utf-8')
        db.session.add(cook)
    return cook


def create_sample_student():
    student = User.query.filter_by(email='student@school.com').first()
    if not student:
        student = User(
            email='student@school.com',
            full_name='Иван Иванов',
            role='student',
            is_active=True,
            balance=1000.00  # Give initial balance for testing
        )
        salt = bcrypt.gensalt()
        student.password_hash = bcrypt.hashpw('student123'.encode('utf-8'), salt).decode('utf-8')
        db.session.add(student)
    else:
        # Update balance if user exists
        student.balance = 1000.00
    return student


def create_additional_students():
    """Create additional test students with initial balances"""
    students_data = [
        ('maria@school.com', 'Мария Петрова', 500.00),
        ('alex@school.com', 'Алексей Сидоров', 750.00),
        ('anna@school.com', 'Анна Кузнецова', 2000.00),
    ]
    
    for email, name, balance in students_data:
        student = User.query.filter_by(email=email).first()
        if not student:
            student = User(
                email=email,
                full_name=name,
                role='student',
                is_active=True,
                balance=balance
            )
            salt = bcrypt.gensalt()
            student.password_hash = bcrypt.hashpw('student123'.encode('utf-8'), salt).decode('utf-8')
            db.session.add(student)


def create_ingredients():
    ingredients_data = [
        ('Куриная грудка', 'кг', 10, 50),
        ('Рис', 'кг', 20, 100),
        ('Картофель', 'кг', 15, 80),
        ('Морковь', 'кг', 5, 30),
        ('Лук', 'кг', 5, 25),
        ('Мука', 'кг', 10, 50),
        ('Молоко', 'л', 10, 40),
        ('Яйца', 'шт', 50, 200),
        ('Сливочное масло', 'кг', 5, 20),
        ('Помидоры', 'кг', 5, 25),
        ('Огурцы', 'кг', 5, 20),
        ('Капуста', 'кг', 5, 30),
        ('Говядина', 'кг', 5, 25),
        ('Филе рыбы', 'кг', 3, 15),
        ('Макароны', 'кг', 5, 30),
        ('Сыр', 'кг', 3, 15),
        ('Яблоки', 'кг', 5, 25),
        ('Бананы', 'кг', 5, 20),
        ('Хлеб', 'шт', 10, 40),
        ('Сахар', 'кг', 5, 25),
    ]
    
    for name, unit, min_stock, quantity in ingredients_data:
        ingredient = Ingredient.query.filter_by(name=name).first()
        if not ingredient:
            ingredient = Ingredient(
                name=name,
                unit=unit,
                min_stock_level=min_stock
            )
            db.session.add(ingredient)
            db.session.flush()
            
            inventory = Inventory(
                ingredient_id=ingredient.id,
                quantity=quantity,
                last_updated=datetime.utcnow()
            )
            db.session.add(inventory)


def create_dishes():
    dishes_data = [
        # Завтраки
        {
            'name': 'Овсяная каша',
            'description': 'Полезная овсяная каша на молоке с медом',
            'price': 60.00,
            'category': 'Завтраки',
            'image_url': '/static/images/oatmeal.jpg'
        },
        {
            'name': 'Омлет с сыром',
            'description': 'Воздушный омлет с сыром и зеленью',
            'price': 75.00,
            'category': 'Завтраки',
            'image_url': '/static/images/omelette.jpg'
        },
        {
            'name': 'Сырники',
            'description': 'Творожные сырники со сметаной и вареньем',
            'price': 80.00,
            'category': 'Завтраки',
            'image_url': '/static/images/syrniki.jpg'
        },
        {
            'name': 'Блины с маслом',
            'description': 'Горячие блины с сливочным маслом',
            'price': 70.00,
            'category': 'Завтраки',
            'image_url': '/static/images/pancakes.jpg'
        },
        {
            'name': 'Бутерброд с сыром',
            'description': 'Свежий бутерброд с сыром и маслом',
            'price': 50.00,
            'category': 'Завтраки',
            'image_url': '/static/images/sandwich.jpg'
        },
        {
            'name': 'Йогурт с мюсли',
            'description': 'Натуральный йогурт с мюсли и фруктами',
            'price': 65.00,
            'category': 'Завтраки',
            'image_url': '/static/images/yogurt.jpg'
        },
        # Горячее
        {
            'name': 'Курица с рисом',
            'description': 'Куриная грудка на гриле с отварным рисом и овощами',
            'price': 150.00,
            'category': 'Горячее',
            'image_url': '/static/images/chicken_rice.jpg'
        },
        {
            'name': 'Говяжье рагу',
            'description': 'Сытное говяжье рагу с картофелем и морковью',
            'price': 180.00,
            'category': 'Горячее',
            'image_url': '/static/images/beef_stew.jpg'
        },
        {
            'name': 'Рыба с картофелем фри',
            'description': 'Хрустящее филе рыбы с картофелем фри',
            'price': 160.00,
            'category': 'Горячее',
            'image_url': '/static/images/fish_chips.jpg'
        },
        {
            'name': 'Паста Карбонара',
            'description': 'Сливочная паста с сыром и яйцом',
            'price': 140.00,
            'category': 'Горячее',
            'image_url': '/static/images/carbonara.jpg'
        },
        # Супы
        {
            'name': 'Овощной суп',
            'description': 'Свежий овощной суп с хлебом',
            'price': 80.00,
            'category': 'Супы',
            'image_url': '/static/images/veg_soup.jpg'
        },
        {
            'name': 'Куриный суп',
            'description': 'Горячий куриный суп с лапшой',
            'price': 90.00,
            'category': 'Супы',
            'image_url': '/static/images/chicken_soup.jpg'
        },
        # Салаты
        {
            'name': 'Свежий салат',
            'description': 'Овощной салат с помидорами и огурцами',
            'price': 60.00,
            'category': 'Салаты',
            'image_url': '/static/images/salad.jpg'
        },
        {
            'name': 'Салат из капусты',
            'description': 'Хрустящий салат из капусты с морковью',
            'price': 50.00,
            'category': 'Салаты',
            'image_url': '/static/images/cabbage_salad.jpg'
        },
        # Десерты
        {
            'name': 'Яблочный пирог',
            'description': 'Сладкий яблочный пирог с корицей',
            'price': 70.00,
            'category': 'Десерты',
            'image_url': '/static/images/apple_pie.jpg'
        },
        {
            'name': 'Фруктовый салат',
            'description': 'Свежие сезонные фрукты',
            'price': 65.00,
            'category': 'Десерты',
            'image_url': '/static/images/fruit_cup.jpg'
        },
        # Напитки
        {
            'name': 'Молоко',
            'description': 'Свежее молоко 250мл',
            'price': 40.00,
            'category': 'Напитки',
            'image_url': '/static/images/milk.jpg'
        },
        {
            'name': 'Фруктовый сок',
            'description': 'Свежевыжатый апельсиновый сок 250мл',
            'price': 55.00,
            'category': 'Напитки',
            'image_url': '/static/images/juice.jpg'
        },
    ]
    
    for dish_data in dishes_data:
        dish = Dish.query.filter_by(name=dish_data['name']).first()
        if not dish:
            dish = Dish(**dish_data, is_available=True)
            db.session.add(dish)


def create_weekly_menu():
    today = date.today()
    
    soups = Dish.query.filter_by(category='Супы').all()
    mains = Dish.query.filter_by(category='Горячее').all()
    salads = Dish.query.filter_by(category='Салаты').all()
    desserts = Dish.query.filter_by(category='Десерты').all()
    drinks = Dish.query.filter_by(category='Напитки').all()
    
    if not all([soups, mains, salads, desserts]):
        return
    
    for i in range(5):
        menu_date = today + timedelta(days=i)
        
        existing = Menu.query.filter_by(menu_date=menu_date, meal_type='lunch').first()
        if existing:
            continue
        
        menu = Menu(
            menu_date=menu_date,
            meal_type='lunch',
            is_active=True
        )
        db.session.add(menu)
        db.session.flush()
        
        menu_items = [
            MenuItem(menu_id=menu.id, dish_id=soups[i % len(soups)].id),
            MenuItem(menu_id=menu.id, dish_id=mains[i % len(mains)].id),
            MenuItem(menu_id=menu.id, dish_id=salads[i % len(salads)].id),
            MenuItem(menu_id=menu.id, dish_id=desserts[i % len(desserts)].id),
        ]
        if drinks:
            menu_items.append(MenuItem(menu_id=menu.id, dish_id=drinks[i % len(drinks)].id))
        
        for item in menu_items:
            db.session.add(item)


def create_breakfast_menu():
    """Create breakfast menus for the week"""
    today = date.today()
    
    breakfasts = Dish.query.filter_by(category='Завтраки').all()
    drinks = Dish.query.filter_by(category='Напитки').all()
    
    if not breakfasts:
        return
    
    for i in range(5):
        menu_date = today + timedelta(days=i)
        
        existing = Menu.query.filter_by(menu_date=menu_date, meal_type='breakfast').first()
        if existing:
            continue
        
        menu = Menu(
            menu_date=menu_date,
            meal_type='breakfast',
            is_active=True
        )
        db.session.add(menu)
        db.session.flush()
        
        # Add 2-3 breakfast items per day
        menu_items = [
            MenuItem(menu_id=menu.id, dish_id=breakfasts[i % len(breakfasts)].id),
            MenuItem(menu_id=menu.id, dish_id=breakfasts[(i + 1) % len(breakfasts)].id),
        ]
        if drinks:
            menu_items.append(MenuItem(menu_id=menu.id, dish_id=drinks[i % len(drinks)].id))
        
        for item in menu_items:
            db.session.add(item)


def seed_all():
    app = create_app()
    
    with app.app_context():
        create_admin_user()
        create_cook_user()
        create_sample_student()
        create_additional_students()
        create_ingredients()
        create_dishes()
        db.session.commit()
        
        create_breakfast_menu()
        create_weekly_menu()
        db.session.commit()


if __name__ == '__main__':
    seed_all()
