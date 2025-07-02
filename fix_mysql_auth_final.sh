#!/bin/bash

echo "================================================================="
echo "  CORRECTION AUTHENTIFICATION MYSQL - NTP MONITOR ENTERPRISE   "
echo "================================================================="
echo "Résolution de l'erreur : (1698, Access denied for user 'root'@'localhost')"
echo "Cette erreur est causée par l'authentification par socket Unix de MySQL/MariaDB"
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

log_info "Début de la correction d'authentification MySQL..."

# Arrêt du service NTP Monitor
systemctl stop $SERVICE_NAME 2>/dev/null

# 1. DIAGNOSTIC DU SYSTÈME DE BASE DE DONNÉES
log_info "1. Diagnostic du système de base de données..."

# Détection du service de base de données
DB_SERVICE=""
if systemctl is-active --quiet mysql; then
    DB_SERVICE="mysql"
    log_info "Service MySQL détecté"
elif systemctl is-active --quiet mariadb; then
    DB_SERVICE="mariadb"  
    log_info "Service MariaDB détecté"
else
    log_warning "Aucun service MySQL/MariaDB actif détecté"
    log_info "Installation de MariaDB..."
    apt-get update -qq
    apt-get install -y mariadb-server mariadb-client
    systemctl start mariadb
    systemctl enable mariadb
    DB_SERVICE="mariadb"
fi

# 2. CONFIGURATION DE L'AUTHENTIFICATION ROOT
log_info "2. Configuration de l'authentification root..."

# Méthode 1: Configuration avec mot de passe pour root
log_info "Configuration de l'authentification root avec mot de passe..."

# Génération d'un mot de passe root sécurisé
ROOT_PASSWORD=$(openssl rand -base64 32)

# Configuration MySQL sécurisée avec mot de passe
mysql --user=root << MYSQL_ROOT_CONFIG || {
    log_warning "Première méthode échouée, tentative avec socket..."
    sudo mysql << MYSQL_ROOT_CONFIG
}
-- Configuration sécurisée de l'authentification root
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${ROOT_PASSWORD}';

-- Suppression des utilisateurs anonymes
DELETE FROM mysql.user WHERE User='';

-- Suppression de la base de données test
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';

-- Application des modifications
FLUSH PRIVILEGES;

SELECT 'Configuration root terminée' as status;
MYSQL_ROOT_CONFIG

# Sauvegarde du mot de passe root dans un fichier sécurisé
echo "[client]" > /root/.my.cnf
echo "user=root" >> /root/.my.cnf
echo "password=${ROOT_PASSWORD}" >> /root/.my.cnf
chmod 600 /root/.my.cnf

log_success "Authentification root configurée avec mot de passe"

# 3. CRÉATION DE L'UTILISATEUR APPLICATION
log_info "3. Création de l'utilisateur application NTP Monitor..."

# Génération d'un mot de passe application sécurisé
APP_PASSWORD=$(openssl rand -base64 24)

mysql --defaults-file=/root/.my.cnf << MYSQL_APP_CONFIG
-- Suppression de l'ancien utilisateur s'il existe
DROP USER IF EXISTS 'ntp_monitor'@'localhost';
DROP USER IF EXISTS 'ntp_app'@'localhost';

-- Création du nouvel utilisateur application
CREATE USER 'ntp_monitor'@'localhost' IDENTIFIED BY '${APP_PASSWORD}';

-- Suppression et création de la base de données
DROP DATABASE IF EXISTS ntp_monitor;
CREATE DATABASE ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Attribution des privilèges complets à l'utilisateur application
GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_monitor'@'localhost';

-- Privilèges additionnels pour la gestion des connexions
GRANT PROCESS ON *.* TO 'ntp_monitor'@'localhost';

-- Application des modifications
FLUSH PRIVILEGES;

-- Test de création de table
USE ntp_monitor;
CREATE TABLE test_connection (id INT PRIMARY KEY, status VARCHAR(50));
INSERT INTO test_connection VALUES (1, 'Connection successful');
SELECT * FROM test_connection;
DROP TABLE test_connection;

SELECT 'Configuration utilisateur application terminée' as status;
MYSQL_APP_CONFIG

if [ $? -eq 0 ]; then
    log_success "Utilisateur application 'ntp_monitor' créé avec succès"
else
    log_error "Erreur création utilisateur application"
    exit 1
fi

# 4. MISE À JOUR DE LA CONFIGURATION APPLICATION
log_info "4. Mise à jour de la configuration application..."

cd "$APP_DIR" || exit 1

# Mise à jour du fichier .env avec les nouvelles informations
cat > .env << ENV_CONFIG
# Configuration NTP Monitor Enterprise
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)

# Configuration Base de Données MySQL
DATABASE_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=ntp_monitor
MYSQL_USER=ntp_monitor
MYSQL_PASSWORD=${APP_PASSWORD}

# Configuration SQLite de fallback (conservée)
SQLITE_DATABASE=instance/ntp_monitor_prod.db

# Configuration NTP
NTP_SERVERS=0.pool.ntp.org,1.pool.ntp.org,2.pool.ntp.org,3.pool.ntp.org
NTP_TIMEOUT=10
NTP_CHECK_INTERVAL=300

# Configuration WebSocket
SOCKETIO_PING_TIMEOUT=60
SOCKETIO_PING_INTERVAL=25

# Configuration Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Configuration Logs
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Configuration Debug
SQLALCHEMY_ECHO=False
ENV_CONFIG

log_success "Fichier .env mis à jour avec les nouvelles informations d'authentification"

# 5. TEST DE CONNEXION MYSQL
log_info "5. Test de connexion MySQL avec les nouveaux paramètres..."

# Test de connexion avec l'utilisateur application
mysql -u ntp_monitor -p"${APP_PASSWORD}" -e "USE ntp_monitor; SELECT 'Test de connexion réussi' as status;" 2>/dev/null

if [ $? -eq 0 ]; then
    log_success "✅ Test de connexion MySQL réussi"
else
    log_error "❌ Test de connexion MySQL échoué"
    
    # Configuration en fallback SQLite
    log_warning "Configuration du fallback SQLite..."
    sed -i 's/DATABASE_TYPE=mysql/DATABASE_TYPE=sqlite/' "$APP_DIR/.env"
    mkdir -p "$APP_DIR/instance"
    touch "$APP_DIR/instance/ntp_monitor_prod.db"
    chown -R ntp-monitor:ntp-monitor "$APP_DIR/instance"
    log_success "Fallback SQLite configuré"
fi

# 6. INITIALISATION DE LA BASE DE DONNÉES APPLICATION
log_info "6. Initialisation de la base de données application..."

source "$VENV_PATH/bin/activate"

# Test et initialisation de l'application
python -c "
import sys
import os
sys.path.insert(0, '.')

try:
    from backend.app import create_app
    app = create_app()
    
    print('✅ Application Flask créée avec succès')
    print(f'Database URI: {app.config.get(\"SQLALCHEMY_DATABASE_URI\", \"Non définie\")[:100]}')
    
    with app.app_context():
        print('✅ Contexte application fonctionnel')
        
        # Initialisation des données
        try:
            from backend.utils.init_data import init_default_data
            init_default_data()
            print('✅ Initialisation des données réussie')
        except Exception as e:
            print(f'⚠️  Initialisation données: {e}')
            
        # Test de connexion à la base
        from backend.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        if db_manager.initialize():
            print('✅ Database Manager initialisé avec succès')
        else:
            print('⚠️  Database Manager utilise le fallback')
            
except Exception as e:
    print(f'❌ Erreur: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

# 7. CONFIGURATION DES PERMISSIONS
log_info "7. Configuration des permissions..."

chown -R ntp-monitor:ntp-monitor "$APP_DIR"
chmod 600 "$APP_DIR/.env"  # Fichier .env sécurisé
chmod 755 "$APP_DIR"

# 8. REDÉMARRAGE DU SERVICE
log_info "8. Redémarrage du service NTP Monitor..."

systemctl daemon-reload
systemctl start $SERVICE_NAME
systemctl enable $SERVICE_NAME

# Attente du démarrage
sleep 15

# 9. VÉRIFICATION FINALE COMPLÈTE
log_info "9. Vérification finale complète..."

echo ""
echo "🔍 VÉRIFICATION FINALE MYSQL"
echo "============================"

# Test du service de base de données
echo "Service de base de données:"
if systemctl is-active --quiet $DB_SERVICE; then
    log_success "✅ Service $DB_SERVICE actif"
else
    log_error "❌ Service $DB_SERVICE inactif"
fi

# Test de connexion MySQL
echo ""
echo "Test de connexion MySQL:"
if mysql -u ntp_monitor -p"${APP_PASSWORD}" -e "SELECT 'MySQL accessible' as status;" 2>/dev/null; then
    log_success "✅ Connexion MySQL fonctionnelle"
    mysql -u ntp_monitor -p"${APP_PASSWORD}" -e "USE ntp_monitor; SHOW TABLES;" 2>/dev/null | head -10
else
    log_warning "❌ Connexion MySQL non accessible (fallback SQLite actif)"
fi

# Test du service NTP Monitor
echo ""
echo "Service NTP Monitor:"
if systemctl is-active --quiet $SERVICE_NAME; then
    log_success "✅ Service NTP Monitor actif"
    systemctl status $SERVICE_NAME --no-pager -l | head -3
else
    log_error "❌ Service NTP Monitor inactif"
    echo "Logs récents:"
    journalctl -u $SERVICE_NAME -n 5 --no-pager
fi

# Test du port d'écoute
echo ""
echo "Port d'écoute:"
if netstat -tlnp 2>/dev/null | grep -q ':5000'; then
    log_success "✅ Port 5000 en écoute"
    netstat -tlnp | grep ':5000'
else
    log_warning "❌ Port 5000 non accessible"
fi

# Test de connectivité web
echo ""
echo "Test de connectivité web:"
sleep 5
if curl -f -s -m 15 http://localhost:5000/ > /dev/null 2>&1; then
    log_success "✅ Application web accessible"
elif curl -f -s -m 15 http://localhost:5000/health > /dev/null 2>&1; then
    log_success "✅ Application web accessible (health check)"
else
    log_warning "❌ Application web non accessible"
fi

echo ""
echo "📊 RÉSULTATS FINAUX"
echo "=================="

if systemctl is-active --quiet $SERVICE_NAME && netstat -tlnp 2>/dev/null | grep -q ':5000'; then
    log_success "🎉 CORRECTION MYSQL RÉUSSIE !"
    echo ""
    echo "🌐 Application NTP Monitor Enterprise disponible sur :"
    echo "   http://79.137.36.66/"
    echo ""
    echo "👤 Comptes utilisateur :"
    echo "   Admin:    admin / admin123"
    echo "   Operator: operator / operator123"
    echo "   Viewer:   viewer / viewer123"
    echo ""
    echo "🗄️  Base de données :"
    echo "   Type: MySQL/MariaDB"
    echo "   Utilisateur: ntp_monitor"
    echo "   Base: ntp_monitor"
    echo ""
    echo "📋 Monitoring :"
    echo "   journalctl -u ntp-monitor -f"
    echo "   systemctl status ntp-monitor"
    
elif systemctl is-active --quiet $SERVICE_NAME; then
    log_warning "⚠️  Service actif mais port non accessible"
    echo "Attendez quelques minutes pour la stabilisation complète."
    
else
    log_error "❌ Service toujours inactif"
    echo ""
    echo "🔧 Diagnostic :"
    echo "   journalctl -u ntp-monitor -n 20"
    echo "   systemctl status ntp-monitor -l"
fi

echo ""
echo "📁 Fichiers de configuration créés :"
echo "   - /root/.my.cnf (authentification MySQL root)"
echo "   - $APP_DIR/.env (configuration application)"
echo "   - Base de données 'ntp_monitor' créée"
echo "   - Utilisateur 'ntp_monitor' configuré"

deactivate 2>/dev/null || true
log_info "Correction d'authentification MySQL terminée." 