from datetime import datetime
from app.extensions import db


class Menu(db.Model):
    __tablename__ = 'menus'
    
    id = db.Column(db.Integer, primary_key=True)
    menu_date = db.Column(db.Date, nullable=False, index=True)
    meal_type = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    menu_items = db.relationship('MenuItem', backref='menu', lazy=True, cascade='all, delete-orphan')
    meal_records = db.relationship('MealRecord', backref='menu', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('menu_date', 'meal_type', name='unique_date_meal_type'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'menu_date': self.menu_date.isoformat() if self.menu_date else None,
            'meal_type': self.meal_type,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Menu {self.menu_date} - {self.meal_type}>'


class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    menu_id = db.Column(db.Integer, db.ForeignKey('menus.id'), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'menu_id': self.menu_id,
            'dish_id': self.dish_id
        }
    
    def __repr__(self):
        return f'<MenuItem Menu {self.menu_id} - Dish {self.dish_id}>'
