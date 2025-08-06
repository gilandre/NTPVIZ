"""
Modèle User - Gestion utilisateurs et authentification
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from backend.database_manager import db

class User(UserMixin, db.Model):
    """Modèle utilisateur avec authentification"""
    
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
    
    # Suppression logique
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
    deleted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Paramètres utilisateur
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
    
    def get_current_time(self):
        """Obtenir l'heure actuelle (méthode utilitaire)"""
        return datetime.utcnow()
    
    def set_password(self, password):
        """Définir le mot de passe haché"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifier le mot de passe"""
        return check_password_hash(self.password_hash, password)
    
    def update_login_info(self):
        """Mettre à jour les informations de connexion (sans commit automatique)"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        # Pas de commit automatique - sera géré par l'appelant
    
    def soft_delete(self, deleted_by_user_id=None):
        """Suppression logique de l'utilisateur"""
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by_user_id
        self.is_active = False
    
    def restore(self):
        """Restaurer un utilisateur supprimé logiquement"""
        self.deleted_at = None
        self.deleted_by = None
        self.is_active = True
    
    @property
    def is_admin(self):
        """Vérifier si l'utilisateur est administrateur"""
        return self.role == 'admin'
    
    @property
    def is_deleted(self):
        """Vérifier si l'utilisateur est supprimé logiquement"""
        return self.deleted_at is not None
    
    @property
    def is_available(self):
        """Vérifier si l'utilisateur est disponible (actif et non supprimé)"""
        return self.is_active and not self.is_deleted
    
    @property
    def can_configure(self):
        """Vérifier si l'utilisateur peut configurer"""
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
            'preferences': self.preferences,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'deleted_by': self.deleted_by,
            'is_deleted': self.is_deleted
        }
    
    def __repr__(self):
        return f'<User {self.username}>' 
