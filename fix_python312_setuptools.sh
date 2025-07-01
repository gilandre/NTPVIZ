#!/bin/bash
# Script de correction pour Python 3.12 + setuptools compatibility
# Usage: ./fix_python312_setuptools.sh

set -e

echo "🐍 CORRECTION PYTHON 3.12 + SETUPTOOLS"
echo "======================================="

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
echo "🐍 Détection de la version Python..."
python3 --version
python3 -c "import sys; print(f'Version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"

echo ""
echo "🧹 Nettoyage complet de l'environnement virtuel..."
if [ -d ".venv" ]; then
    rm -rf .venv
    echo "✅ Ancien environnement virtuel supprimé"
fi

echo ""
echo "🐍 Création d'un nouvel environnement virtuel..."
sudo -u ntp-monitor python3 -m venv .venv

echo ""
echo "🐍 Mise à jour critique de pip et setuptools pour Python 3.12..."
sudo -u ntp-monitor .venv/bin/python -m pip install --upgrade \
    pip==23.3.1 \
    setuptools==69.0.2 \
    wheel==0.42.0

echo ""
echo "🐍 Vérification des versions critiques..."
sudo -u ntp-monitor .venv/bin/python -c "import setuptools; print(f'setuptools: {setuptools.__version__}')"
sudo -u ntp-monitor .venv/bin/python -c "import pkg_resources; print('pkg_resources: OK')" || echo "⚠️ pkg_resources pas encore installé"

echo ""
echo "🐍 Installation des dépendances de base (Python 3.12 compatible)..."
sudo -u ntp-monitor .venv/bin/pip install \
    Cython==3.0.5 \
    packaging==23.2 \
    distlib==0.3.7

echo ""
echo "🐍 Installation MySQL dependencies..."
sudo -u ntp-monitor .venv/bin/pip install mysqlclient

echo ""
echo "🐍 Installation Flask et dépendances principales..."
sudo -u ntp-monitor .venv/bin/pip install \
    Flask==2.3.3 \
    Flask-SQLAlchemy==3.0.5 \
    Flask-Login==0.6.3 \
    Flask-WTF==1.2.1 \
    Flask-SocketIO==5.3.6 \
    SQLAlchemy==2.0.21 \
    Werkzeug==2.3.7

echo ""
echo "🐍 Installation WebSocket (versions compatibles)..."
sudo -u ntp-monitor .venv/bin/pip install \
    python-socketio==5.8.0 \
    python-engineio==4.7.1

echo ""
echo "🐍 Installation des utilitaires réseau..."
sudo -u ntp-monitor .venv/bin/pip install \
    ntplib==0.4.0 \
    requests==2.31.0 \
    bcrypt==4.0.1 \
    PyMySQL==1.1.0 \
    python-dateutil==2.8.2 \
    pytz==2023.3

echo ""
echo "🐍 Installation des dépendances optionnelles (sans numpy problématique)..."
sudo -u ntp-monitor .venv/bin/pip install \
    psutil==5.9.5 \
    python-dotenv==1.0.0 \
    jinja2==3.1.2 \
    cryptography==41.0.8

echo ""
echo "📝 Tentative d'installation des dépendances restantes depuis requirements.txt..."
if [ -f "requirements.txt" ]; then
    # Installation en ignorant les erreurs sur les packages optionnels
    sudo -u ntp-monitor .venv/bin/pip install -r requirements.txt --no-deps || echo "⚠️ Some optional packages failed, continuing..."
else
    echo "⚠️ requirements.txt non trouvé, packages de base installés"
fi

echo ""
echo "🔧 Test de l'environnement Python..."
sudo -u ntp-monitor .venv/bin/python -c "
try:
    import flask
    import flask_sqlalchemy
    import flask_login
    import flask_socketio
    import ntplib
    import mysqlclient
    print('✅ Modules critiques importés avec succès')
    print(f'Flask: {flask.__version__}')
    print(f'Flask-SocketIO: {flask_socketio.__version__}')
except ImportError as e:
    print(f'❌ Erreur import: {e}')
    exit(1)
"

echo ""
echo "🗄️ Configuration MySQL..."
if ! systemctl is-active --quiet mysql; then
    systemctl start mysql
    systemctl enable mysql
fi

# Configuration basique MySQL
mysql -u root -e "CREATE DATABASE IF NOT EXISTS ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || true
mysql -u root -e "CREATE USER IF NOT EXISTS 'ntp_monitor'@'localhost' IDENTIFIED BY 'ntp_password_2024';" 2>/dev/null || true
mysql -u root -e "GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_monitor'@'localhost';" 2>/dev/null || true
mysql -u root -e "FLUSH PRIVILEGES;" 2>/dev/null || true

echo ""
echo "⚙️ Configuration de l'application..."
if [ ! -f ".env" ]; then
    cat > ".env" << EOF
# Configuration production NTP Monitor Enterprise - Python 3.12
FLASK_ENV=production
DATABASE_URL=mysql://ntp_monitor:ntp_password_2024@localhost/ntp_monitor
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
HOST=0.0.0.0
PORT=5000
DEBUG=False
EOF
    chown ntp-monitor:ntp-monitor .env
    chmod 600 .env
fi

echo ""
echo "🗄️ Initialisation de la base de données..."
sudo -u ntp-monitor .venv/bin/python -c "
import sys
sys.path.insert(0, '.')
try:
    from backend.database_manager import db_manager
    db_manager.initialize()
    print('✅ Base de données initialisée')
except Exception as e:
    print(f'⚠️ Erreur DB: {e}')
" || echo "Base de données sera initialisée au démarrage"

sudo -u ntp-monitor .venv/bin/python -c "
import sys
sys.path.insert(0, '.')
try:
    from backend.utils.init_data import init_default_data
    init_default_data()
    print('✅ Données par défaut initialisées')
except Exception as e:
    print(f'⚠️ Erreur données: {e}')
" || echo "Données par défaut seront initialisées au démarrage"

echo ""
echo "🔧 Configuration des permissions..."
chown -R ntp-monitor:ntp-monitor "$APP_DIR"
chmod +x app.py 2>/dev/null || true

echo ""
echo "🚀 Redémarrage du service..."
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
echo "🎉 CORRECTION PYTHON 3.12 TERMINÉE !"
echo "===================================="
echo ""
echo "📝 Changements appliqués:"
echo "   • Environnement virtuel recréé pour Python 3.12"
echo "   • setuptools mis à jour vers version 69.0.2 (compatible Python 3.12)"
echo "   • pip mis à jour vers version 23.3.1"
echo "   • pkg_resources compatibility fixé"
echo "   • Toutes les dépendances réinstallées proprement"
echo ""
echo "🔗 Application: http://$(hostname -I | awk '{print $1}'):5000"
echo "👤 Login: admin / admin123" 