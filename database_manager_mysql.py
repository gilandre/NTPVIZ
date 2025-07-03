#!/usr/bin/env python3
"""
Database Manager MySQL - Gestionnaire centralisé MySQL pour NTP Monitor Enterprise
VERSION PRODUCTION MYSQL
"""

import os
import logging
import threading
from contextlib import contextmanager
from typing import Optional, Any, Dict
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import pymysql

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manager centralisé pour la base de données MySQL"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, 'initialized'):
            return
            
        self.logger = logging.getLogger(__name__)
        self.engine = None
        self.SessionLocal = None
        self.initialized = False
        
        # Configuration MySQL
        self.mysql_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '',  # Authentification socket Unix
            'database': 'ntp_monitor'
        }
        
        # URL de connexion MySQL
        self.database_url = (
            f"mysql+pymysql://{self.mysql_config['user']}@"
            f"{self.mysql_config['host']}:{self.mysql_config['port']}/{self.mysql_config['database']}"
        )
        
        self.logger.info(f"🗃️ Database Manager MySQL initialisé")
        self.logger.info(f"🔌 URL MySQL: {self.database_url}")

    def initialize(self, app=None):
        """Initialiser la connexion à la base de données MySQL"""
        if self.initialized:
            self.logger.info("✅ Database Manager déjà initialisé")
            return True

        try:
            self.logger.info(f"🔌 Tentative connexion MySQL: {self.mysql_config['host']}:{self.mysql_config['port']}")
            self.logger.info(f"📊 Base de données: {self.mysql_config['database']}")
            self.logger.info(f"👤 Utilisateur: {self.mysql_config['user']}")
            
            # Test de connexion avec PyMySQL direct
            try:
                import pymysql
                test_conn = pymysql.connect(
                    host=self.mysql_config['host'],
                    port=self.mysql_config['port'],
                    user=self.mysql_config['user'],
                    password=self.mysql_config['password'],
                    database=self.mysql_config['database'],
                    autocommit=True,
                    charset='utf8mb4'
                )
                test_conn.close()
                self.logger.info("✅ Test connexion MySQL réussie")
                
            except Exception as e:
                self.logger.error(f"❌ Test connexion MySQL échoué: {e}")
                return False
            
            # Créer l'engine SQLAlchemy
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Test de connexion SQLAlchemy
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                self.logger.info("✅ Test SQLAlchemy MySQL réussie")
            
            # Créer la factory de sessions
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            self.initialized = True
            self.logger.info("✅ Database Manager MySQL initialisé avec succès")
            
            # Créer les tables si nécessaire
            self._create_tables()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation Database Manager MySQL: {e}")
            import traceback
            self.logger.error(f"Stack trace: {traceback.format_exc()}")
            return False

    def _create_tables(self):
        """Créer les tables si elles n'existent pas"""
        try:
            # Import dynamique pour éviter l'import circulaire
            from backend.database import Base
            
            # Créer toutes les tables
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("✅ Tables MySQL créées/vérifiées")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur création tables MySQL: {e}")

    def get_session(self) -> Optional[Session]:
        """Obtenir une nouvelle session de base de données"""
        if not self.initialized:
            self.logger.warning("Database Manager non initialisé")
            return None
            
        try:
            return self.SessionLocal()
        except Exception as e:
            self.logger.error(f"Erreur création session MySQL: {e}")
            return None

    @contextmanager
    def get_session_context(self):
        """Context manager pour une session de base de données"""
        session = self.get_session()
        if session is None:
            raise Exception("Impossible d'obtenir une session de base de données MySQL")
            
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Erreur dans la session MySQL: {e}")
            raise
        finally:
            session.close()

    def execute_query(self, query: str, params: dict = None) -> Any:
        """Exécuter une requête SQL"""
        if not self.initialized:
            return None
            
        try:
            with self.get_session_context() as session:
                result = session.execute(text(query), params or {})
                return result.fetchall()
        except Exception as e:
            self.logger.error(f"Erreur exécution requête MySQL: {e}")
            return None

    def close(self):
        """Fermer la connexion à la base de données"""
        if self.engine:
            self.engine.dispose()
            self.logger.info("🔌 Connexion MySQL fermée")

# Instance globale
db_manager = DatabaseManager()

# Compatibilité Flask-SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, JSON, ForeignKey
from backend.database import Base

# Variable db pour compatibilité
db = db_manager

# Attributs SQLAlchemy pour compatibilité Flask-SQLAlchemy
db_manager.Model = Base
db_manager.Column = Column
db_manager.Integer = Integer
db_manager.String = String
db_manager.DateTime = DateTime
db_manager.Boolean = Boolean
db_manager.Float = Float
db_manager.Text = Text
db_manager.JSON = JSON
db_manager.ForeignKey = ForeignKey

# Même chose pour db
db.Model = Base
db.Column = Column
db.Integer = Integer
db.String = String
db.DateTime = DateTime
db.Boolean = Boolean
db.Float = Float
db.Text = Text
db.JSON = JSON
db.ForeignKey = ForeignKey

# Functions helper pour compatibilité
def get_db_session_with_context():
    """Fonction helper pour obtenir une session avec context manager"""
    return db_manager.get_session_context()

def init_database_manager(app=None):
    """Initialiser le Database Manager"""
    return db_manager.initialize(app) 