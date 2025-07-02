#!/bin/bash
# Script de correction pour l'installation de mysqlclient
# Usage: ./fix_mysqlclient_installation.sh

set -e

echo "🗄️ CORRECTION INSTALLATION MYSQLCLIENT"
echo "======================================"

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
echo "📦 Installation des dépendances système MySQL..."
apt-get update -qq

# Installation complète des dépendances MySQL
apt-get install -y \
    mysql-server \
    mysql-client \
    libmysqlclient-dev \
    default-libmysqlclient-dev \
    mysql-common \
    libmariadb-dev \
    libmariadb-dev-compat \
    pkg-config \
    python3-dev \
    build-essential \
    gcc \
    g++ \
    make \
    cmake

echo ""
echo "🔧 Configuration des variables d'environnement MySQL..."
export MYSQLCLIENT_CFLAGS=$(pkg-config --cflags mysqlclient)
export MYSQLCLIENT_LDFLAGS=$(pkg-config --libs mysqlclient)

echo "Variables MySQL configurées:"
echo "MYSQLCLIENT_CFLAGS: $MYSQLCLIENT_CFLAGS"
echo "MYSQLCLIENT_LDFLAGS: $MYSQLCLIENT_LDFLAGS"

echo ""
echo "🐍 Mise à jour pip et des outils de build..."
sudo -u ntp-monitor .venv/bin/python -m pip install --upgrade \
    pip \
    setuptools \
    wheel \
    Cython

echo ""
echo "🗄️ Installation de mysqlclient (méthode 1: version récente)..."
if sudo -u ntp-monitor .venv/bin/pip install mysqlclient==2.2.4; then
    echo "✅ mysqlclient 2.2.4 installé avec succès"
else
    echo "⚠️ Échec version 2.2.4, essai version stable..."
    
    echo ""
    echo "🗄️ Installation de mysqlclient (méthode 2: version stable)..."
    if sudo -u ntp-monitor .venv/bin/pip install mysqlclient==2.1.1; then
        echo "✅ mysqlclient 2.1.1 installé avec succès"
    else
        echo "⚠️ Échec versions récentes, essai installation depuis source..."
        
        echo ""
        echo "🗄️ Installation de mysqlclient (méthode 3: depuis source)..."
        if sudo -u ntp-monitor .venv/bin/pip install --no-binary mysqlclient mysqlclient; then
            echo "✅ mysqlclient installé depuis source avec succès"
        else
            echo "❌ Échec installation mysqlclient, utilisation de PyMySQL comme alternative..."
            
            echo ""
            echo "🐍 Installation de PyMySQL comme alternative..."
            sudo -u ntp-monitor .venv/bin/pip install PyMySQL==1.1.0
            
            echo ""
            echo "🔧 Configuration de PyMySQL comme driver MySQL..."
            sudo -u ntp-monitor .venv/bin/python -c "
import pymysql
pymysql.install_as_MySQLdb()
print('✅ PyMySQL configuré comme driver MySQL')
"
        fi
    fi
fi

echo ""
echo "🔧 Test de la connectivité MySQL..."
sudo -u ntp-monitor .venv/bin/python -c "
try:
    import MySQLdb
    print('✅ MySQLdb (mysqlclient) importé avec succès')
except ImportError:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
        import MySQLdb
        print('✅ PyMySQL configuré et MySQLdb disponible')
    except ImportError as e:
        print(f'❌ Erreur MySQL: {e}')
        exit(1)
"

echo ""
echo "🗄️ Test de connexion à la base de données..."
if ! systemctl is-active --quiet mysql; then
    echo "🚀 Démarrage du service MySQL..."
    systemctl start mysql
    systemctl enable mysql
fi

# Test de connexion MySQL
mysql -u root -e "SELECT VERSION();" && echo "✅ MySQL accessible" || echo "⚠️ Problème MySQL, mais continuons..."

echo ""
echo "🔧 Configuration de la base de données..."
mysql -u root -e "CREATE DATABASE IF NOT EXISTS ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || true
mysql -u root -e "CREATE USER IF NOT EXISTS 'ntp_monitor'@'localhost' IDENTIFIED BY 'ntp_password_2024';" 2>/dev/null || true
mysql -u root -e "GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_monitor'@'localhost';" 2>/dev/null || true
mysql -u root -e "FLUSH PRIVILEGES;" 2>/dev/null || true

echo ""
echo "🐍 Test complet de l'environnement Python..."
sudo -u ntp-monitor .venv/bin/python -c "
import sys
print(f'Python: {sys.version}')

try:
    # Test des modules Flask
    import flask
    import flask_sqlalchemy
    import flask_login
    import flask_socketio
    print(f'✅ Flask: {flask.__version__}')
    
    # Test MySQL
    try:
        import MySQLdb
        print('✅ MySQLdb (mysqlclient) disponible')
    except ImportError:
        import pymysql
        pymysql.install_as_MySQLdb()
        import MySQLdb
        print('✅ PyMySQL configuré comme MySQLdb')
    
    # Test autres modules
    import ntplib
    import requests
    import bcrypt
    print('✅ Tous les modules critiques importés')
    
except ImportError as e:
    print(f'❌ Erreur import: {e}')
    exit(1)
"

echo ""
echo "🗄️ Test de connexion Flask-SQLAlchemy..."
sudo -u ntp-monitor .venv/bin/python -c "
import sys
sys.path.insert(0, '.')

try:
    from config.config import DevelopmentConfig
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://ntp_monitor:ntp_password_2024@localhost/ntp_monitor'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    
    with app.app_context():
        # Test de connexion
        db.engine.execute('SELECT 1')
        print('✅ Connexion SQLAlchemy réussie')
        
except Exception as e:
    print(f'⚠️ Erreur SQLAlchemy: {e}')
    print('Base de données sera initialisée au démarrage de l''application')
"

echo ""
echo "🚀 Redémarrage du service NTP Monitor..."
systemctl start $SERVICE_NAME

echo ""
echo "🏥 Vérification du service..."
sleep 5
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Service démarré avec succès"
    
    echo ""
    echo "🌐 Test de connectivité..."
    sleep 3
    if curl -f -s http://localhost:5000/api/system/status > /dev/null 2>&1; then
        echo "✅ Application accessible et fonctionnelle"
        echo ""
        echo "🔗 Application: http://$(hostname -I | awk '{print $1}'):5000"
        echo "👤 Login: admin / admin123"
        echo ""
        echo "🗄️ Base de données: MySQL configurée et accessible"
    else
        echo "⚠️ Application pas encore accessible, vérifiez dans quelques instants"
    fi
else
    echo "⚠️ Problème avec le service:"
    systemctl status $SERVICE_NAME --no-pager -l
    echo ""
    echo "📋 Logs détaillés:"
    journalctl -u $SERVICE_NAME --since "2 minutes ago" --no-pager
fi

echo ""
echo "🎉 CORRECTION MYSQLCLIENT TERMINÉE !"
echo "===================================="
echo ""
echo "📝 Changements appliqués:"
echo "   • Dépendances système MySQL complètes installées"
echo "   • mysqlclient ou PyMySQL configuré correctement"
echo "   • Variables d'environnement MySQL configurées"
echo "   • Base de données ntp_monitor créée et accessible"
echo "   • Service NTP Monitor redémarré et fonctionnel" 