from datetime import datetime
from app.extensions import db
import bcrypt


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    balance = db.Column(db.Numeric(10, 2), default=0.00)
    
    payments = db.relationship('Payment', backref='user', lazy=True, cascade='all, delete-orphan')
    dish_purchases = db.relationship('DishPurchase', backref='user', lazy=True, cascade='all, delete-orphan')
    subscriptions = db.relationship('Subscription', backref='user', lazy=True, cascade='all, delete-orphan')
    meal_records = db.relationship('MealRecord', backref='user', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='user', lazy=True, cascade='all, delete-orphan')
    allergies = db.relationship('Allergy', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    created_purchase_requests = db.relationship(
        'PurchaseRequest',
        foreign_keys='PurchaseRequest.created_by',
        backref='creator',
        lazy=True
    )
    approved_purchase_requests = db.relationship(
        'PurchaseRequest',
        foreign_keys='PurchaseRequest.approved_by',
        backref='approver',
        lazy=True
    )
    
    def set_password(self, password):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def has_role(self, role):
        return self.role == role
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'balance': float(self.balance) if self.balance else 0.00
        }
    
    def add_balance(self, amount):
        """Add amount to user's balance"""
        current = float(self.balance) if self.balance else 0.00
        self.balance = current + amount
    
    def deduct_balance(self, amount):
        """Deduct amount from user's balance if sufficient"""
        current = float(self.balance) if self.balance else 0.00
        if current < amount:
            return False
        self.balance = current - amount
        return True
    
    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Allergy(db.Model):
    __tablename__ = 'allergies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    allergy_type = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'allergy_type': self.allergy_type,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Allergy {self.allergy_type} for User {self.user_id}>'
