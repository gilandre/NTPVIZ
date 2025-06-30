#!/usr/bin/env python3
"""
Database Manager Centralisé - NTP Monitor Enterprise
Gère toutes les connexions MySQL avec sessions thread-safe
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
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.engine = None
        self.SessionLocal = None
        self._app = None
        self.logger = logger
        
        # Configuration MySQL par défaut
        self.mysql_config = {
            'host': os.environ.get('MYSQL_HOST', 'localhost'),
            'port': int(os.environ.get('MYSQL_PORT', 3306)),
            'user': os.environ.get('MYSQL_USER', 'ntp_user'),
            'password': os.environ.get('MYSQL_PASSWORD', 'ntp_password'),
            'database': os.environ.get('MYSQL_DATABASE', 'ntp_monitor'),
            'charset': 'utf8mb4'
        }
        
        self.initialized = False
    
    def initialize(self, app=None, database_url=None):
        """Initialiser le manager avec l'application Flask"""
        try:
            self._app = app
            
            # Construire l'URL de connexion MySQL
            if database_url:
                self.database_url = database_url
            else:
                self.database_url = (
                    f"mysql+pymysql://{self.mysql_config['user']}:"
                    f"{self.mysql_config['password']}@"
                    f"{self.mysql_config['host']}:{self.mysql_config['port']}/"
                    f"{self.mysql_config['database']}?charset={self.mysql_config['charset']}"
                )
            
            # Créer le moteur avec pool de connexions optimisé
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=20,           # Pool de 20 connexions
                max_overflow=30,        # 30 connexions supplémentaires si besoin
                pool_pre_ping=True,     # Vérifier les connexions avant utilisation
                pool_recycle=3600,      # Recycler les connexions après 1h
                pool_timeout=30,        # Timeout de 30s pour obtenir une connexion
                echo=False,             # Pas de logs SQL (trop verbeux)
                isolation_level="READ_COMMITTED"  # Isolation optimale pour concurrence
            )
            
            # Créer la factory de sessions
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,        # Pas de flush automatique
                expire_on_commit=False  # Garder les objets après commit
            )
            
            # Tester la connexion
            self._test_connection()
            
            self.initialized = True
            self.logger.info("🚀 Database Manager MySQL initialisé avec succès")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation Database Manager: {e}")
            raise
    
    def _test_connection(self):
        """Tester la connexion MySQL"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT VERSION()"))
                version = result.fetchone()[0]
                self.logger.info(f"✅ Connexion MySQL réussie - Version: {version}")
        except Exception as e:
            self.logger.error(f"❌ Test connexion MySQL échoué: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """
        Context manager pour obtenir une session thread-safe
        Usage: 
            with db_manager.get_session() as session:
                # Opérations sur la base
        """
        if not self.initialized:
            raise RuntimeError("Database Manager non initialisé")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Erreur session base de données: {e}")
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_session_with_app_context(self, app=None):
        """
        Context manager avec contexte Flask + session DB
        Résout les problèmes "Working outside of application context"
        """
        target_app = app or self._app
        
        if target_app:
            with target_app.app_context():
                with self.get_session() as session:
                    yield session
        else:
            # Fallback sans contexte Flask
            with self.get_session() as session:
                yield session
    
    def execute_raw_sql(self, sql: str, params: Optional[Dict[str, Any]] = None):
        """Exécuter du SQL brut de manière sécurisée"""
        try:
            with self.get_session() as session:
                result = session.execute(text(sql), params or {})
                return result.fetchall()
        except Exception as e:
            self.logger.error(f"Erreur exécution SQL: {e}")
            raise
    
    def get_table_info(self, table_name: str):
        """Obtenir les informations d'une table"""
        try:
            sql = """
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = :database AND TABLE_NAME = :table_name
                ORDER BY ORDINAL_POSITION
            """
            return self.execute_raw_sql(sql, {
                'database': self.mysql_config['database'],
                'table_name': table_name
            })
        except Exception as e:
            self.logger.error(f"Erreur récupération info table {table_name}: {e}")
            return []
    
    def check_table_exists(self, table_name: str) -> bool:
        """Vérifier si une table existe"""
        try:
            sql = """
                SELECT COUNT(*) as count
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = :database AND TABLE_NAME = :table_name
            """
            result = self.execute_raw_sql(sql, {
                'database': self.mysql_config['database'],
                'table_name': table_name
            })
            return result[0][0] > 0 if result else False
        except Exception as e:
            self.logger.error(f"Erreur vérification table {table_name}: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Obtenir les informations de connexion"""
        return {
            'host': self.mysql_config['host'],
            'port': self.mysql_config['port'],
            'database': self.mysql_config['database'],
            'user': self.mysql_config['user'],
            'initialized': self.initialized,
            'engine_pool_size': self.engine.pool.size() if self.engine else 0,
            'engine_pool_checked_in': self.engine.pool.checkedin() if self.engine else 0,
            'engine_pool_checked_out': self.engine.pool.checkedout() if self.engine else 0
        }
    
    def close(self):
        """Fermer toutes les connexions"""
        if self.engine:
            self.engine.dispose()
            self.logger.info("🔒 Database Manager fermé")

# Instance globale du Database Manager
db_manager = DatabaseManager()

# Fonctions utilitaires pour compatibilité
def get_db_session():
    """Obtenir une session DB (fonction utilitaire)"""
    return db_manager.get_session()

def get_db_session_with_context(app=None):
    """Obtenir une session DB avec contexte Flask"""
    return db_manager.get_session_with_app_context(app)

def init_database_manager(app, database_url=None):
    """Initialiser le Database Manager"""
    return db_manager.initialize(app, database_url) 