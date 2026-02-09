from datetime import datetime, timezone
from app.extensions import db


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        # Ensure created_at is timezone-aware and return as ISO format with 'Z' suffix
        created_at_str = None
        if self.created_at:
            # If datetime is naive, assume UTC
            if self.created_at.tzinfo is None:
                aware_dt = self.created_at.replace(tzinfo=timezone.utc)
            else:
                aware_dt = self.created_at
            created_at_str = aware_dt.isoformat()
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': created_at_str
        }
    
    def mark_as_read(self):
        self.is_read = True
    
    def __repr__(self):
        return f'<Notification {self.id} - {self.title}>'
