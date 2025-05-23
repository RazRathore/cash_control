from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class Client(db.Model):
    """Client model for storing client information"""
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    client_type = db.Column(db.Enum('Individual', 'Corporate', name='client_type'), nullable=False, default='Individual')
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(50), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(50), nullable=True, default='India')
    postal_code = db.Column(db.String(20), nullable=True)
    status = db.Column(db.Enum('Active', 'Pending', 'Inactive', name='client_status'), default='Active')
    balance = db.Column(db.Integer, default=0)  # Storing in paise (1/100 of a rupee)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert client object to dictionary"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'name': self.name,
            'client_type': self.client_type,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'postal_code': self.postal_code,
            'status': self.status,
            'balance': float(self.balance) if self.balance is not None else 0.00,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def generate_client_id(cls, client_type='I'):
        """Generate a new client ID"""
        prefix = 'CLI' if client_type == 'Individual' else 'CLC'
        last_client = cls.query.order_by(cls.id.desc()).first()
        next_id = 1001 if not last_client else last_client.id + 1
        return f"{prefix}{next_id:04d}"


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    debit_amount = db.Column(db.Integer, default=0)  # Storing in paise (1/100 of a rupee)
    credit_amount = db.Column(db.Integer, default=0)  # Storing in paise (1/100 of a rupee)
    balance = db.Column(db.Integer, default=0)  # Storing in paise (1/100 of a rupee)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    client = db.relationship('Client', backref='transactions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'name': self.name,
            'description': self.description,
            'debit_amount': self.debit_amount,
            'credit_amount': self.credit_amount,
            'balance': self.balance,
            'client_id': self.client_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
