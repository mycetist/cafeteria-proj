from datetime import datetime
from app.extensions import db


class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False, unique=True)
    quantity = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ingredient_id': self.ingredient_id,
            'quantity': float(self.quantity) if self.quantity else 0,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    def is_low_stock(self):
        if self.ingredient and self.ingredient.min_stock_level:
            return self.quantity < self.ingredient.min_stock_level
        return False
    
    def __repr__(self):
        return f'<Inventory Ingredient {self.ingredient_id} - {self.quantity}>'
