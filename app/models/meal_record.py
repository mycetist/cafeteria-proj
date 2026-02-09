from datetime import datetime
from app.extensions import db


class MealRecord(db.Model):
    __tablename__ = 'meal_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menus.id'), nullable=False)
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    meal_type = db.Column(db.String(20), nullable=False)
    is_confirmed = db.Column(db.Boolean, default=False)
    

    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'menu_id': self.menu_id,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'meal_type': self.meal_type,
            'is_confirmed': self.is_confirmed
        }
    
    def __repr__(self):
        return f'<MealRecord User {self.user_id} - Menu {self.menu_id}>'
