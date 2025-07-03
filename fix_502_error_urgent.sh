#!/bin/bash
# CORRECTION URGENTE ERREUR 502 BAD GATEWAY
# Fix pymysql + diagnostic complet

set -e

echo "🚨 CORRECTION URGENTE ERREUR 502 BAD GATEWAY"
echo "============================================"

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

# Diagnostic et correction sur le serveur
ssh -t $REMOTE_USER@$REMOTE_SERVER << 'EOF'
echo "🔍 DIAGNOSTIC COMPLET DU PROBLÈME 502"
echo "======================================"

PROJECT_DIR="/opt/NTPVIZ"
SERVICE_NAME="ntp-monitor"

# Étape 1: Diagnostic des services
echo "📊 1. STATUT DES SERVICES"
echo "------------------------"
echo "🔧 Nginx:"
sudo systemctl is-active nginx || echo "❌ Nginx arrêté"
echo "🔧 NTP Monitor:"
sudo systemctl is-active $SERVICE_NAME || echo "❌ NTP Monitor arrêté"

echo ""
echo "📋 2. LOGS RÉCENTS NTP MONITOR"
echo "------------------------------"
sudo journalctl -u $SERVICE_NAME --no-pager -n 20

echo ""
echo "📋 3. PROCESSUS SUR PORT 5000"
echo "-----------------------------"
sudo netstat -tlnp | grep :5000 || echo "❌ Aucun processus sur port 5000"

echo ""
echo "🔧 4. CORRECTION DES MODULES MANQUANTS"
echo "======================================="

cd $PROJECT_DIR

# Arrêter le service défaillant
sudo systemctl stop $SERVICE_NAME 2>/dev/null || true

# Installation urgente des modules
echo "📦 Installation modules critiques..."
sudo -u ntp-monitor bash << 'PYFIX'
source .venv/bin/activate

echo "🔧 Installation pymysql et dépendances critiques..."
pip install -q --upgrade pip

# Modules absolument nécessaires
pip install -q pymysql==1.1.0
pip install -q flask-cors==4.0.0
pip install -q python-dotenv==1.0.0
pip install -q psutil==5.9.6

# Modules Flask essentiels (vérification versions)
pip install -q Flask==2.3.3
pip install -q Werkzeug==2.3.7
pip install -q flask-login==0.6.3
pip install -q flask-socketio==5.3.6
pip install -q SQLAlchemy==2.0.23

# Modules NTP
pip install -q ntplib==0.4.0
pip install -q python-dateutil==2.8.2
pip install -q pytz==2023.3

echo "✅ Modules installés"

echo "🧪 Test des imports critiques:"
python3 -c "
modules = ['pymysql', 'flask', 'sqlalchemy', 'ntplib', 'flask_login', 'flask_socketio']
for module in modules:
    try:
        __import__(module)
        print(f'✅ {module} OK')
    except ImportError as e:
        print(f'❌ {module}: {e}')
"
PYFIX

echo ""
echo "🧪 5. TEST APPLICATION"
echo "====================="

# Test direct de l'application
echo "🔍 Test import application..."
sudo -u ntp-monitor bash -c "
cd $PROJECT_DIR
source .venv/bin/activate
export PYTHONPATH='$PROJECT_DIR'
export FLASK_ENV=production

timeout 15 python3 << 'APPTEST'
import sys
sys.path.insert(0, '/opt/NTPVIZ')

try:
    print('🔄 Import app...')
    import app
    print('✅ App importée avec succès')
    
    print('🔄 Création app Flask...')
    flask_app, socketio = app.create_app()
    print('✅ App Flask créée')
    
    print('🔄 Test config...')
    print(f'Secret Key: {flask_app.config.get(\"SECRET_KEY\", \"Non définie\")[:10]}...')
    print(f'Database URL: {flask_app.config.get(\"DATABASE_URL\", \"Non définie\")}')
    
except Exception as e:
    print(f'❌ Erreur: {e}')
    import traceback
    traceback.print_exc()
APPTEST
"

# Vérifier la configuration
echo ""
echo "🔧 6. VÉRIFICATION CONFIGURATION"
echo "================================"

echo "📁 Répertoires:"
ls -la $PROJECT_DIR/logs/ 2>/dev/null || echo "❌ Répertoire logs manquant"
ls -la $PROJECT_DIR/instance/ 2>/dev/null || echo "❌ Répertoire instance manquant"

echo ""
echo "📄 Fichier .env:"
if [ -f "$PROJECT_DIR/.env" ]; then
    echo "✅ .env existe"
    cat $PROJECT_DIR/.env | head -10
else
    echo "❌ .env manquant - création..."
    sudo tee $PROJECT_DIR/.env > /dev/null << 'ENVEOF'
FLASK_ENV=production
FLASK_APP=app.py
SECRET_KEY=emeraudeviz-ntp-production-fix502
DATABASE_URL=sqlite:///instance/ntp_monitor.db
HOST=0.0.0.0
PORT=5000
ENVEOF
    sudo chown ntp-monitor:ntp-monitor $PROJECT_DIR/.env
fi

# Créer répertoires manquants
sudo mkdir -p $PROJECT_DIR/logs $PROJECT_DIR/instance
sudo chown -R ntp-monitor:ntp-monitor $PROJECT_DIR/logs $PROJECT_DIR/instance

echo ""
echo "🚀 7. REDÉMARRAGE FORCÉ"
echo "======================="

# Tuer tous les processus Python sur le port 5000
sudo pkill -f "python.*app.py" 2>/dev/null || echo "Aucun processus Python à tuer"
sudo fuser -k 5000/tcp 2>/dev/null || echo "Port 5000 libre"

# Redémarrer les services
echo "🔄 Redémarrage Nginx..."
sudo systemctl restart nginx

echo "🔄 Redémarrage NTP Monitor..."
sudo systemctl daemon-reload
sudo systemctl restart $SERVICE_NAME

# Attendre le démarrage
echo "⏳ Attente démarrage (15 secondes)..."
sleep 15

echo ""
echo "📊 8. VÉRIFICATION FINALE"
echo "========================="

echo "🔧 Statut services:"
echo "Nginx: $(sudo systemctl is-active nginx)"
echo "NTP Monitor: $(sudo systemctl is-active $SERVICE_NAME)"

echo ""
echo "🌐 Test port 5000:"
if sudo netstat -tlnp | grep :5000; then
    echo "✅ Application écoute sur port 5000"
else
    echo "❌ Aucune application sur port 5000"
fi

echo ""
echo "📋 Logs finaux (10 dernières lignes):"
sudo journalctl -u $SERVICE_NAME --no-pager -n 10

echo ""
echo "🧪 Test HTTP local:"
curl -I http://localhost:5000/ 2>/dev/null | head -3 || echo "❌ Pas de réponse HTTP locale"

echo ""
if sudo systemctl is-active $SERVICE_NAME | grep -q "active"; then
    echo "🎉 SERVICE ACTIF - Test externe..."
else
    echo "❌ SERVICE INACTIF - Problème persistant"
    echo "🔍 Diagnostic approfondi:"
    sudo journalctl -u $SERVICE_NAME --no-pager -n 30
fi

echo ""
echo "🎯 CORRECTION 502 TERMINÉE"
echo "=========================="
echo "🌐 Test URL: http://79.137.36.66/"
echo "📊 API Santé: http://79.137.36.66/health"
echo ""
echo "🔧 Si problème persiste:"
echo "   ssh ubuntu@79.137.36.66"
echo "   sudo journalctl -u ntp-monitor -f"
echo "   sudo systemctl status ntp-monitor"
EOF

# Test final depuis l'extérieur
echo ""
echo "🔍 TEST FINAL DEPUIS L'EXTÉRIEUR"
echo "================================"

sleep 5

echo "🌐 Test HTTP externe..."
if curl -I -s --connect-timeout 20 http://$REMOTE_SERVER/ | head -3; then
    echo ""
    echo "✅ SUCCÈS - Application accessible !"
    
    # Test de l'API santé
    echo "📊 Test API santé..."
    curl -s --connect-timeout 10 http://$REMOTE_SERVER/health 2>/dev/null | head -5 || echo "API santé en cours d'initialisation"
    
else
    echo "⚠️ Application encore en démarrage ou problème persistant"
    echo ""
    echo "🔧 Diagnostic manuel requis:"
    echo "   ssh ubuntu@79.137.36.66"
    echo "   sudo journalctl -u ntp-monitor -n 50"
    echo "   sudo systemctl status ntp-monitor"
    echo "   curl -I http://localhost:5000/"
fi

echo ""
echo "🎉 CORRECTION ERREUR 502 TERMINÉE !"
echo "==================================="
echo "🌐 URL: http://$REMOTE_SERVER/"
echo "📊 Santé: http://$REMOTE_SERVER/health"
echo "📋 Logs: ssh $REMOTE_USER@$REMOTE_SERVER 'sudo journalctl -u ntp-monitor -f'"
echo ""
echo "🚀 EMERAUDEVIZ NTP devrait maintenant être accessible !" 