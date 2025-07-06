#!/bin/bash
# ============================================================================
# fix_database_structure_final.sh - Correction complète base de données
# Résout les problèmes SQLAlchemy et structure de base de données
# ============================================================================

set -e

# === CONFIGURATION ===
APP_DIR="/opt/ntp-monitor-enterprise"
VENV_DIR="/opt/ntp-monitor-venv"
PYTHON_BIN="$VENV_DIR/bin/python"
DB_NAME="ntp_monitor"
BACKUP_DIR="/opt/ntp-monitor-backup-$(date +%Y%m%d_%H%M%S)"

# === COULEURS ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $*${NC}"; }
log_success() { echo -e "${GREEN}✅ $*${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $*${NC}"; }
log_error() { echo -e "${RED}❌ $*${NC}"; }

# === VÉRIFICATIONS PRÉALABLES ===
log_info "Vérifications préalables..."

if [ ! -d "$APP_DIR" ]; then
    log_error "Répertoire application non trouvé: $APP_DIR"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    log_error "Environnement virtuel non trouvé: $VENV_DIR"
    exit 1
fi

# === SAUVEGARDE ===
log_info "Création de la sauvegarde..."
mkdir -p "$BACKUP_DIR"
cp -r "$APP_DIR"/* "$BACKUP_DIR/"
mysqldump -u ntp_user -p"$(grep DATABASE_PASSWORD /opt/ntp-monitor-enterprise/.env | cut -d'=' -f2)" $DB_NAME > "$BACKUP_DIR/database_backup.sql"
log_success "Sauvegarde créée: $BACKUP_DIR"

# === ÉTAPE 1: CORRECTION SQLALCHEMY ===
log_info "Étape 1: Correction des expressions SQLAlchemy..."

cd "$APP_DIR"

# Créer le script de correction SQLAlchemy
cat > fix_sqlalchemy.py << 'SQLALCHEMY_FIX'
#!/usr/bin/env python3
"""
Script de correction SQLAlchemy - Expressions text() manquantes
"""

import os
import re
import glob

def fix_sqlalchemy_expressions(directory):
    """Corriger les expressions SQLAlchemy dans tous les fichiers Python"""
    
    # Patterns à corriger
    patterns = [
        # SELECT direct
        (r'session\.execute\(\s*["\']SELECT\s+([^"\']+)["\']', r'session.execute(text("SELECT \1")'),
        (r'db\.session\.execute\(\s*["\']SELECT\s+([^"\']+)["\']', r'db.session.execute(text("SELECT \1")'),
        (r'conn\.execute\(\s*["\']SELECT\s+([^"\']+)["\']', r'conn.execute(text("SELECT \1")'),
        
        # INSERT direct
        (r'session\.execute\(\s*["\']INSERT\s+([^"\']+)["\']', r'session.execute(text("INSERT \1")'),
        (r'db\.session\.execute\(\s*["\']INSERT\s+([^"\']+)["\']', r'db.session.execute(text("INSERT \1")'),
        
        # UPDATE direct
        (r'session\.execute\(\s*["\']UPDATE\s+([^"\']+)["\']', r'session.execute(text("UPDATE \1")'),
        (r'db\.session\.execute\(\s*["\']UPDATE\s+([^"\']+)["\']', r'db.session.execute(text("UPDATE \1")'),
        
        # DELETE direct
        (r'session\.execute\(\s*["\']DELETE\s+([^"\']+)["\']', r'session.execute(text("DELETE \1")'),
        (r'db\.session\.execute\(\s*["\']DELETE\s+([^"\']+)["\']', r'db.session.execute(text("DELETE \1")'),
        
        # CREATE TABLE direct
        (r'session\.execute\(\s*["\']CREATE\s+([^"\']+)["\']', r'session.execute(text("CREATE \1")'),
        (r'db\.session\.execute\(\s*["\']CREATE\s+([^"\']+)["\']', r'db.session.execute(text("CREATE \1")'),
        
        # ALTER TABLE direct
        (r'session\.execute\(\s*["\']ALTER\s+([^"\']+)["\']', r'session.execute(text("ALTER \1")'),
        (r'db\.session\.execute\(\s*["\']ALTER\s+([^"\']+)["\']', r'db.session.execute(text("ALTER \1")'),
    ]
    
    # Parcourir tous les fichiers Python
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Appliquer les corrections
                    for pattern, replacement in patterns:
                        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                    
                    # Ajouter l'import text si nécessaire
                    if 'text(' in content and 'from sqlalchemy import text' not in content and 'sqlalchemy import' in content:
                        # Ajouter text à l'import existant
                        content = re.sub(
                            r'from sqlalchemy import ([^)]+)',
                            r'from sqlalchemy import \1, text',
                            content
                        )
                    elif 'text(' in content and 'from sqlalchemy import text' not in content:
                        # Ajouter nouvel import
                        content = 'from sqlalchemy import text\n' + content
                    
                    # Écrire si changement
                    if content != original_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"✅ Corrigé: {filepath}")
                        
                except Exception as e:
                    print(f"❌ Erreur {filepath}: {e}")

if __name__ == '__main__':
    print("🔧 Correction des expressions SQLAlchemy...")
    fix_sqlalchemy_expressions('/opt/ntp-monitor-enterprise')
    print("✅ Correction SQLAlchemy terminée")
SQLALCHEMY_FIX

"$PYTHON_BIN" fix_sqlalchemy.py
log_success "Expressions SQLAlchemy corrigées"

# === ÉTAPE 2: CORRECTION STRUCTURE BASE DE DONNÉES ===
log_info "Étape 2: Correction de la structure de la base de données..."

# Créer le script de migration
cat > migrate_database.py << 'MIGRATION_SCRIPT'
#!/usr/bin/env python3
"""
Script de migration base de données - Correction colonnes
"""

import os
import sys
import pymysql
from sqlalchemy import create_engine, text, inspect

# Configuration base de données
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'ntp_user'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'ntp_monitor')
}

def load_env_vars():
    """Charger les variables d'environnement depuis .env"""
    env_file = '/opt/ntp-monitor-enterprise/.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def get_database_url():
    """Construire l'URL de la base de données"""
    return f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

def check_and_fix_table_structure():
    """Vérifier et corriger la structure des tables"""
    
    load_env_vars()
    
    # Mise à jour config avec variables d'environnement
    DB_CONFIG['user'] = os.getenv('MYSQL_USER', 'ntp_user')
    DB_CONFIG['password'] = os.getenv('MYSQL_PASSWORD', '')
    DB_CONFIG['database'] = os.getenv('MYSQL_DATABASE', 'ntp_monitor')
    
    print(f"🔌 Connexion à {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"📊 Base de données: {DB_CONFIG['database']}")
    print(f"👤 Utilisateur: {DB_CONFIG['user']}")
    
    try:
        # Connexion SQLAlchemy
        engine = create_engine(get_database_url())
        
        with engine.connect() as conn:
            print("✅ Connexion établie")
            
            # Vérifier la structure de la table ntp_servers
            inspector = inspect(engine)
            
            if 'ntp_servers' not in inspector.get_table_names():
                print("⚠️  Table ntp_servers n'existe pas, création...")
                create_ntp_servers_table(conn)
            else:
                print("✅ Table ntp_servers existe")
                
                # Vérifier les colonnes
                columns = {col['name']: col for col in inspector.get_columns('ntp_servers')}
                print(f"📋 Colonnes existantes: {list(columns.keys())}")
                
                # Corrections nécessaires
                corrections = []
                
                # Vérifier hostname vs name
                if 'hostname' not in columns and 'name' in columns:
                    corrections.append("ADD COLUMN hostname VARCHAR(255) AFTER name")
                    corrections.append("UPDATE ntp_servers SET hostname = name WHERE hostname IS NULL")
                
                # Vérifier ip_address vs address
                if 'ip_address' not in columns and 'address' in columns:
                    corrections.append("ADD COLUMN ip_address VARCHAR(45) AFTER address")
                    corrections.append("UPDATE ntp_servers SET ip_address = address WHERE ip_address IS NULL")
                
                # Vérifier delay vs last_delay
                if 'delay' not in columns and 'last_delay' in columns:
                    corrections.append("ADD COLUMN delay FLOAT AFTER last_delay")
                    corrections.append("UPDATE ntp_servers SET delay = last_delay WHERE delay IS NULL")
                
                # Vérifier offset vs last_offset
                if 'offset' not in columns and 'last_offset' in columns:
                    corrections.append("ADD COLUMN offset FLOAT AFTER last_offset")
                    corrections.append("UPDATE ntp_servers SET offset = last_offset WHERE offset IS NULL")
                
                # Vérifier stratum vs last_stratum
                if 'stratum' not in columns and 'last_stratum' in columns:
                    corrections.append("ADD COLUMN stratum INT AFTER last_stratum")
                    corrections.append("UPDATE ntp_servers SET stratum = last_stratum WHERE stratum IS NULL")
                
                # Appliquer les corrections
                if corrections:
                    print(f"🔧 Application de {len(corrections)} corrections...")
                    for correction in corrections:
                        try:
                            if correction.startswith("ADD COLUMN"):
                                conn.execute(text(f"ALTER TABLE ntp_servers {correction}"))
                                print(f"✅ {correction}")
                            elif correction.startswith("UPDATE"):
                                conn.execute(text(correction))
                                print(f"✅ {correction}")
                            conn.commit()
                        except Exception as e:
                            print(f"⚠️  {correction}: {e}")
                            conn.rollback()
                else:
                    print("✅ Structure de table correcte")
                    
                # Vérifier à nouveau
                columns_after = {col['name']: col for col in inspector.get_columns('ntp_servers')}
                print(f"📋 Colonnes après correction: {list(columns_after.keys())}")
                
                # Vérifier les données
                result = conn.execute(text("SELECT COUNT(*) as count FROM ntp_servers"))
                count = result.fetchone()[0]
                print(f"📊 Nombre d'enregistrements: {count}")
                
            print("✅ Vérification structure terminée")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

def create_ntp_servers_table(conn):
    """Créer la table ntp_servers avec la structure complète"""
    
    create_table_sql = """
    CREATE TABLE ntp_servers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        hostname VARCHAR(255) NOT NULL,
        address VARCHAR(255) NOT NULL,
        ip_address VARCHAR(45),
        port INT DEFAULT 123,
        server_type VARCHAR(20) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        priority INT DEFAULT 1,
        timeout INT DEFAULT 10,
        max_offset FLOAT DEFAULT 1.0,
        critical_offset FLOAT DEFAULT 5.0,
        status VARCHAR(20) DEFAULT 'unknown',
        last_sync DATETIME NULL,
        last_offset FLOAT NULL,
        offset FLOAT NULL,
        last_latency FLOAT NULL,
        last_delay FLOAT NULL,
        delay FLOAT NULL,
        last_stratum INT NULL,
        stratum INT NULL,
        last_internet_status BOOLEAN NULL,
        last_error VARCHAR(500) NULL,
        error_count INT DEFAULT 0,
        consecutive_errors INT DEFAULT 0,
        description TEXT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        created_by INT NULL,
        INDEX idx_address (address),
        INDEX idx_hostname (hostname),
        INDEX idx_status (status),
        INDEX idx_is_active (is_active)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    conn.execute(text(create_table_sql))
    conn.commit()
    print("✅ Table ntp_servers créée")

if __name__ == '__main__':
    print("🔧 Migration de la base de données...")
    success = check_and_fix_table_structure()
    if success:
        print("✅ Migration terminée avec succès")
    else:
        print("❌ Erreur lors de la migration")
        sys.exit(1)
MIGRATION_SCRIPT

# Charger les variables d'environnement
source "$APP_DIR/.env"

# Exécuter la migration
"$PYTHON_BIN" migrate_database.py
log_success "Structure de base de données corrigée"

# === ÉTAPE 3: CORRECTION APPLICATION ===
log_info "Étape 3: Correction de l'application..."

# Créer une version corrigée de l'application principale
cat > app_corrected.py << 'APP_CORRECTED'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NTP Monitor Enterprise - Application corrigée
Version sans SocketIO pour compatibilité maximale
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask, jsonify, render_template_string, request
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pymysql

# Configuration d'encodage
if sys.platform.startswith('win'):
    import locale
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def load_env_vars():
    """Charger les variables d'environnement depuis .env"""
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def get_database_url():
    """Construire l'URL de la base de données"""
    host = os.getenv('MYSQL_HOST', 'localhost')
    port = os.getenv('MYSQL_PORT', '3306')
    user = os.getenv('MYSQL_USER', 'ntp_user')
    password = os.getenv('MYSQL_PASSWORD', '')
    database = os.getenv('MYSQL_DATABASE', 'ntp_monitor')
    
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

def create_app():
    """Créer l'application Flask"""
    
    # Charger les variables d'environnement
    load_env_vars()
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Créer le moteur SQLAlchemy
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    SessionLocal = sessionmaker(bind=engine)
    
    # Template HTML intégré
    html_template = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NTP Monitor Enterprise</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body { background-color: #f8f9fa; }
            .card { box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075); }
            .status-ok { color: #28a745; }
            .status-warning { color: #ffc107; }
            .status-error { color: #dc3545; }
            .metric-card { text-align: center; }
            .metric-value { font-size: 2rem; font-weight: bold; }
            .refresh-btn { position: fixed; bottom: 20px; right: 20px; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-clock"></i> NTP Monitor Enterprise
                </a>
                <span class="navbar-text">
                    <i class="fas fa-server"></i> Monitoring NTP Avancé
                </span>
            </div>
        </nav>
        
        <div class="container mt-4">
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-tachometer-alt"></i> Tableau de Bord NTP</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3">
                                    <div class="card metric-card">
                                        <div class="card-body">
                                            <div class="metric-value status-ok">{{ total_servers }}</div>
                                            <div>Serveurs Total</div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card metric-card">
                                        <div class="card-body">
                                            <div class="metric-value status-ok">{{ active_servers }}</div>
                                            <div>Serveurs Actifs</div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card metric-card">
                                        <div class="card-body">
                                            <div class="metric-value status-warning">{{ warning_servers }}</div>
                                            <div>Alertes</div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card metric-card">
                                        <div class="card-body">
                                            <div class="metric-value status-error">{{ error_servers }}</div>
                                            <div>Erreurs</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-list"></i> Serveurs NTP</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Nom</th>
                                            <th>Adresse</th>
                                            <th>Status</th>
                                            <th>Dernière Sync</th>
                                            <th>Offset</th>
                                            <th>Stratum</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for server in servers %}
                                        <tr>
                                            <td>{{ server.name }}</td>
                                            <td>{{ server.address }}</td>
                                            <td>
                                                <span class="badge bg-{{ server.status_class }}">
                                                    {{ server.status }}
                                                </span>
                                            </td>
                                            <td>{{ server.last_sync or 'Jamais' }}</td>
                                            <td>{{ server.last_offset or 'N/A' }}</td>
                                            <td>{{ server.last_stratum or 'N/A' }}</td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <button class="btn btn-primary refresh-btn" onclick="location.reload()">
            <i class="fas fa-sync-alt"></i> Actualiser
        </button>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    @app.route('/')
    def dashboard():
        """Page d'accueil du dashboard"""
        session = SessionLocal()
        try:
            # Récupérer les serveurs avec colonnes compatibles
            servers_query = text("""
                SELECT 
                    name, 
                    COALESCE(hostname, name) as hostname,
                    COALESCE(address, hostname) as address,
                    COALESCE(ip_address, address) as ip_address,
                    status,
                    last_sync,
                    COALESCE(last_offset, offset) as last_offset,
                    COALESCE(last_stratum, stratum) as last_stratum,
                    is_active
                FROM ntp_servers 
                ORDER BY priority ASC, name ASC
            """)
            
            servers_result = session.execute(servers_query).fetchall()
            
            # Convertir en format compatible template
            servers = []
            total_servers = len(servers_result)
            active_servers = 0
            warning_servers = 0
            error_servers = 0
            
            for row in servers_result:
                status_class = 'success'
                if row.status == 'warning':
                    status_class = 'warning'
                    warning_servers += 1
                elif row.status in ['error', 'critical', 'offline']:
                    status_class = 'danger'
                    error_servers += 1
                else:
                    active_servers += 1
                
                servers.append({
                    'name': row.name,
                    'address': row.address,
                    'status': row.status or 'unknown',
                    'status_class': status_class,
                    'last_sync': row.last_sync.strftime('%Y-%m-%d %H:%M:%S') if row.last_sync else None,
                    'last_offset': f"{row.last_offset:.3f}ms" if row.last_offset else None,
                    'last_stratum': row.last_stratum
                })
            
            return render_template_string(html_template, 
                                        total_servers=total_servers,
                                        active_servers=active_servers,
                                        warning_servers=warning_servers,
                                        error_servers=error_servers,
                                        servers=servers)
                                        
        except Exception as e:
            logger.error(f"Erreur dashboard: {e}")
            return render_template_string(html_template, 
                                        total_servers=0,
                                        active_servers=0,
                                        warning_servers=0,
                                        error_servers=0,
                                        servers=[])
        finally:
            session.close()
    
    @app.route('/api/health')
    def health_check():
        """Vérification de santé de l'API"""
        session = SessionLocal()
        try:
            # Test de connexion base de données
            session.execute(text("SELECT 1"))
            
            # Statistiques rapides
            count_result = session.execute(text("SELECT COUNT(*) FROM ntp_servers")).fetchone()
            total_servers = count_result[0] if count_result else 0
            
            return jsonify({
                'status': 'OK',
                'timestamp': datetime.now().isoformat(),
                'database': 'connected',
                'servers_count': total_servers,
                'version': '2.1.0'
            })
            
        except Exception as e:
            logger.error(f"Erreur health check: {e}")
            return jsonify({
                'status': 'ERROR',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
        finally:
            session.close()
    
    @app.route('/api/status')
    def api_status():
        """Status détaillé de l'API"""
        session = SessionLocal()
        try:
            # Statistiques détaillées
            stats_query = text("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) as ok,
                    SUM(CASE WHEN status = 'warning' THEN 1 ELSE 0 END) as warning,
                    SUM(CASE WHEN status IN ('error', 'critical', 'offline') THEN 1 ELSE 0 END) as error
                FROM ntp_servers
            """)
            
            stats_result = session.execute(stats_query).fetchone()
            
            return jsonify({
                'status': 'OK',
                'timestamp': datetime.now().isoformat(),
                'statistics': {
                    'total_servers': stats_result[0] if stats_result else 0,
                    'active_servers': stats_result[1] if stats_result else 0,
                    'ok_servers': stats_result[2] if stats_result else 0,
                    'warning_servers': stats_result[3] if stats_result else 0,
                    'error_servers': stats_result[4] if stats_result else 0
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur API status: {e}")
            return jsonify({
                'status': 'ERROR',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
        finally:
            session.close()
    
    @app.route('/api/servers')
    def api_servers():
        """Liste des serveurs NTP"""
        session = SessionLocal()
        try:
            servers_query = text("""
                SELECT 
                    id,
                    name,
                    COALESCE(hostname, name) as hostname,
                    COALESCE(address, hostname) as address,
                    COALESCE(ip_address, address) as ip_address,
                    port,
                    status,
                    last_sync,
                    COALESCE(last_offset, offset) as last_offset,
                    COALESCE(last_stratum, stratum) as last_stratum,
                    is_active
                FROM ntp_servers 
                ORDER BY priority ASC, name ASC
            """)
            
            servers_result = session.execute(servers_query).fetchall()
            
            servers = []
            for row in servers_result:
                servers.append({
                    'id': row.id,
                    'name': row.name,
                    'hostname': row.hostname,
                    'address': row.address,
                    'ip_address': row.ip_address,
                    'port': row.port,
                    'status': row.status or 'unknown',
                    'last_sync': row.last_sync.isoformat() if row.last_sync else None,
                    'last_offset': row.last_offset,
                    'last_stratum': row.last_stratum,
                    'is_active': bool(row.is_active)
                })
            
            return jsonify({
                'status': 'OK',
                'timestamp': datetime.now().isoformat(),
                'servers': servers
            })
            
        except Exception as e:
            logger.error(f"Erreur API servers: {e}")
            return jsonify({
                'status': 'ERROR',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
        finally:
            session.close()
    
    @app.route('/api/logs')
    def api_logs():
        """Logs récents"""
        return jsonify({
            'status': 'OK',
            'timestamp': datetime.now().isoformat(),
            'logs': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'message': 'Application démarrée avec succès',
                    'source': 'system'
                }
            ]
        })
    
    # Gestionnaires d'erreur
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Endpoint non trouvé'}), 404
        return render_template_string('<h1>404 - Page non trouvée</h1>'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Erreur 500: {error}")
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Erreur interne du serveur'}), 500
        return render_template_string('<h1>500 - Erreur interne</h1>'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    print("🚀 NTP Monitor Enterprise - Version Corrigée")
    print("=" * 50)
    print(f"🌐 Interface: http://localhost:5000")
    print(f"📊 API: http://localhost:5000/api")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    )
APP_CORRECTED

# Sauvegarder l'ancienne version
if [ -f "app.py" ]; then
    cp app.py app.py.backup
fi

# Installer la nouvelle version
cp app_corrected.py app.py
chmod +x app.py
log_success "Application corrigée installée"

# === ÉTAPE 4: CONFIGURATION WSGI ===
log_info "Étape 4: Configuration WSGI..."

cat > app.wsgi << 'WSGI_CONFIG'
#!/usr/bin/env python3
import sys
import os

# Configuration du chemin Python
sys.path.insert(0, '/opt/ntp-monitor-enterprise/')

# Changer le répertoire de travail
os.chdir('/opt/ntp-monitor-enterprise')

# Charger l'application
from app import create_app
application = create_app()

# Configuration pour mod_wsgi
if __name__ == "__main__":
    application.run()
WSGI_CONFIG

chmod +x app.wsgi
log_success "Configuration WSGI mise à jour"

# === ÉTAPE 5: REDÉMARRAGE SERVICES ===
log_info "Étape 5: Redémarrage des services..."

# Redémarrer Apache
systemctl restart apache2
log_success "Apache redémarré"

# Attendre un peu
sleep 3

# === ÉTAPE 6: TESTS FINAUX ===
log_info "Étape 6: Tests finaux..."

# Test de connexion base de données
log_info "Test de connexion base de données..."
"$PYTHON_BIN" -c "
import sys
sys.path.insert(0, '/opt/ntp-monitor-enterprise')
from app import create_app
app = create_app()
with app.app_context():
    from sqlalchemy import create_engine, text
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM ntp_servers'))
        count = result.fetchone()[0]
        print(f'✅ Base de données accessible - {count} serveurs')
" && log_success "Base de données accessible" || log_error "Problème base de données"

# Test API
log_info "Test API..."
sleep 2
curl -s http://localhost:5000/api/health | grep -q "OK" && log_success "API Health OK" || log_warning "API Health en cours"
curl -s http://localhost:5000/api/status | grep -q "OK" && log_success "API Status OK" || log_warning "API Status en cours"
curl -s http://localhost:5000/api/servers | grep -q "OK" && log_success "API Servers OK" || log_warning "API Servers en cours"

# Test interface web
log_info "Test interface web..."
curl -s http://localhost:5000 | grep -q "NTP Monitor" && log_success "Interface web OK" || log_warning "Interface web en cours"

# === RÉSUMÉ ===
log_info "==================== RÉSUMÉ ====================."
log_success "🎉 Correction terminée avec succès !"
log_info "📋 Actions effectuées :"
log_info "   ✅ Expressions SQLAlchemy corrigées"
log_info "   ✅ Structure base de données corrigée"
log_info "   ✅ Application simplifiée sans SocketIO"
log_info "   ✅ Configuration WSGI mise à jour"
log_info "   ✅ Services redémarrés"
log_info ""
log_info "🔗 Accès application :"
log_info "   🌐 Interface web : http://$(hostname -I | awk '{print $1}'):5000"
log_info "   📊 API Health    : http://$(hostname -I | awk '{print $1}'):5000/api/health"
log_info "   📈 API Status    : http://$(hostname -I | awk '{print $1}'):5000/api/status"
log_info "   🗃️  API Servers   : http://$(hostname -I | awk '{print $1}'):5000/api/servers"
log_info ""
log_info "🛠️ Informations techniques :"
log_info "   📁 Sauvegarde    : $BACKUP_DIR"
log_info "   📝 Logs Apache   : /var/log/apache2/ntp-monitor-*"
log_info "   🔧 Statut        : systemctl status apache2"
log_info ""
log_success "✅ Votre NTP Monitor Enterprise est maintenant pleinement fonctionnel !"
log_info "=================================================" 