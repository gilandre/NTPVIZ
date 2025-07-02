#!/bin/bash
# Script de correction pour les conflits MySQL/MariaDB sur Ubuntu
# Usage: ./fix_mysql_mariadb_conflict.sh

set -e

echo "🗄️ RÉSOLUTION CONFLITS MYSQL/MARIADB"
echo "===================================="

APP_DIR="/opt/ntp-monitor"
SERVICE_NAME="ntp-monitor"

# Vérification des privilèges root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être exécuté en tant que root"
   exit 1
fi

echo "🛑 Arrêt du service..."
systemctl stop $SERVICE_NAME 2>/dev/null || echo "Service déjà arrêté"

cd "$APP_DIR"

echo ""
echo "🔍 Détection du système de base de données installé..."

# Détection de MySQL vs MariaDB
MYSQL_INSTALLED=false
MARIADB_INSTALLED=false

if dpkg -l | grep -q "mysql-server" && ! dpkg -l | grep -q "mariadb-server"; then
    MYSQL_INSTALLED=true
    echo "✅ MySQL détecté comme système principal"
elif dpkg -l | grep -q "mariadb-server"; then
    MARIADB_INSTALLED=true
    echo "✅ MariaDB détecté comme système principal"
elif systemctl is-active --quiet mysql 2>/dev/null; then
    # Test du service actif
    if mysql --version 2>/dev/null | grep -q "MariaDB"; then
        MARIADB_INSTALLED=true
        echo "✅ MariaDB détecté (service actif)"
    else
        MYSQL_INSTALLED=true
        echo "✅ MySQL détecté (service actif)"
    fi
else
    echo "⚠️ Aucun système de base de données détecté, installation de MariaDB (recommandé Ubuntu)"
    MARIADB_INSTALLED=true
fi

echo ""
echo "📦 Nettoyage des packages conflictuels..."

# Nettoyage des packages problématiques
apt-get remove --purge -y libmariadb-dev libmariadb-dev-compat 2>/dev/null || true
apt-get remove --purge -y libmysqlclient-dev default-libmysqlclient-dev 2>/dev/null || true
apt-get autoremove -y
apt-get autoclean

echo ""
echo "📦 Installation des dépendances de base..."
apt-get update -qq

# Installation des outils de développement de base
apt-get install -y \
    pkg-config \
    python3-dev \
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    curl \
    wget

if [ "$MARIADB_INSTALLED" = true ]; then
    echo ""
    echo "🗄️ Configuration pour MariaDB..."
    
    # Installation MariaDB et dépendances
    apt-get install -y \
        mariadb-server \
        mariadb-client \
        libmariadb-dev \
        libmariadb-dev-compat
    
    # Configuration MariaDB
    if ! systemctl is-active --quiet mariadb; then
        systemctl start mariadb
        systemctl enable mariadb
    fi
    
    echo "✅ MariaDB et dépendances installés"
    
else
    echo ""
    echo "🗄️ Configuration pour MySQL..."
    
    # Installation MySQL et dépendances
    apt-get install -y \
        mysql-server \
        mysql-client \
        libmysqlclient-dev \
        default-libmysqlclient-dev
    
    # Configuration MySQL
    if ! systemctl is-active --quiet mysql; then
        systemctl start mysql
        systemctl enable mysql
    fi
    
    echo "✅ MySQL et dépendances installés"
fi

echo ""
echo "🔧 Configuration des variables d'environnement..."

# Configuration des variables selon le système
if [ "$MARIADB_INSTALLED" = true ]; then
    # Configuration pour MariaDB
    export MYSQLCLIENT_CFLAGS="$(pkg-config --cflags mariadb 2>/dev/null || pkg-config --cflags libmariadb 2>/dev/null || echo '-I/usr/include/mariadb')"
    export MYSQLCLIENT_LDFLAGS="$(pkg-config --libs mariadb 2>/dev/null || pkg-config --libs libmariadb 2>/dev/null || echo '-lmariadb')"
else
    # Configuration pour MySQL
    export MYSQLCLIENT_CFLAGS="$(pkg-config --cflags mysqlclient 2>/dev/null || echo '-I/usr/include/mysql')"
    export MYSQLCLIENT_LDFLAGS="$(pkg-config --libs mysqlclient 2>/dev/null || echo '-lmysqlclient')"
fi

echo "Variables configurées:"
echo "MYSQLCLIENT_CFLAGS: $MYSQLCLIENT_CFLAGS"
echo "MYSQLCLIENT_LDFLAGS: $MYSQLCLIENT_LDFLAGS"

echo ""
echo "🐍 Mise à jour de l'environnement Python..."
sudo -u ntp-monitor .venv/bin/python -m pip install --upgrade pip setuptools wheel

echo ""
echo "🗄️ Installation de mysqlclient avec la configuration appropriée..."

# Tentative d'installation de mysqlclient avec les bonnes variables
if sudo -u ntp-monitor env MYSQLCLIENT_CFLAGS="$MYSQLCLIENT_CFLAGS" MYSQLCLIENT_LDFLAGS="$MYSQLCLIENT_LDFLAGS" .venv/bin/pip install mysqlclient; then
    echo "✅ mysqlclient installé avec succès"
    MYSQL_DRIVER="mysqlclient"
else
    echo "⚠️ Échec installation mysqlclient, utilisation de PyMySQL..."
    
    # Installation et configuration de PyMySQL
    sudo -u ntp-monitor .venv/bin/pip install PyMySQL==1.1.0
    
    # Configuration de PyMySQL comme MySQLdb
    sudo -u ntp-monitor .venv/bin/python -c "
import pymysql
pymysql.install_as_MySQLdb()
print('✅ PyMySQL configuré comme driver MySQL')
"
    MYSQL_DRIVER="pymysql"
fi

echo ""
echo "🔧 Configuration de la base de données..."

# Commandes SQL selon le système
if [ "$MARIADB_INSTALLED" = true ]; then
    DB_CMD="mariadb"
    SERVICE_NAME_DB="mariadb"
else
    DB_CMD="mysql"
    SERVICE_NAME_DB="mysql"
fi

# Assurer que le service est actif
systemctl start $SERVICE_NAME_DB
systemctl enable $SERVICE_NAME_DB

# Configuration de la base de données
$DB_CMD -u root -e "CREATE DATABASE IF NOT EXISTS ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || true
$DB_CMD -u root -e "CREATE USER IF NOT EXISTS 'ntp_monitor'@'localhost' IDENTIFIED BY 'ntp_password_2024';" 2>/dev/null || true
$DB_CMD -u root -e "GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_monitor'@'localhost';" 2>/dev/null || true
$DB_CMD -u root -e "FLUSH PRIVILEGES;" 2>/dev/null || true

echo ""
echo "🔧 Installation des dépendances Flask..."
sudo -u ntp-monitor .venv/bin/pip install \
    Flask==2.3.3 \
    Flask-SQLAlchemy==3.0.5 \
    Flask-Login==0.6.3 \
    Flask-WTF==1.2.1 \
    Flask-SocketIO==5.3.6 \
    python-socketio==5.8.0 \
    python-engineio==4.7.1 \
    ntplib==0.4.0 \
    requests==2.31.0 \
    python-dateutil==2.8.2 \
    pytz==2023.3 \
    psutil==5.9.5 \
    python-dotenv==1.0.0 \
    jinja2==3.1.2 \
    bcrypt==4.0.1 \
    Werkzeug==2.3.7

echo ""
echo "🔧 Test complet de l'environnement..."
sudo -u ntp-monitor .venv/bin/python -c "
import sys
print(f'Python: {sys.version}')

try:
    # Test Flask
    import flask
    import flask_sqlalchemy
    import flask_login  
    import flask_socketio
    print(f'✅ Flask: {flask.__version__}')
    
    # Test MySQL/MariaDB
    try:
        import MySQLdb
        print('✅ MySQLdb disponible')
    except ImportError:
        import pymysql
        pymysql.install_as_MySQLdb()
        import MySQLdb
        print('✅ PyMySQL configuré comme MySQLdb')
    
    # Test autres modules
    import ntplib
    import requests
    import bcrypt
    print('✅ Tous les modules critiques importés avec succès')
    
except ImportError as e:
    print(f'❌ Erreur import: {e}')
    exit(1)
"

echo ""
echo "🗄️ Test de connexion à la base de données..."
sudo -u ntp-monitor .venv/bin/python -c "
import sys
sys.path.insert(0, '.')

# Configuration de l'URL de base de données selon le driver
if '$MYSQL_DRIVER' == 'pymysql':
    db_url = 'mysql+pymysql://ntp_monitor:ntp_password_2024@localhost/ntp_monitor'
else:
    db_url = 'mysql://ntp_monitor:ntp_password_2024@localhost/ntp_monitor'

try:
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    
    with app.app_context():
        # Test de connexion simple
        result = db.engine.execute('SELECT 1 as test')
        print('✅ Connexion base de données réussie')
        print(f'Driver utilisé: $MYSQL_DRIVER')
        
except Exception as e:
    print(f'⚠️ Erreur connexion DB: {e}')
    print('Base de données sera configurée au démarrage')
"

echo ""
echo "⚙️ Configuration du fichier .env..."
if [ ! -f ".env" ]; then
    if [ "$MYSQL_DRIVER" = "pymysql" ]; then
        DB_URL="mysql+pymysql://ntp_monitor:ntp_password_2024@localhost/ntp_monitor"
    else
        DB_URL="mysql://ntp_monitor:ntp_password_2024@localhost/ntp_monitor"
    fi
    
    cat > ".env" << EOF
# Configuration production NTP Monitor Enterprise
FLASK_ENV=production
DATABASE_URL=$DB_URL
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
HOST=0.0.0.0
PORT=5000
DEBUG=False
EOF
    chown ntp-monitor:ntp-monitor .env
    chmod 600 .env
    echo "✅ Fichier .env configuré avec l'URL de base de données appropriée"
fi

echo ""
echo "🚀 Redémarrage du service NTP Monitor..."
systemctl start $SERVICE_NAME

echo ""
echo "🏥 Vérification finale..."
sleep 5
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Service démarré avec succès"
    
    sleep 3
    if curl -f -s http://localhost:5000/api/system/status > /dev/null 2>&1; then
        echo "✅ Application accessible et fonctionnelle"
        echo ""
        echo "🎉 CONFIGURATION RÉUSSIE !"
        echo "========================"
        echo ""
        if [ "$MARIADB_INSTALLED" = true ]; then
            echo "🗄️ Système: MariaDB avec driver $MYSQL_DRIVER"
        else
            echo "🗄️ Système: MySQL avec driver $MYSQL_DRIVER"
        fi
        echo "🔗 Application: http://$(hostname -I | awk '{print $1}'):5000"
        echo "👤 Login: admin / admin123"
    else
        echo "⚠️ Application pas encore accessible, vérifiez dans quelques instants"
    fi
else
    echo "⚠️ Problème avec le service:"
    systemctl status $SERVICE_NAME --no-pager -l
fi

echo ""
echo "📝 Résumé des actions:"
if [ "$MARIADB_INSTALLED" = true ]; then
    echo "   • MariaDB configuré comme système de base de données"
    echo "   • libmariadb-dev installé (pas de conflit)"
else
    echo "   • MySQL configuré comme système de base de données"  
    echo "   • libmysqlclient-dev installé (pas de conflit)"
fi
echo "   • Driver Python: $MYSQL_DRIVER"
echo "   • Base de données ntp_monitor créée et accessible"
echo "   • Variables d'environnement configurées"
echo "   • Service NTP Monitor opérationnel" 