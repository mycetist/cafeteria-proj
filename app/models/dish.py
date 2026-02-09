from app.extensions import db


class Dish(db.Model):
    __tablename__ = 'dishes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(255))
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    menu_items = db.relationship('MenuItem', backref='dish', lazy=True, cascade='all, delete-orphan')
    dish_ingredients = db.relationship('DishIngredient', backref='dish', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='dish', lazy=True, cascade='all, delete-orphan')
    purchases = db.relationship('DishPurchase', backref='dish', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else 0,
            'category': self.category,
            'image_url': self.image_url,
            'is_available': self.is_available,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Dish {self.name}>'


class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    unit = db.Column(db.String(20), nullable=False)
    min_stock_level = db.Column(db.Numeric(10, 2), default=10.0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    dish_ingredients = db.relationship('DishIngredient', backref='ingredient', lazy=True, cascade='all, delete-orphan')
    inventory = db.relationship('Inventory', backref='ingredient', lazy=True, uselist=False, cascade='all, delete-orphan')
    purchase_items = db.relationship('PurchaseItem', backref='ingredient', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'unit': self.unit,
            'min_stock_level': float(self.min_stock_level) if self.min_stock_level else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Ingredient {self.name}>'


class DishIngredient(db.Model):
    __tablename__ = 'dish_ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity_required = db.Column(db.Numeric(10, 2), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'dish_id': self.dish_id,
            'ingredient_id': self.ingredient_id,
            'quantity_required': float(self.quantity_required) if self.quantity_required else 0
        }
    
    def __repr__(self):
        return f'<DishIngredient Dish {self.dish_id} - Ingredient {self.ingredient_id}>'
