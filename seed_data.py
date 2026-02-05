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
            is_active=True
        )
        salt = bcrypt.gensalt()
        student.password_hash = bcrypt.hashpw('student123'.encode('utf-8'), salt).decode('utf-8')
        db.session.add(student)
    return student


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
        {
            'name': 'Курица с рисом',
            'description': 'Куриная грудка на гриле с отварным рисом и овощами',
            'price': 150.00,
            'category': 'main',
            'image_url': '/static/images/chicken_rice.jpg'
        },
        {
            'name': 'Говяжье рагу',
            'description': 'Сытное говяжье рагу с картофелем и морковью',
            'price': 180.00,
            'category': 'main',
            'image_url': '/static/images/beef_stew.jpg'
        },
        {
            'name': 'Рыба с картофелем фри',
            'description': 'Хрустящее филе рыбы с картофелем фри',
            'price': 160.00,
            'category': 'main',
            'image_url': '/static/images/fish_chips.jpg'
        },
        {
            'name': 'Паста Карбонара',
            'description': 'Сливочная паста с сыром и яйцом',
            'price': 140.00,
            'category': 'main',
            'image_url': '/static/images/carbonara.jpg'
        },
        {
            'name': 'Овощной суп',
            'description': 'Свежий овощной суп с хлебом',
            'price': 80.00,
            'category': 'soup',
            'image_url': '/static/images/veg_soup.jpg'
        },
        {
            'name': 'Куриный суп',
            'description': 'Горячий куриный суп с лапшой',
            'price': 90.00,
            'category': 'soup',
            'image_url': '/static/images/chicken_soup.jpg'
        },
        {
            'name': 'Свежий салат',
            'description': 'Овощной салат с помидорами и огурцами',
            'price': 60.00,
            'category': 'salad',
            'image_url': '/static/images/salad.jpg'
        },
        {
            'name': 'Салат из капусты',
            'description': 'Хрустящий салат из капусты с морковью',
            'price': 50.00,
            'category': 'salad',
            'image_url': '/static/images/cabbage_salad.jpg'
        },
        {
            'name': 'Яблочный пирог',
            'description': 'Сладкий яблочный пирог с корицей',
            'price': 70.00,
            'category': 'dessert',
            'image_url': '/static/images/apple_pie.jpg'
        },
        {
            'name': 'Фруктовый салат',
            'description': 'Свежие сезонные фрукты',
            'price': 65.00,
            'category': 'dessert',
            'image_url': '/static/images/fruit_cup.jpg'
        },
        {
            'name': 'Молоко',
            'description': 'Свежее молоко 250мл',
            'price': 40.00,
            'category': 'drink',
            'image_url': '/static/images/milk.jpg'
        },
        {
            'name': 'Фруктовый сок',
            'description': 'Свежевыжатый апельсиновый сок 250мл',
            'price': 55.00,
            'category': 'drink',
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
    
    soups = Dish.query.filter_by(category='soup').all()
    mains = Dish.query.filter_by(category='main').all()
    salads = Dish.query.filter_by(category='salad').all()
    desserts = Dish.query.filter_by(category='dessert').all()
    drinks = Dish.query.filter_by(category='drink').all()
    
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


def seed_all():
    app = create_app()
    
    with app.app_context():
        create_admin_user()
        create_cook_user()
        create_sample_student()
        create_ingredients()
        create_dishes()
        db.session.commit()
        
        create_weekly_menu()
        db.session.commit()


if __name__ == '__main__':
    seed_all()
