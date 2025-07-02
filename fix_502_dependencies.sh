#!/bin/bash

echo "======================================================="
echo "  CORRECTION DÉPENDANCES - NTP MONITOR ENTERPRISE     "
echo "======================================================="
echo "Résolution des problèmes identifiés :"
echo "1. Conflit redis/celery versions"
echo "2. Module psutil manquant"
echo "3. Dépendances Python incomplètes"
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

log_info "Début de la correction des dépendances..."

cd "$APP_DIR" || exit 1

# Arrêt du service pour éviter les conflits
systemctl stop $SERVICE_NAME 2>/dev/null

# 1. CORRECTION DU CONFLIT REDIS/CELERY
log_info "1. Correction du conflit redis/celery..."
source "$VENV_PATH/bin/activate"

# Désinstallation des packages conflictuels
pip uninstall -y redis celery 2>/dev/null

# Installation des versions compatibles
log_info "Installation de redis 4.6.0 (compatible avec celery)..."
pip install redis==4.6.0

log_info "Installation de celery sans extra redis..."
pip install celery==5.3.4

# 2. INSTALLATION DES MODULES MANQUANTS
log_info "2. Installation des modules Python manquants..."

# Liste des modules critiques
REQUIRED_MODULES=(
    "psutil"
    "ntplib" 
    "pymysql"
    "cryptography"
    "flask"
    "flask-login"
    "flask-sqlalchemy"
    "flask-socketio"
    "python-socketio==5.8.0"
    "werkzeug"
    "jinja2"
    "click"
    "itsdangerous"
    "markupsafe"
    "sqlalchemy"
    "python-dotenv"
    "requests"
    "urllib3"
    "certifi"
    "charset-normalizer"
    "idna"
)

for module in "${REQUIRED_MODULES[@]}"; do
    log_info "Installation de $module..."
    pip install "$module" --no-deps --force-reinstall 2>/dev/null || {
        log_warning "Erreur installation $module, tentative sans contraintes..."
        pip install "${module%%==*}" --force-reinstall 2>/dev/null
    }
done

# 3. RÉINSTALLATION COMPLÈTE DES REQUIREMENTS
log_info "3. Réinstallation des requirements avec résolution de conflits..."

# Sauvegarde du requirements.txt original
cp requirements.txt requirements.txt.backup 2>/dev/null

# Création d'un requirements.txt corrigé
cat > requirements_fixed.txt << 'REQUIREMENTS_EOF'
# Core Flask
Flask==2.3.3
Flask-Login==0.6.3
Flask-SQLAlchemy==3.0.5
Flask-SocketIO==5.3.6

# Database
SQLAlchemy==2.0.23
PyMySQL==1.1.0
cryptography>=42.0.8

# WebSocket - Versions compatibles
python-socketio==5.8.0
python-engineio==4.7.1

# Redis et Celery - Versions compatibles
redis==4.6.0
celery==5.3.4

# Monitoring et Système
psutil==5.9.6
ntplib==0.4.0

# Utilitaires
python-dotenv==1.0.0
requests==2.31.0
click==8.1.7
itsdangerous==2.1.2
Jinja2==3.1.2
MarkupSafe==2.1.3
Werkzeug==2.3.7

# Python 3.12 compatibility
setuptools>=69.0.2
pip>=23.3.1
wheel>=0.42.0
REQUIREMENTS_EOF

# Installation avec le fichier corrigé
log_info "Installation avec requirements corrigés..."
pip install -r requirements_fixed.txt --force-reinstall

# 4. TEST DE L'ENVIRONNEMENT PYTHON
log_info "4. Test de l'environnement Python..."

python -c "
import sys
import importlib

modules_to_test = [
    'flask', 'flask_login', 'flask_sqlalchemy', 'flask_socketio',
    'sqlalchemy', 'pymysql', 'psutil', 'ntplib', 'redis', 'celery',
    'python_dotenv', 'requests', 'cryptography'
]

failed_modules = []
for module in modules_to_test:
    try:
        importlib.import_module(module)
        print(f'✅ {module}')
    except ImportError as e:
        print(f'❌ {module}: {e}')
        failed_modules.append(module)

if failed_modules:
    print(f'\\n❌ Modules manquants: {failed_modules}')
    sys.exit(1)
else:
    print('\\n✅ Tous les modules sont disponibles')
"

# 5. TEST DE CRÉATION DE L'APPLICATION
log_info "5. Test de création de l'application Flask..."

python -c "
import sys
import os
sys.path.insert(0, '.')

try:
    # Test des imports backend
    from backend.app import create_app
    print('✅ Import backend.app réussi')
    
    # Création de l'app
    app = create_app()
    print('✅ Création app Flask réussie')
    print(f'Database URI: {app.config.get(\"SQLALCHEMY_DATABASE_URI\", \"Non défini\")}')
    
    # Test du contexte app
    with app.app_context():
        print('✅ Contexte application fonctionnel')
        
        # Test de l'initialisation des données
        try:
            from backend.utils.init_data import init_default_data
            init_default_data()
            print('✅ Initialisation base de données réussie')
        except Exception as e:
            print(f'⚠️  Initialisation BDD: {e}')
            
except Exception as e:
    print(f'❌ Erreur: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

# 6. MISE À JOUR DE LA CONFIGURATION .ENV
log_info "6. Mise à jour de la configuration .env..."

# Mise à jour du .env avec les bonnes versions
cat >> "$APP_DIR/.env" << 'ENV_APPEND'

# Configuration Redis corrigée
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Configuration WebSocket corrigée
SOCKETIO_ASYNC_MODE=threading
SOCKETIO_CORS_ALLOWED_ORIGINS=*

# Configuration Debug
FLASK_DEBUG=False
SQLALCHEMY_ECHO=False
ENV_APPEND

# 7. REDÉMARRAGE DU SERVICE
log_info "7. Redémarrage du service..."

# Rechargement systemd
systemctl daemon-reload

# Démarrage du service
systemctl start $SERVICE_NAME
systemctl enable $SERVICE_NAME

# Attente du démarrage
sleep 8

# 8. VÉRIFICATION FINALE COMPLÈTE
log_info "8. Vérification finale..."

echo ""
echo "🔍 DIAGNOSTIC COMPLET"
echo "===================="

# Test du service
echo "Service ntp-monitor:"
if systemctl is-active --quiet $SERVICE_NAME; then
    log_success "✅ Service actif"
    systemctl status $SERVICE_NAME --no-pager -l | head -3
else
    log_error "❌ Service inactif"
    echo "Dernières erreurs:"
    journalctl -u $SERVICE_NAME -n 5 --no-pager
fi

echo ""
echo "Port 5000:"
if netstat -tlnp 2>/dev/null | grep -q ':5000'; then
    log_success "✅ Port 5000 en écoute"
    netstat -tlnp | grep ':5000'
else
    log_warning "❌ Port 5000 non accessible"
    echo "Ports Python actifs:"
    netstat -tlnp 2>/dev/null | grep python || echo "Aucun port Python actif"
fi

echo ""
echo "Test de connectivité:"
sleep 3
if curl -f -s -m 15 http://localhost:5000/ > /dev/null 2>&1; then
    log_success "✅ Application accessible"
elif curl -f -s -m 15 http://localhost:5000/health > /dev/null 2>&1; then
    log_success "✅ Application accessible (health check)"
else
    log_warning "❌ Application non accessible"
    
    # Test manuel final
    log_info "Test de démarrage manuel..."
    timeout 15 python app.py &
    PID=$!
    sleep 10
    if kill -0 $PID 2>/dev/null; then
        log_success "✅ Démarrage manuel réussi"
        kill $PID 2>/dev/null
    else
        log_error "❌ Échec démarrage manuel"
    fi
fi

echo ""
echo "📊 RÉSULTATS FINAUX"
echo "=================="

if systemctl is-active --quiet $SERVICE_NAME && netstat -tlnp 2>/dev/null | grep -q ':5000'; then
    log_success "🎉 CORRECTION RÉUSSIE !"
    echo ""
    echo "🌐 Application disponible sur :"
    echo "   http://79.137.36.66/"
    echo ""
    echo "👤 Comptes utilisateur :"
    echo "   Admin:    admin / admin123"
    echo "   Operator: operator / operator123" 
    echo "   Viewer:   viewer / viewer123"
    echo ""
    echo "📋 Monitoring :"
    echo "   journalctl -u ntp-monitor -f"
    echo "   systemctl status ntp-monitor"

elif systemctl is-active --quiet $SERVICE_NAME; then
    log_warning "⚠️ Service actif mais port non accessible"
    echo "Vérifiez la configuration Flask dans les logs."
    
else
    log_error "❌ Service toujours inactif"
    echo ""
    echo "🔧 Diagnostic avancé :"
    echo "   journalctl -u ntp-monitor -n 50"
    echo "   cd /opt/ntp-monitor && source .venv/bin/activate && python app.py"
    echo ""
    echo "📞 Modules installés :"
    pip list | grep -E "(flask|redis|celery|psutil|ntplib|pymysql)"
fi

echo ""
echo "📁 Fichiers créés/modifiés :"
echo "   - requirements_fixed.txt (versions compatibles)"
echo "   - .env (configuration mise à jour)"
echo "   - Modules Python corrigés"

deactivate 2>/dev/null || true
log_info "Correction des dépendances terminée." 