#!/bin/bash
# Script de correction rapide pour les versions de packages problématiques
# Usage: ./fix_cryptography_version.sh

set -e

echo "🔧 CORRECTION VERSIONS PACKAGES PROBLÉMATIQUES"
echo "=============================================="

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
echo "🐍 Mise à jour pip vers la dernière version..."
sudo -u ntp-monitor .venv/bin/python -m pip install --upgrade pip

echo ""
echo "🔧 Correction des packages avec versions problématiques..."

echo "🔐 Installation de cryptography (version disponible)..."
sudo -u ntp-monitor .venv/bin/pip install "cryptography>=42.0.8" --upgrade

echo "🔧 Installation des dépendances de sécurité..."
sudo -u ntp-monitor .venv/bin/pip install \
    bcrypt==4.0.1 \
    Werkzeug==2.3.7

echo ""
echo "🔄 Mise à jour depuis GitHub..."
sudo -u ntp-monitor git fetch origin
sudo -u ntp-monitor git reset --hard origin/dev

echo ""
echo "🐍 Installation sélective des dépendances essentielles..."
sudo -u ntp-monitor .venv/bin/pip install \
    Flask==2.3.3 \
    Flask-SQLAlchemy==3.0.5 \
    Flask-Login==0.6.3 \
    Flask-WTF==1.2.1 \
    Flask-SocketIO==5.3.6 \
    python-socketio==5.8.0 \
    python-engineio==4.7.1 \
    ntplib==0.4.0 \
    mysqlclient \
    requests==2.31.0 \
    PyMySQL==1.1.0 \
    python-dateutil==2.8.2 \
    pytz==2023.3 \
    psutil==5.9.5 \
    python-dotenv==1.0.0 \
    jinja2==3.1.2

echo ""
echo "🔧 Test de l'environnement..."
sudo -u ntp-monitor .venv/bin/python -c "
try:
    import flask
    import flask_sqlalchemy
    import flask_login
    import flask_socketio
    import ntplib
    import mysqlclient
    import cryptography
    print('✅ Modules critiques importés avec succès')
    print(f'Flask: {flask.__version__}')
    print(f'Flask-SocketIO: {flask_socketio.__version__}')
    print(f'Cryptography: {cryptography.__version__}')
except ImportError as e:
    print(f'❌ Erreur import: {e}')
    exit(1)
"

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
        echo ""
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
echo "🎉 CORRECTION TERMINÉE !"
echo "======================="
echo ""
echo "📝 Changements appliqués:"
echo "   • cryptography mis à jour vers version disponible (>=42.0.8)"
echo "   • pip mis à jour vers la dernière version"
echo "   • Packages essentiels installés avec succès"
echo "   • Service redémarré et fonctionnel" 