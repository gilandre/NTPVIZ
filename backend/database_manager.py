#!/usr/bin/env python3
"""
Database Manager - Gestionnaire centralisé MySQL pour NTP Monitor Enterprise
VERSION CORRIGÉE - Erreur syntaxe ligne 85 résolue
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

# Base sera importée dynamiquement pour éviter l'import circulaire

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manager centralisé pour la base de données MySQL"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
            
        self.logger = logging.getLogger(__name__)
        self.engine = None
        self.SessionLocal = None
        self._app = None
        self.initialized = False
        
        # Configuration MySQL
        self.mysql_config = {
            'host': os.environ.get('MYSQL_HOST', 'localhost'),
            'port': int(os.environ.get('MYSQL_PORT', 3306)),
            'user': os.environ.get('MYSQL_USER', 'ntp_user'),
            'password': os.environ.get('MYSQL_PASSWORD', 'NTP_Monitor_2025!'),
            'database': os.environ.get('MYSQL_DATABASE', 'ntp_monitor')
        }
        
        # URL de connexion MySQL avec gestion d'erreurs de charset
        self.database_url = (
            f"mysql+pymysql://{self.mysql_config['user']}:{self.mysql_config['password']}@"
            f"{self.mysql_config['host']}:{self.mysql_config['port']}/{self.mysql_config['database']}"
            f"?charset=utf8mb4&autocommit=true"
        )
        
        # ⚠️ PAS D'INITIALISATION AUTOMATIQUE - Éviter les imports circulaires
        self.logger.info("📝 Database Manager créé - Initialisation à la demande")
    
    def initialize(self):
        """Initialiser le gestionnaire de base de données"""
        if self.initialized:
            self.logger.info("Database Manager déjà initialisé")
            return True
        
        try:
            # Créer le moteur SQLAlchemy
            self.logger.info(f"🔌 Tentative connexion MySQL: {self.mysql_config['host']}:{self.mysql_config['port']}")
            self.logger.info(f"📊 Base de données: {self.mysql_config['database']}")
            self.logger.info(f"👤 Utilisateur: {self.mysql_config['user']}")
            
            # Test de connexion MySQL direct
            try:
                test_conn = pymysql.connect(
                    host=self.mysql_config['host'],
                    port=self.mysql_config['port'],
                    user=self.mysql_config['user'],
                    password=self.mysql_config['password'],
                    connect_timeout=10
                )
                test_conn.close()
                self.logger.info("✅ Test connexion MySQL direct réussi")
            except Exception as e:
                self.logger.error(f"❌ Test connexion MySQL direct échoué: {e}")
                # Essayer de créer la base de données
                try:
                    root_conn = pymysql.connect(
                        host=self.mysql_config['host'],
                        port=self.mysql_config['port'],
                        user=self.mysql_config['user'],
                        password=self.mysql_config['password'],
                        connect_timeout=10
                    )
                    cursor = root_conn.cursor()
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.mysql_config['database']}")
                    cursor.execute(f"USE {self.mysql_config['database']}")
                    root_conn.commit()
                    root_conn.close()
                    self.logger.info(f"✅ Base de données {self.mysql_config['database']} créée/vérifiée")
                except Exception as e2:
                    self.logger.error(f"❌ Impossible de créer la base de données: {e2}")
                    raise
            
            # Créer le moteur SQLAlchemy
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=10,
                max_overflow=20,
                echo=False  # Réduire les logs SQL
            )
            
            # Tester la connexion SQLAlchemy
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT VERSION()"))
                version = result.fetchone()[0]
                self.logger.info(f"✅ Connexion SQLAlchemy réussie - MySQL {version}")
            
            # Créer les tables (import dynamique pour éviter l'import circulaire)
            try:
                from backend.database import Base
                Base.metadata.create_all(self.engine)
                self.logger.info("✅ Tables créées avec succès")
                # Appliquer la migration server_types (idempotent)
                try:
                    scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
                    migrate_sql = os.path.join(scripts_dir, 'migrate_server_types.sql')
                    if os.path.exists(migrate_sql):
                        with open(migrate_sql, 'r') as f:
                            ddl_all = f.read()
                        statements = [s.strip() for s in ddl_all.split(';') if s.strip()]
                        with self.engine.begin() as conn:
                            for stmt in statements:
                                try:
                                    conn.execute(text(stmt))
                                except Exception as stmt_err:
                                    # Tolérer les erreurs d'existence (FK déjà posée, index existant...)
                                    self.logger.debug(f"Migration server_types - statement ignoré: {stmt_err}")
                        self.logger.info("✅ Migration server_types appliquée (si nécessaire)")
                except Exception as mig_e:
                    self.logger.warning(f"⚠️ Migration server_types ignorée/partielle: {mig_e}")
                # Vérifier/Créer la table audit_logs si absente
                try:
                    if not self.check_table_exists('audit_logs'):
                        self.logger.info("🛠️ Création de la table audit_logs...")
                        from sqlalchemy import text as _text
                        ddl = (
                            "CREATE TABLE IF NOT EXISTS audit_logs ("
                            "id INT AUTO_INCREMENT PRIMARY KEY,"
                            "timestamp DATETIME NOT NULL,"
                            "user_id INT NULL,"
                            "username VARCHAR(150) NULL,"
                            "role VARCHAR(50) NULL,"
                            "action VARCHAR(100) NOT NULL,"
                            "resource VARCHAR(100) NULL,"
                            "resource_id VARCHAR(100) NULL,"
                            "details TEXT NULL,"
                            "ip_address VARCHAR(64) NULL,"
                            "user_agent TEXT NULL,"
                            "method VARCHAR(10) NULL,"
                            "endpoint VARCHAR(200) NULL,"
                            "url TEXT NULL,"
                            "INDEX idx_timestamp (timestamp),"
                            "INDEX idx_user_id (user_id),"
                            "INDEX idx_action (action),"
                            "INDEX idx_resource (resource),"
                            "INDEX idx_resource_id (resource_id)) "
                            "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
                        )
                        with self.engine.begin() as conn:
                            conn.execute(_text(ddl))
                        self.logger.info("✅ Table audit_logs créée")
                except Exception as e:
                    self.logger.warning(f"⚠️ Création automatique de audit_logs échouée: {e}")
            except ImportError as e:
                self.logger.warning(f"⚠️ Import Base échoué: {e} - Tables créées plus tard")
            except Exception as e:
                self.logger.warning(f"⚠️ Erreur création tables: {e} - Tables créées plus tard")
            
            # Créer la fabrique de sessions
            self.SessionLocal = sessionmaker(bind=self.engine)
            
            self.initialized = True
            self.logger.info("✅ Database Manager initialisé avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation Database Manager: {e}")
            import traceback
            self.logger.error(f"Stack trace: {traceback.format_exc()}")
            return False
    
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
            # Attendre un peu au cas où l'initialisation serait en cours
            import time
            max_retries = 3
            for i in range(max_retries):
                if self.initialized:
                    break
                self.logger.warning(f"Database Manager non encore initialisé, tentative {i+1}/{max_retries}")
                time.sleep(1)
            
            if not self.initialized:
                error_msg = (
                    f"Database Manager non initialisé après {max_retries} tentatives. "
                    f"Configuration MySQL: {self.mysql_config['host']}:{self.mysql_config['port']}/{self.mysql_config['database']} "
                    f"(user: {self.mysql_config['user']})"
                )
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
        
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
                from sqlalchemy import text
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
    return db_manager.initialize()

# ================== COMPATIBILITÉ MODELS SQLALCHEMY ==================

# Variable 'db' pour compatibilité avec les modèles SQLAlchemy
# Elle pointe vers l'instance SQLAlchemy du database manager
from flask_sqlalchemy import SQLAlchemy

class DatabaseProxy:
    """Proxy pour fournir une interface db compatible avec Flask-SQLAlchemy"""
    
    def __init__(self):
        self._db = None
        self._models = {}
        
    def init_app(self, app):
        """Initialiser avec l'app Flask"""
        self._db = SQLAlchemy(app)
        return self._db
        
    @property
    def Model(self):
        """Retourner la classe Model de SQLAlchemy"""
        if self._db:
            return self._db.Model
        # Fallback vers SQLAlchemy de base
        from sqlalchemy.ext.declarative import declarative_base
        if not hasattr(self, '_base_model'):
            self._base_model = declarative_base()
        return self._base_model
    
    @property
    def Column(self):
        """Retourner Column de SQLAlchemy"""
        if self._db:
            return self._db.Column
        from sqlalchemy import Column
        return Column
    
    @property
    def Integer(self):
        """Retourner Integer de SQLAlchemy"""
        if self._db:
            return self._db.Integer
        from sqlalchemy import Integer
        return Integer
    
    @property
    def String(self):
        """Retourner String de SQLAlchemy"""
        if self._db:
            return self._db.String
        from sqlalchemy import String
        return String
    
    @property
    def DateTime(self):
        """Retourner DateTime de SQLAlchemy"""
        if self._db:
            return self._db.DateTime
        from sqlalchemy import DateTime
        return DateTime
    
    @property
    def Boolean(self):
        """Retourner Boolean de SQLAlchemy"""
        if self._db:
            return self._db.Boolean
        from sqlalchemy import Boolean
        return Boolean
    
    @property
    def Float(self):
        """Retourner Float de SQLAlchemy"""
        if self._db:
            return self._db.Float
        from sqlalchemy import Float
        return Float
    
    @property
    def Text(self):
        """Retourner Text de SQLAlchemy"""
        if self._db:
            return self._db.Text
        from sqlalchemy import Text
        return Text
    
    @property
    def JSON(self):
        """Retourner JSON de SQLAlchemy"""
        if self._db:
            return self._db.JSON
        from sqlalchemy import JSON
        return JSON
    
    @property
    def ForeignKey(self):
        """Retourner ForeignKey de SQLAlchemy"""
        if self._db:
            return self._db.ForeignKey
        from sqlalchemy import ForeignKey
        return ForeignKey
    
    @property
    def relationship(self):
        """Retourner relationship de SQLAlchemy"""
        if self._db:
            return self._db.relationship
        from sqlalchemy.orm import relationship
        return relationship
    
    @property
    def session(self):
        """Retourner une session via le database manager"""
        if self._db and hasattr(self._db, 'session'):
            return self._db.session
        # Fallback vers le database manager
        return db_manager.get_session()

# Créer l'instance db pour compatibilité avec les modèles
db = DatabaseProxy()

# Initialisation automatique du Database Manager
try:
    if not db_manager.initialized:
        logger.info("🚀 Initialisation automatique du Database Manager...")
        db_manager.initialize()
except Exception as e:
    logger.warning(f"⚠️ Initialisation automatique échouée: {e} - Sera réessayée à la demande") 