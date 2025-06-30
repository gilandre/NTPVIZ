"""
Modle User - Gestion utilisateurs et authentification
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from backend.app import db

class User(UserMixin, db.Model):
    """Modle utilisateur avec authentification"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profil utilisateur
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='viewer')
    
    # Status et dates
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=0)
    
    # Paramtres utilisateur
    preferences = db.Column(db.JSON, default=lambda: {
        'theme': 'light',
        'language': 'fr',
        'notifications': True,
        'auto_refresh': True,
        'refresh_interval': 30
    })
    
    def __init__(self, username, email, password, role='viewer'):
        self.username = username
        self.email = email
        self.set_password(password)
        self.role = role
    
    def set_password(self, password):
        """Dfinir le mot de passe hach"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vrifier le mot de passe"""
        return check_password_hash(self.password_hash, password)
    
    def update_login(self):
        """Mettre  jour les informations de connexion"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        db.session.commit()
    
    @property
    def is_admin(self):
        """Vrifier si l'utilisateur est administrateur"""
        return self.role == 'admin'
    
    @property
    def can_configure(self):
        """Vrifier si l'utilisateur peut configurer"""
        return self.role in ['admin', 'operator']
    
    @property
    def full_name(self):
        """Nom complet de l'utilisateur"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def to_dict(self):
        """Convertir en dictionnaire pour API"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'preferences': self.preferences
        }
    
    def __repr__(self):
        return f'<User {self.username}>' 
