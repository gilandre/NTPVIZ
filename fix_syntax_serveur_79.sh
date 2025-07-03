#!/bin/bash
# Script de correction erreur syntaxe database_manager.py
set -e

echo "🔧 CORRECTION ERREUR SYNTAXE DATABASE_MANAGER.PY"
echo "================================================"

PROJECT_DIR="/opt/NTPVIZ"
SERVICE_NAME="ntp-monitor"

# Stopper le service
echo "🛑 Arrêt du service..."
systemctl stop $SERVICE_NAME || true

# Aller dans le répertoire du projet
cd $PROJECT_DIR

echo "🔨 Correction du fichier database_manager.py..."

# Créer la version corrigée simplifiée
cat > backend/database_manager.py << 'EOF'
#!/usr/bin/env python3
"""
Database Manager - Version corrigée erreur syntaxe ligne 85
"""

import os
import logging
import threading
from contextlib import contextmanager
from typing import Optional, Any, Dict
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pymysql

logger = logging.getLogger(__name__)

class DatabaseManager:
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
        self.initialized = False
        
        # Configuration SQLite forcée
        self.database_url = f"sqlite:///{os.path.dirname(os.path.abspath(__file__))}/../instance/ntp_monitor.db"
        self.logger.info("🗃️ Configuration SQLite FORCÉE")
    
    def initialize(self):
        if self.initialized:
            return True
        
        try:
            # Créer le répertoire instance
            instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance')
            os.makedirs(instance_dir, exist_ok=True)
            
            # Créer le moteur SQLAlchemy
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                echo=False
            )
            
            # Tester la connexion
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT sqlite_version()"))
                version = result.fetchone()[0]
                self.logger.info(f"✅ SQLite connecté - Version: {version}")
            
            # Créer les tables
            try:
                from backend.database import Base
                Base.metadata.create_all(self.engine)
                self.logger.info("✅ Tables créées")
            except Exception as e:
                self.logger.warning(f"⚠️ Tables: {e}")
            
            self.SessionLocal = sessionmaker(bind=self.engine)
            self.initialized = True
            self.logger.info("✅ Database Manager initialisé")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation: {e}")
            return False
    
    @contextmanager
    def get_session(self):
        if not self.initialized:
            if not self.initialize():
                raise RuntimeError("Database non initialisé")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Erreur session: {e}")
            raise
        finally:
            session.close()
    
    def close(self):
        if self.engine:
            self.engine.dispose()

# Instance globale
db_manager = DatabaseManager()

def get_db_session():
    return db_manager.get_session()

def init_database_manager(app=None, database_url=None):
    return db_manager.initialize()

# Proxy SQLAlchemy
class DatabaseProxy:
    @property
    def Model(self):
        from sqlalchemy.ext.declarative import declarative_base
        if not hasattr(self, '_base_model'):
            self._base_model = declarative_base()
        return self._base_model
    
    @property
    def Column(self):
        from sqlalchemy import Column
        return Column
    
    @property
    def Integer(self):
        from sqlalchemy import Integer
        return Integer
    
    @property
    def String(self):
        from sqlalchemy import String
        return String
    
    @property
    def DateTime(self):
        from sqlalchemy import DateTime
        return DateTime
    
    @property
    def Boolean(self):
        from sqlalchemy import Boolean
        return Boolean
    
    @property
    def Text(self):
        from sqlalchemy import Text
        return Text
    
    @property
    def ForeignKey(self):
        from sqlalchemy import ForeignKey
        return ForeignKey
    
    @property
    def session(self):
        return db_manager.get_session()

db = DatabaseProxy()
EOF

# Corriger les permissions
chown -R ntp-monitor:ntp-monitor $PROJECT_DIR/backend/database_manager.py
chown -R ntp-monitor:ntp-monitor $PROJECT_DIR/instance/ 2>/dev/null || true

echo "✅ Fichier database_manager.py corrigé"

# Test de syntaxe
cd $PROJECT_DIR
sudo -u ntp-monitor bash -c "
source .venv/bin/activate
python3 -m py_compile backend/database_manager.py
"

if [ $? -eq 0 ]; then
    echo "✅ Syntaxe Python correcte"
else
    echo "❌ Erreur de syntaxe"
    exit 1
fi

# Redémarrer le service
echo "🔄 Redémarrage du service..."
systemctl daemon-reload
systemctl restart $SERVICE_NAME

sleep 5

# Vérifier le statut
systemctl status $SERVICE_NAME --no-pager -l

echo "🎉 CORRECTION TERMINÉE !"
echo "Test: curl -I http://79.137.36.66:5000/" 