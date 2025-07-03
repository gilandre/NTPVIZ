#!/usr/bin/env python3
"""
Database Manager SQLite - Gestionnaire centralisé SQLite pour NTP Monitor Enterprise
VERSION CORRIGÉE POUR SQLITE UNIQUEMENT
"""

import os
import logging
import threading
from contextlib import contextmanager
from typing import Optional, Any, Dict
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manager centralisé pour la base de données SQLite"""

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
        
        # Configuration SQLite
        self.db_path = Path(__file__).parent.parent / 'instance' / 'ntp_monitor.db'
        self.db_path.parent.mkdir(exist_ok=True)
        self.database_url = f'sqlite:///{self.db_path}'
        
        self.logger.info(f"🗃️ Database Manager SQLite initialisé")
        self.logger.info(f"📁 Chemin base: {self.db_path}")

    def initialize(self, app=None):
        """Initialiser la connexion à la base de données SQLite"""
        if self.initialized:
            self.logger.info("✅ Database Manager déjà initialisé")
            return True

        try:
            self.logger.info(f"🔌 Connexion SQLite: {self.database_url}")
            
            # Créer l'engine SQLite
            self.engine = create_engine(
                self.database_url,
                poolclass=StaticPool,
                connect_args={
                    'check_same_thread': False,
                    'timeout': 20
                },
                echo=False
            )
            
            # Test de connexion
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Créer la factory de sessions
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            self.initialized = True
            self.logger.info("✅ Database Manager SQLite initialisé avec succès")
            
            # Créer les tables si nécessaire
            self._create_tables()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation Database Manager: {e}")
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
            self.logger.info("✅ Tables SQLite créées/vérifiées")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur création tables: {e}")

    def get_session(self) -> Optional[Session]:
        """Obtenir une nouvelle session de base de données"""
        if not self.initialized:
            self.logger.warning("Database Manager non initialisé")
            return None
            
        try:
            return self.SessionLocal()
        except Exception as e:
            self.logger.error(f"Erreur création session: {e}")
            return None

    @contextmanager
    def get_session_context(self):
        """Context manager pour une session de base de données"""
        session = self.get_session()
        if session is None:
            raise Exception("Impossible d'obtenir une session de base de données")
            
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Erreur dans la session: {e}")
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
            self.logger.error(f"Erreur exécution requête: {e}")
            return None

    def close(self):
        """Fermer la connexion à la base de données"""
        if self.engine:
            self.engine.dispose()
            self.logger.info("🔌 Connexion SQLite fermée")

# Instance globale
db_manager = DatabaseManager()

# Function helper pour compatibilité
def get_db_session_with_context():
    """Fonction helper pour obtenir une session avec context manager"""
    return db_manager.get_session_context()

def init_database_manager(app=None):
    """Initialiser le Database Manager"""
    return db_manager.initialize(app) 