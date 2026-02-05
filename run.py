#!/usr/bin/env python3
from app import create_app, db
from app.models import (
    User, Allergy, Dish, Ingredient, DishIngredient,
    Menu, MenuItem, Payment, Subscription, Inventory,
    MealRecord, Review, PurchaseRequest, PurchaseItem, Notification
)

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Allergy': Allergy,
        'Dish': Dish,
        'Ingredient': Ingredient,
        'DishIngredient': DishIngredient,
        'Menu': Menu,
        'MenuItem': MenuItem,
        'Payment': Payment,
        'Subscription': Subscription,
        'Inventory': Inventory,
        'MealRecord': MealRecord,
        'Review': Review,
        'PurchaseRequest': PurchaseRequest,
        'PurchaseItem': PurchaseItem,
        'Notification': Notification
    }


if __name__ == '__main__':
    app.run(
        host=app.config['APP_HOST'],
        port=app.config['APP_PORT'],
        debug=app.config.get('DEBUG', True)
    )
