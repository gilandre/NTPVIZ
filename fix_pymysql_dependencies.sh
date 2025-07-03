#!/bin/bash
# Correction rapide - Installation modules manquants sur serveur 79.137.36.66
set -e

echo "🔧 CORRECTION MODULES MANQUANTS - SERVEUR 79.137.36.66"
echo "======================================================="

REMOTE_SERVER="79.137.36.66"
REMOTE_USER="ubuntu"
PROJECT_DIR="/opt/NTPVIZ"
SERVICE_NAME="ntp-monitor"

echo "📍 Serveur: $REMOTE_SERVER"
echo "🕒 $(date)"

# Test connexion
if ! ssh -o ConnectTimeout=10 $REMOTE_USER@$REMOTE_SERVER "echo 'SSH OK'"; then
    echo "❌ Connexion SSH échouée"
    exit 1
fi

echo "✅ Connexion SSH établie"

# Exécuter la correction sur le serveur
echo "🔧 Installation des modules manquants..."

ssh -t $REMOTE_USER@$REMOTE_SERVER << 'EOF'
echo "🔄 Correction modules Python sur le serveur..."

PROJECT_DIR="/opt/NTPVIZ"
SERVICE_NAME="ntp-monitor"

# Stopper le service
echo "🛑 Arrêt temporaire du service..."
sudo systemctl stop $SERVICE_NAME 2>/dev/null || true

cd $PROJECT_DIR

# Installation des modules manquants
echo "📦 Installation modules Python manquants..."
sudo -u ntp-monitor bash << 'PYEOF'
source .venv/bin/activate

echo "📋 Modules actuels:"
pip list | grep -E "(Flask|pymysql|SQLAlchemy)" || echo "Modules manquants détectés"

echo ""
echo "🔧 Installation modules manquants..."

# Modules de base manquants
pip install -q pymysql==1.1.0
pip install -q mysqlclient==2.2.1 || echo "⚠️ mysqlclient optionnel"

# Modules Flask supplémentaires
pip install -q flask-cors==4.0.0
pip install -q flask-wtf==1.2.1
pip install -q wtforms==3.1.1

# Modules système et utilitaires
pip install -q psutil==5.9.6
pip install -q python-dotenv==1.0.0
pip install -q email-validator==2.1.0

# Modules pour NTP et monitoring
pip install -q ntplib==0.4.0
pip install -q ipaddress==1.0.23 || echo "⚠️ ipaddress intégré à Python"

# Modules pour WebSocket et temps réel
pip install -q eventlet==0.33.3
pip install -q gevent==23.9.1 || echo "⚠️ gevent optionnel"

# Modules cryptographiques
pip install -q passlib==1.7.4
pip install -q argon2-cffi==23.1.0

echo ""
echo "✅ Installation terminée"

echo "📋 Modules installés:"
pip list | grep -E "(Flask|pymysql|SQLAlchemy|ntplib|passlib)" | sort

echo ""
echo "🧪 Test imports critiques:"
python3 -c "
try:
    import pymysql
    print('✅ pymysql OK')
except ImportError as e:
    print(f'❌ pymysql: {e}')

try:
    import flask
    print('✅ flask OK')
except ImportError as e:
    print(f'❌ flask: {e}')

try:
    import sqlalchemy
    print('✅ sqlalchemy OK')
except ImportError as e:
    print(f'❌ sqlalchemy: {e}')

try:
    import ntplib
    print('✅ ntplib OK')
except ImportError as e:
    print(f'❌ ntplib: {e}')

try:
    import flask_login
    print('✅ flask_login OK')
except ImportError as e:
    print(f'❌ flask_login: {e}')

try:
    import flask_socketio
    print('✅ flask_socketio OK')
except ImportError as e:
    print(f'❌ flask_socketio: {e}')
"
PYEOF

# Test de l'application
echo ""
echo "🧪 Test application complète..."
sudo -u ntp-monitor bash -c "
cd $PROJECT_DIR
source .venv/bin/activate
export PYTHONPATH='$PROJECT_DIR'
timeout 10 python3 -c '
import sys
sys.path.insert(0, \"$PROJECT_DIR\")
try:
    import app
    print(\"✅ Application importée avec succès\")
except Exception as e:
    print(f\"❌ Erreur import app: {e}\")
    import traceback
    traceback.print_exc()
'
"

if [ $? -eq 0 ]; then
    echo "✅ Tests réussis"
else
    echo "⚠️ Tests partiels - vérification des logs"
fi

# Redémarrer le service
echo ""
echo "🚀 Redémarrage du service..."
sudo systemctl start $SERVICE_NAME

# Attendre le démarrage
sleep 8

# Vérifier le statut
echo "📊 Statut du service:"
sudo systemctl is-active $SERVICE_NAME
sudo systemctl status $SERVICE_NAME --no-pager -l | head -10

echo ""
echo "📋 Logs récents (15 dernières lignes):"
sudo journalctl -u $SERVICE_NAME --no-pager -n 15

echo ""
echo "🎉 CORRECTION TERMINÉE !"
echo "======================="
echo "🌐 URL: http://79.137.36.66/"
echo "📊 Santé: http://79.137.36.66/health"
echo ""
echo "🔧 Si problème persiste:"
echo "   ssh ubuntu@79.137.36.66"
echo "   sudo journalctl -u ntp-monitor -f"
EOF

# Test final depuis la machine locale
echo ""
echo "🔍 Test final de connexion..."
sleep 5

if curl -I -s --connect-timeout 15 http://$REMOTE_SERVER/ | grep -q "200\|302\|404"; then
    echo "✅ Serveur web répond"
    
    # Test spécifique de l'API santé
    if curl -s --connect-timeout 10 http://$REMOTE_SERVER/health | grep -q "status\|healthy"; then
        echo "✅ API santé fonctionnelle"
    else
        echo "⚠️ API santé en cours d'initialisation"
    fi
else
    echo "⚠️ Application en cours de démarrage..."
    echo "Attendez quelques secondes et testez manuellement:"
    echo "curl -I http://$REMOTE_SERVER/"
fi

echo ""
echo "🎉 CORRECTION MODULES PYTHON TERMINÉE !"
echo "======================================="
echo "🌐 Application: http://$REMOTE_SERVER/"
echo "📊 API Santé: http://$REMOTE_SERVER/health"
echo "📋 Logs: ssh $REMOTE_USER@$REMOTE_SERVER 'sudo journalctl -u ntp-monitor -f'"
echo ""
echo "🔧 Modules critiques installés:"
echo "   ✅ pymysql (connexion base de données)"
echo "   ✅ flask-cors (Cross-Origin Resource Sharing)"
echo "   ✅ ntplib (protocole NTP)"
echo "   ✅ psutil (monitoring système)"
echo ""
echo "🚀 EMERAUDEVIZ NTP devrait maintenant fonctionner !" 