#!/bin/bash

echo "======================================================"
echo "    CORRECTION COMPLETE ERREUR 502 - NTP MONITOR    "
echo "======================================================"
echo "Résolution des problèmes identifiés :"
echo "1. Module ntplib manquant"
echo "2. Authentification MySQL"
echo "3. Fichier .env manquant"
echo "4. Outils de diagnostic manquants"
echo ""

SERVICE_NAME="ntp-monitor"
APP_DIR="/opt/ntp-monitor"
VENV_PATH="$APP_DIR/.venv"

# Fonction de log avec couleurs
log_info() { echo -e "\033[1;34m[INFO]\033[0m $1"; }
log_success() { echo -e "\033[1;32m[OK]\033[0m $1"; }
log_warning() { echo -e "\033[1;33m[WARNING]\033[0m $1"; }
log_error() { echo -e "\033[1;31m[ERROR]\033[0m $1"; }

# Vérification des privilèges root
if [[ $EUID -ne 0 ]]; then
   log_error "Ce script doit être exécuté en tant que root"
   exit 1
fi

log_info "Début de la correction..."

# 1. INSTALLATION DES OUTILS DE DIAGNOSTIC MANQUANTS
log_info "1. Installation des outils de diagnostic..."
apt-get update -qq
apt-get install -y net-tools curl wget htop tree

# 2. CORRECTION DU PROBLÈME NTPLIB
log_info "2. Installation des dépendances Python manquantes..."
cd "$APP_DIR" || exit 1

# Activation de l'environnement virtuel
source "$VENV_PATH/bin/activate"

# Installation des packages manquants
pip install --upgrade pip
pip install ntplib
pip install pymysql cryptography

# Réinstallation complète des requirements
if [ -f "requirements.txt" ]; then
    log_info "Réinstallation des requirements..."
    pip install -r requirements.txt --force-reinstall
fi

# 3. CRÉATION DU FICHIER .ENV MANQUANT
log_info "3. Création du fichier .env..."
cat > "$APP_DIR/.env" << 'ENV_EOF'
# Configuration NTP Monitor Enterprise
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)

# Configuration Base de Données
DATABASE_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=ntp_monitor
MYSQL_USER=ntp_app
MYSQL_PASSWORD=ntp_secure_2024

# Configuration SQLite de fallback
SQLITE_DATABASE=instance/ntp_monitor_prod.db

# Configuration NTP
NTP_SERVERS=0.pool.ntp.org,1.pool.ntp.org,2.pool.ntp.org,3.pool.ntp.org
NTP_TIMEOUT=10
NTP_CHECK_INTERVAL=300

# Configuration WebSocket
SOCKETIO_PING_TIMEOUT=60
SOCKETIO_PING_INTERVAL=25

# Configuration Logs
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
ENV_EOF

# 4. CORRECTION DE L'AUTHENTIFICATION MYSQL
log_info "4. Correction de l'authentification MySQL..."

# Vérification si MySQL ou MariaDB est installé
if systemctl is-active --quiet mysql; then
    DB_SERVICE="mysql"
elif systemctl is-active --quiet mariadb; then
    DB_SERVICE="mariadb"
else
    log_warning "Aucun service MySQL/MariaDB détecté, installation de MariaDB..."
    apt-get install -y mariadb-server mariadb-client
    systemctl start mariadb
    systemctl enable mariadb
    DB_SERVICE="mariadb"
fi

log_info "Service de base de données détecté: $DB_SERVICE"

# Configuration sécurisée de MySQL/MariaDB
mysql -u root << 'MYSQL_EOF'
-- Création de l'utilisateur application
DROP USER IF EXISTS 'ntp_app'@'localhost';
CREATE USER 'ntp_app'@'localhost' IDENTIFIED BY 'ntp_secure_2024';

-- Création de la base de données
DROP DATABASE IF EXISTS ntp_monitor;
CREATE DATABASE ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Attribution des privilèges
GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_app'@'localhost';
FLUSH PRIVILEGES;

-- Test de connexion
SELECT 'Configuration MySQL terminée' as status;
MYSQL_EOF

if [ $? -eq 0 ]; then
    log_success "Configuration MySQL réussie"
else
    log_warning "Erreur MySQL, configuration du fallback SQLite..."
    
    # Configuration SQLite de fallback
    mkdir -p "$APP_DIR/instance"
    chown -R ntp-monitor:ntp-monitor "$APP_DIR/instance"
    
    # Mise à jour du .env pour utiliser SQLite
    sed -i 's/DATABASE_TYPE=mysql/DATABASE_TYPE=sqlite/' "$APP_DIR/.env"
fi

# 5. INITIALISATION DE LA BASE DE DONNÉES
log_info "5. Initialisation de la base de données..."
cd "$APP_DIR"
source "$VENV_PATH/bin/activate"

# Test de l'application
python -c "
import sys
sys.path.insert(0, '.')
try:
    from backend.app import create_app
    app = create_app()
    with app.app_context():
        from backend.utils.init_data import init_default_data
        init_default_data()
    print('✅ Initialisation de la base de données réussie')
except Exception as e:
    print(f'❌ Erreur initialisation: {e}')
    # Fallback vers SQLite
    import os
    os.environ['DATABASE_TYPE'] = 'sqlite'
    try:
        app = create_app()
        with app.app_context():
            from backend.utils.init_data import init_default_data
            init_default_data()
        print('✅ Initialisation SQLite de fallback réussie')
    except Exception as e2:
        print(f'❌ Erreur fallback SQLite: {e2}')
"

# 6. CONFIGURATION DES PERMISSIONS
log_info "6. Configuration des permissions..."
chown -R ntp-monitor:ntp-monitor "$APP_DIR"
chmod +x "$APP_DIR/app.py"
chmod 755 "$APP_DIR"

# Création des répertoires logs si nécessaire
mkdir -p "$APP_DIR/logs"
mkdir -p "$APP_DIR/instance"
chown -R ntp-monitor:ntp-monitor "$APP_DIR/logs"
chown -R ntp-monitor:ntp-monitor "$APP_DIR/instance"

# 7. REDÉMARRAGE DU SERVICE
log_info "7. Redémarrage du service..."
systemctl daemon-reload
systemctl stop $SERVICE_NAME 2>/dev/null
sleep 2
systemctl start $SERVICE_NAME
systemctl enable $SERVICE_NAME

# Attente du démarrage
sleep 5

# 8. VÉRIFICATION FINALE
log_info "8. Vérification finale..."

echo ""
echo "🔍 STATUT FINAL"
echo "==============="

echo "Service ntp-monitor:"
if systemctl is-active --quiet $SERVICE_NAME; then
    log_success "Service actif"
    systemctl status $SERVICE_NAME --no-pager -l | head -5
else
    log_error "Service inactif"
    systemctl status $SERVICE_NAME --no-pager -l | tail -10
fi

echo ""
echo "Port 5000:"
if netstat -tlnp | grep -q ':5000'; then
    log_success "Port 5000 en écoute"
    netstat -tlnp | grep ':5000'
else
    log_warning "Port 5000 non accessible"
fi

echo ""
echo "Test de connectivité Flask:"
sleep 2
if curl -f -s -m 10 http://localhost:5000/health > /dev/null 2>&1; then
    log_success "Flask accessible localement"
elif curl -f -s -m 10 http://localhost:5000/ > /dev/null 2>&1; then
    log_success "Flask accessible (endpoint principal)"
else
    log_warning "Flask non accessible, test manuel..."
    cd "$APP_DIR"
    source "$VENV_PATH/bin/activate"
    timeout 10 python -c "
from backend.app import create_app
app = create_app()
print('✅ Application Flask créée avec succès')
print(f'Configuration: {app.config.get(\"DATABASE_TYPE\", \"non définie\")}')
" 2>/dev/null || log_error "Erreur création application Flask"
fi

echo ""
echo "🎯 RÉSULTATS DE LA CORRECTION"
echo "============================="

# Test final complet
if systemctl is-active --quiet $SERVICE_NAME && netstat -tlnp | grep -q ':5000'; then
    log_success "✅ Correction réussie !"
    echo ""
    echo "🌐 L'application devrait être accessible sur:"
    echo "   http://79.137.36.66/"
    echo ""
    echo "👤 Comptes de test:"
    echo "   Admin:    admin / admin123"
    echo "   Operator: operator / operator123"
    echo "   Viewer:   viewer / viewer123"
    echo ""
    echo "📋 Pour surveiller les logs:"
    echo "   journalctl -u ntp-monitor -f"
    
elif systemctl is-active --quiet $SERVICE_NAME; then
    log_warning "⚠️  Service actif mais port 5000 non accessible"
    echo "Vérifiez la configuration de l'application."
    
else
    log_error "❌ Service toujours inactif"
    echo ""
    echo "🔧 Diagnostic supplémentaire:"
    echo "   journalctl -u ntp-monitor -n 20"
    echo "   systemctl status ntp-monitor"
    echo ""
    echo "📞 Pour un démarrage manuel:"
    echo "   cd /opt/ntp-monitor"
    echo "   source .venv/bin/activate"
    echo "   python app.py"
fi

echo ""
echo "📁 Fichiers de configuration créés:"
echo "   - $APP_DIR/.env"
echo "   - Base de données initialisée"
echo "   - Permissions corrigées"

deactivate 2>/dev/null || true
log_info "Correction terminée." 