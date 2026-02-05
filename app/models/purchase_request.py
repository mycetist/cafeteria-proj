from datetime import datetime
from app.extensions import db


class PurchaseRequest(db.Model):
    __tablename__ = 'purchase_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text)
    
    purchase_items = db.relationship('PurchaseItem', backref='request', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'created_by': self.created_by,
            'approved_by': self.approved_by,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'notes': self.notes
        }
    
    def __repr__(self):
        return f'<PurchaseRequest {self.id} - {self.status}>'


class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('purchase_requests.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    estimated_cost = db.Column(db.Numeric(10, 2), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'ingredient_id': self.ingredient_id,
            'quantity': float(self.quantity) if self.quantity else 0,
            'estimated_cost': float(self.estimated_cost) if self.estimated_cost else 0
        }
    
    def __repr__(self):
        return f'<PurchaseItem Request {self.request_id} - Ingredient {self.ingredient_id}>'
