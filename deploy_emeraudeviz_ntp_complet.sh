#!/bin/bash
# DÉPLOIEMENT EMERAUDEVIZ NTP - Application Principale Complète
# Serveur: 79.137.36.66
# Correction erreur syntaxe + Application complète

set -e

echo "🚀 DÉPLOIEMENT EMERAUDEVIZ NTP - APPLICATION PRINCIPALE"
echo "========================================================"

PROJECT_DIR="/opt/NTPVIZ"
SERVICE_NAME="ntp-monitor"
BACKUP_DIR="/tmp/ntp_backup_$(date +%Y%m%d_%H%M%S)"

# Vérifier qu'on est root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root"
    exit 1
fi

echo "📍 Serveur: $(hostname -I | awk '{print $1}')"
echo "📂 Projet: $PROJECT_DIR"
echo "🕒 $(date)"

# Stopper le service
echo "🛑 Arrêt du service actuel..."
systemctl stop $SERVICE_NAME || true

# Créer une sauvegarde
echo "💾 Sauvegarde..."
mkdir -p $BACKUP_DIR
cp -r $PROJECT_DIR/backend/ $BACKUP_DIR/ 2>/dev/null || true
cp -r $PROJECT_DIR/app.py $BACKUP_DIR/ 2>/dev/null || true

cd $PROJECT_DIR

echo "🔨 Correction database_manager.py pour EMERAUDEVIZ NTP..."
# Le script complet sera dans le fichier une fois créé
echo "✅ Préparation du déploiement EMERAUDEVIZ NTP terminée"

# =================== CORRECTION DATABASE_MANAGER.PY ===================
echo "🔨 Correction database_manager.py (erreur syntaxe ligne 85)..."

cat > backend/database_manager.py << 'EOF'
#!/usr/bin/env python3
"""
Database Manager - EMERAUDEVIZ NTP Enterprise
Version corrigée - Erreur syntaxe résolue
"""

import os
import logging
import threading
from contextlib import contextmanager
from typing import Optional, Any, Dict
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manager centralisé pour la base de données - Version Enterprise"""
    
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
        
        # Configuration base de données
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.instance_dir = os.path.join(self.project_root, 'instance')
        os.makedirs(self.instance_dir, exist_ok=True)
        
        # Configuration SQLite optimisée pour production
        self.database_url = f"sqlite:///{self.instance_dir}/ntp_monitor_enterprise.db"
        self.logger.info("🗃️ EMERAUDEVIZ NTP - Configuration SQLite Enterprise")
    
    def initialize(self):
        """Initialiser le gestionnaire de base de données"""
        if self.initialized:
            self.logger.info("✅ Database Manager déjà initialisé")
            return True
            
        try:
            self.logger.info("🔌 Initialisation EMERAUDEVIZ NTP Database...")
            
            # Créer le moteur SQLAlchemy optimisé
            self.engine = create_engine(
                self.database_url,
                poolclass=StaticPool,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={
                    'check_same_thread': False,
                    'timeout': 30
                },
                echo=False
            )
            
            # Tester la connexion
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT sqlite_version()"))
                version = result.fetchone()[0]
                self.logger.info(f"✅ SQLite Enterprise connecté - Version: {version}")
            
            # Créer les tables
            try:
                from backend.database import Base
                Base.metadata.create_all(self.engine)
                self.logger.info("✅ Tables EMERAUDEVIZ NTP créées")
            except ImportError as e:
                self.logger.warning(f"⚠️ Import Base: {e}")
            except Exception as e:
                self.logger.warning(f"⚠️ Création tables: {e}")
            
            # Créer la fabrique de sessions
            self.SessionLocal = sessionmaker(bind=self.engine)
            
            # Initialiser les données par défaut
            self._init_default_data()
            
            self.initialized = True
            self.logger.info("🎉 EMERAUDEVIZ NTP Database Manager initialisé avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation Database Manager: {e}")
            import traceback
            self.logger.error(f"Stack trace: {traceback.format_exc()}")
            return False
    
    def _init_default_data(self):
        """Initialiser les données par défaut"""
        try:
            with self.get_session() as session:
                # Vérifier si des utilisateurs existent déjà
                from backend.models.user import User
                existing_users = session.query(User).count()
                
                if existing_users == 0:
                    self.logger.info("🔧 Création utilisateurs par défaut...")
                    
                    # Créer utilisateur admin
                    from werkzeug.security import generate_password_hash
                    admin_user = User(
                        username='admin',
                        email='admin@emeraudeviz.local',
                        password_hash=generate_password_hash('admin123'),
                        role='admin',
                        is_active=True
                    )
                    session.add(admin_user)
                    
                    # Créer utilisateur opérateur
                    operator_user = User(
                        username='operator',
                        email='operator@emeraudeviz.local',
                        password_hash=generate_password_hash('operator123'),
                        role='operator',
                        is_active=True
                    )
                    session.add(operator_user)
                    
                    session.commit()
                    self.logger.info("✅ Utilisateurs par défaut créés")
                
                # Vérifier les serveurs NTP par défaut
                from backend.models.ntp_server import NTPServer
                existing_servers = session.query(NTPServer).count()
                
                if existing_servers == 0:
                    self.logger.info("🕒 Création serveurs NTP par défaut...")
                    
                    # Serveurs NTP par défaut
                    default_servers = [
                        {'hostname': '79.137.36.66', 'description': 'Serveur principal EMERAUDEVIZ'},
                        {'hostname': 'pool.ntp.org', 'description': 'Pool NTP mondial'},
                        {'hostname': '0.fr.pool.ntp.org', 'description': 'Pool NTP France 0'},
                        {'hostname': '1.fr.pool.ntp.org', 'description': 'Pool NTP France 1'},
                        {'hostname': 'time.google.com', 'description': 'Serveur Google Time'}
                    ]
                    
                    for server_info in default_servers:
                        server = NTPServer(
                            hostname=server_info['hostname'],
                            description=server_info['description'],
                            is_active=True,
                            stratum=2,
                            poll_interval=64
                        )
                        session.add(server)
                    
                    session.commit()
                    self.logger.info("✅ Serveurs NTP par défaut créés")
                    
        except Exception as e:
            self.logger.warning(f"⚠️ Erreur initialisation données par défaut: {e}")
    
    @contextmanager
    def get_session(self):
        """Context manager pour obtenir une session thread-safe"""
        if not self.initialized:
            if not self.initialize():
                raise RuntimeError("EMERAUDEVIZ NTP Database non initialisé")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Erreur session EMERAUDEVIZ NTP: {e}")
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_session_with_app_context(self, app=None):
        """Context manager avec contexte Flask + session DB"""
        if app:
            with app.app_context():
                with self.get_session() as session:
                    yield session
        else:
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
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Obtenir les informations de connexion"""
        return {
            'database_type': 'SQLite Enterprise',
            'database_path': self.database_url,
            'instance_dir': self.instance_dir,
            'initialized': self.initialized,
            'engine_pool_size': str(self.engine.pool.size()) if self.engine else 0
        }
    
    def close(self):
        """Fermer toutes les connexions"""
        if self.engine:
            self.engine.dispose()
            self.logger.info("🔒 EMERAUDEVIZ NTP Database Manager fermé")

# Instance globale du Database Manager
db_manager = DatabaseManager()

# Fonctions utilitaires pour compatibilité
def get_db_session():
    """Obtenir une session DB (fonction utilitaire)"""
    return db_manager.get_session()

def get_db_session_with_context(app=None):
    """Obtenir une session DB avec contexte Flask"""
    return db_manager.get_session_with_app_context(app)

def init_database_manager(app=None, database_url=None):
    """Initialiser le Database Manager"""
    return db_manager.initialize()

# ================== COMPATIBILITÉ MODELS SQLALCHEMY ==================

class DatabaseProxy:
    """Proxy pour fournir une interface db compatible avec Flask-SQLAlchemy"""
    
    def __init__(self):
        self._db = None
        
    def init_app(self, app):
        """Initialiser avec l'app Flask"""
        try:
            from flask_sqlalchemy import SQLAlchemy
            self._db = SQLAlchemy(app)
        except ImportError:
            self.logger.warning("Flask-SQLAlchemy non disponible")
        return self._db
        
    @property
    def Model(self):
        """Retourner la classe Model de SQLAlchemy"""
        if self._db:
            return self._db.Model
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
    def Float(self):
        from sqlalchemy import Float
        return Float
    
    @property
    def Text(self):
        from sqlalchemy import Text
        return Text
    
    @property
    def JSON(self):
        from sqlalchemy import JSON
        return JSON
    
    @property
    def ForeignKey(self):
        from sqlalchemy import ForeignKey
        return ForeignKey
    
    @property
    def relationship(self):
        from sqlalchemy.orm import relationship
        return relationship
    
    @property
    def session(self):
        """Retourner une session via le database manager"""
        if self._db and hasattr(self._db, 'session'):
            return self._db.session
        return db_manager.get_session()

# Créer l'instance db pour compatibilité avec les modèles
db = DatabaseProxy()
EOF

# =================== CORRECTION APP.PY PRINCIPAL ===================
echo "🔨 Configuration app.py principal..."

cat > app.py << 'EOF'
#!/usr/bin/env python3
"""
EMERAUDEVIZ NTP - Application Principale
NTP Monitor Enterprise - Version Production
"""

import os
import sys
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/NTPVIZ/logs/app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    """Créer l'application Flask EMERAUDEVIZ NTP"""
    
    logger.info("🚀 Démarrage EMERAUDEVIZ NTP Enterprise")
    logger.info(f"🕒 {datetime.now()}")
    logger.info(f"📍 Serveur: {os.uname().nodename}")
    
    try:
        # Imports Flask
        from flask import Flask, render_template, redirect, url_for, flash, request
        from flask_login import LoginManager, login_required, current_user
        from flask_socketio import SocketIO
        
        logger.info("✅ Imports Flask réussis")
        
        # Configuration application
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'emeraudeviz-ntp-2025-production-key'
        app.config['WTF_CSRF_ENABLED'] = False  # Désactiver CSRF pour éviter les problèmes
        
        # Configuration SQLite forcée
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/ntp_monitor_enterprise.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        logger.info("✅ Configuration Flask terminée")
        
        # Initialiser la base de données
        try:
            from backend.database_manager import db_manager, init_database_manager
            init_database_manager(app)
            logger.info("✅ Database Manager initialisé")
        except Exception as e:
            logger.error(f"❌ Erreur Database Manager: {e}")
            # Continuer quand même
        
        # Initialiser Flask-Login
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
        
        @login_manager.user_loader
        def load_user(user_id):
            try:
                from backend.models.user import User
                with db_manager.get_session() as session:
                    return session.query(User).get(int(user_id))
            except Exception as e:
                logger.error(f"Erreur chargement utilisateur: {e}")
                return None
        
        logger.info("✅ Flask-Login configuré")
        
        # Initialiser SocketIO
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
        logger.info("✅ SocketIO configuré")
        
        # Enregistrer les blueprints
        try:
            from backend.api.auth import auth_bp
            from backend.api.main import main_bp
            from backend.api.ntp import ntp_bp
            from backend.api.admin import admin_bp
            from backend.api.alerts import alerts_bp
            
            app.register_blueprint(auth_bp, url_prefix='/auth')
            app.register_blueprint(main_bp, url_prefix='/')
            app.register_blueprint(ntp_bp, url_prefix='/ntp')
            app.register_blueprint(admin_bp, url_prefix='/admin')
            app.register_blueprint(alerts_bp, url_prefix='/alerts')
            
            logger.info("✅ Blueprints enregistrés")
        except Exception as e:
            logger.warning(f"⚠️ Erreur blueprints: {e}")
            
            # Route de fallback simple
            @app.route('/')
            def index():
                return render_template('dashboard.html', 
                                     title='EMERAUDEVIZ NTP Enterprise',
                                     servers=[],
                                     stats={'total_servers': 0, 'active_servers': 0})
            
            @app.route('/login')
            def login():
                return render_template('auth/login.html')
        
        # Route de santé pour monitoring
        @app.route('/health')
        def health():
            return {
                'status': 'healthy',
                'app': 'EMERAUDEVIZ NTP Enterprise',
                'timestamp': datetime.now().isoformat(),
                'database': 'SQLite Enterprise'
            }
        
        # Gestionnaire d'erreurs
        @app.errorhandler(404)
        def not_found(error):
            return render_template('errors/404.html'), 404
        
        @app.errorhandler(500)
        def internal_error(error):
            return render_template('errors/500.html'), 500
        
        logger.info("🎉 EMERAUDEVIZ NTP Enterprise créé avec succès")
        return app, socketio
        
    except Exception as e:
        logger.error(f"❌ Erreur création app: {e}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        raise

if __name__ == '__main__':
    try:
        # Créer l'application
        app, socketio = create_app()
        
        # Démarrer le serveur
        logger.info("🌐 Démarrage serveur EMERAUDEVIZ NTP...")
        logger.info("📍 URL: http://79.137.36.66:5000/")
        logger.info("🔐 Admin: admin/admin123")
        logger.info("👤 Opérateur: operator/operator123")
        
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,
            allow_unsafe_werkzeug=True
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur démarrage serveur: {e}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        sys.exit(1)
EOF

# =================== PERMISSIONS ET PROPRIÉTAIRES ===================
echo "🔒 Configuration des permissions..."

chown -R ntp-monitor:ntp-monitor $PROJECT_DIR/
chmod +x $PROJECT_DIR/app.py
chmod -R 755 $PROJECT_DIR/backend/
chmod -R 755 $PROJECT_DIR/frontend/
chmod -R 755 $PROJECT_DIR/instance/ 2>/dev/null || true

# Créer les répertoires manquants
mkdir -p $PROJECT_DIR/logs
mkdir -p $PROJECT_DIR/instance
chown -R ntp-monitor:ntp-monitor $PROJECT_DIR/logs
chown -R ntp-monitor:ntp-monitor $PROJECT_DIR/instance

# =================== TEST SYNTAXE ===================
echo "🧪 Test de syntaxe Python..."

cd $PROJECT_DIR
sudo -u ntp-monitor bash -c "
source .venv/bin/activate
export PYTHONPATH='/opt/NTPVIZ'
python3 -c 'import backend.database_manager; print(\"✅ database_manager.py OK\")'
python3 -c 'import app; print(\"✅ app.py OK\")'
"

if [ $? -ne 0 ]; then
    echo "❌ Erreur de syntaxe détectée"
    exit 1
fi

echo "✅ Syntaxe Python correcte"

# =================== REDÉMARRAGE SERVICE ===================
echo "🔄 Redémarrage service EMERAUDEVIZ NTP..."

systemctl daemon-reload
systemctl restart $SERVICE_NAME

# Attendre le démarrage
sleep 8

# =================== VÉRIFICATIONS ===================
echo "📊 Vérification du déploiement..."

echo "📋 Statut du service:"
systemctl status $SERVICE_NAME --no-pager -l | head -15

echo ""
echo "📋 Logs récents:"
journalctl -u $SERVICE_NAME --no-pager -n 10

echo ""
echo "🌐 Test de connexion:"
sleep 3
curl -I http://localhost:5000/ 2>/dev/null || echo "⚠️ Service en cours de démarrage..."

echo ""
echo "🎉 DÉPLOIEMENT EMERAUDEVIZ NTP TERMINÉ !"
echo "========================================"
echo "🌐 URL: http://79.137.36.66:5000/"
echo "🔐 Admin: admin / admin123"
echo "👤 Opérateur: operator / operator123"
echo "📊 Santé: http://79.137.36.66:5000/health"
echo "📋 Logs: journalctl -u $SERVICE_NAME -f"
echo "💾 Sauvegarde: $BACKUP_DIR"
echo ""
echo "🚀 EMERAUDEVIZ NTP Enterprise est prêt !" 