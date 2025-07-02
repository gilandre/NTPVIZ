#!/bin/bash

echo "======================================================="
echo "    CORRECTION FINALE - NTP MONITOR ENTERPRISE       "
echo "======================================================="
echo "Installation des modules manquants identifiés :"
echo "- python-dotenv (pour fichier .env)"
echo "- pytz (pour fuseaux horaires)"
echo "- Vérification complète de tous les modules"
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

log_info "Début de la correction finale..."

cd "$APP_DIR" || exit 1

# Arrêt du service
systemctl stop $SERVICE_NAME 2>/dev/null

# Activation de l'environnement virtuel
source "$VENV_PATH/bin/activate"

# 1. INSTALLATION DES MODULES MANQUANTS CRITIQUES
log_info "1. Installation des modules manquants critiques..."

# Liste complète des modules requis
CRITICAL_MODULES=(
    "python-dotenv"
    "pytz"
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
    "requests"
    "urllib3"
    "certifi"
    "charset-normalizer"
    "idna"
    "redis==4.6.0"
    "celery==5.3.4"
    "setuptools>=69.0.2"
)

log_info "Installation des modules critiques..."
for module in "${CRITICAL_MODULES[@]}"; do
    log_info "Installation de $module..."
    pip install "$module" --force-reinstall --no-cache-dir 2>/dev/null || {
        log_warning "Erreur installation $module, nouvelle tentative..."
        pip install "${module%%==*}" --force-reinstall --no-cache-dir
    }
done

# 2. CRÉATION D'UN REQUIREMENTS.TXT COMPLET
log_info "2. Création d'un requirements.txt complet..."

cat > requirements_complete.txt << 'REQUIREMENTS_EOF'
# Core Flask Framework
Flask==2.3.3
Flask-Login==0.6.3
Flask-SQLAlchemy==3.0.5
Flask-SocketIO==5.3.6
Werkzeug==2.3.7
Jinja2==3.1.2
click==8.1.7
itsdangerous==2.1.2
MarkupSafe==2.1.3

# Database & ORM
SQLAlchemy==2.0.23
PyMySQL==1.1.0
cryptography>=42.0.8

# WebSocket Support - Versions compatibles
python-socketio==5.8.0
python-engineio==4.7.1

# Redis et Celery - Versions compatibles testées
redis==4.6.0
celery==5.3.4

# Configuration et Environnement
python-dotenv==1.0.0

# Date et Time
pytz==2023.3

# Monitoring et Système
psutil==5.9.6
ntplib==0.4.0

# HTTP et Requests
requests==2.31.0
urllib3==2.0.7
certifi==2023.11.17
charset-normalizer==3.3.2
idna==3.6

# Python 3.12 Compatibility
setuptools>=69.0.2
pip>=23.3.1
wheel>=0.42.0

# Dépendances additionnelles
six==1.16.0
packaging==23.2
REQUIREMENTS_EOF

# Installation avec le fichier complet
log_info "Installation avec requirements complet..."
pip install -r requirements_complete.txt --force-reinstall --no-cache-dir

# 3. TEST COMPLET DE TOUS LES MODULES
log_info "3. Test complet de tous les modules..."

python -c "
import sys
import importlib

print('🔍 TEST COMPLET DES MODULES')
print('===========================')

# Modules critiques à tester
modules_to_test = [
    ('flask', 'Flask'),
    ('flask_login', 'Flask-Login'), 
    ('flask_sqlalchemy', 'Flask-SQLAlchemy'),
    ('flask_socketio', 'Flask-SocketIO'),
    ('sqlalchemy', 'SQLAlchemy'),
    ('pymysql', 'PyMySQL'),
    ('psutil', 'psutil'),
    ('ntplib', 'ntplib'),
    ('redis', 'redis'),
    ('celery', 'celery'),
    ('dotenv', 'python-dotenv'),
    ('pytz', 'pytz'),
    ('requests', 'requests'),
    ('cryptography', 'cryptography'),
    ('werkzeug', 'Werkzeug'),
    ('jinja2', 'Jinja2'),
    ('click', 'Click'),
    ('itsdangerous', 'ItsDangerous'),
    ('markupsafe', 'MarkupSafe')
]

failed_modules = []
success_count = 0

for module_name, display_name in modules_to_test:
    try:
        importlib.import_module(module_name)
        print(f'✅ {display_name}')
        success_count += 1
    except ImportError as e:
        print(f'❌ {display_name}: {e}')
        failed_modules.append(display_name)

print(f'\\n📊 RÉSULTAT: {success_count}/{len(modules_to_test)} modules disponibles')

if failed_modules:
    print(f'❌ Modules manquants: {failed_modules}')
    sys.exit(1)
else:
    print('✅ Tous les modules sont disponibles')
"

if [ $? -ne 0 ]; then
    log_error "Modules manquants détectés, nouvelle installation..."
    pip install python-dotenv pytz --force-reinstall --no-cache-dir
fi

# 4. TEST CRÉATION APPLICATION FLASK
log_info "4. Test création application Flask..."

python -c "
import sys
import os
sys.path.insert(0, '.')

try:
    print('🔍 TEST CRÉATION APPLICATION FLASK')
    print('==================================')
    
    # Test import backend
    from backend.app import create_app
    print('✅ Import backend.app réussi')
    
    # Test création app
    app = create_app()
    print('✅ Création app Flask réussie')
    print(f'✅ Database URI configurée: {app.config.get(\"SQLALCHEMY_DATABASE_URI\", \"Non défini\")[:50]}...')
    
    # Test contexte application
    with app.app_context():
        print('✅ Contexte application fonctionnel')
        
        # Test initialisation données
        try:
            from backend.utils.init_data import init_default_data
            init_default_data()
            print('✅ Initialisation base de données réussie')
        except Exception as e:
            print(f'⚠️  Initialisation BDD (non critique): {e}')
    
    print('\\n🎉 APPLICATION FLASK PRÊTE !')
            
except Exception as e:
    print(f'❌ Erreur critique: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    log_error "Erreur création application Flask"
    exit 1
fi

# 5. REDÉMARRAGE ET TEST DU SERVICE
log_info "5. Redémarrage et test du service..."

# Redémarrage systemd
systemctl daemon-reload
systemctl start $SERVICE_NAME
systemctl enable $SERVICE_NAME

# Attente du démarrage
sleep 10

# 6. VÉRIFICATION FINALE COMPLÈTE
log_info "6. Vérification finale complète..."

echo ""
echo "🔍 DIAGNOSTIC FINAL COMPLET"
echo "==========================="

# Test du service
echo "Service ntp-monitor:"
if systemctl is-active --quiet $SERVICE_NAME; then
    log_success "✅ Service actif"
    systemctl status $SERVICE_NAME --no-pager -l | head -3
else
    log_error "❌ Service inactif"
    echo "Dernières erreurs détaillées:"
    journalctl -u $SERVICE_NAME -n 10 --no-pager
fi

echo ""
echo "Ports d'écoute:"
if netstat -tlnp 2>/dev/null | grep -q ':5000'; then
    log_success "✅ Port 5000 en écoute"
    netstat -tlnp | grep ':5000'
else
    log_warning "❌ Port 5000 non accessible"
    echo "Tous les ports d'écoute:"
    netstat -tlnp 2>/dev/null | grep python || echo "Aucun port Python actif"
fi

echo ""
echo "Test de connectivité HTTP:"
sleep 5

# Test avec plusieurs endpoints
ENDPOINTS=("/" "/health" "/auth/login")
ACCESS_SUCCESS=false

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -f -s -m 15 "http://localhost:5000$endpoint" > /dev/null 2>&1; then
        log_success "✅ Endpoint $endpoint accessible"
        ACCESS_SUCCESS=true
        break
    fi
done

if [ "$ACCESS_SUCCESS" = false ]; then
    log_warning "❌ Aucun endpoint accessible, test démarrage manuel final..."
    
    # Test manuel avec output détaillé
    timeout 20 bash -c "cd $APP_DIR && source $VENV_PATH/bin/activate && python app.py" &
    PID=$!
    sleep 15
    
    if kill -0 $PID 2>/dev/null; then
        log_success "✅ Démarrage manuel réussi"
        kill $PID 2>/dev/null
        ACCESS_SUCCESS=true
    else
        log_error "❌ Échec démarrage manuel"
    fi
fi

echo ""
echo "📊 RÉSULTATS FINAUX"
echo "=================="

if systemctl is-active --quiet $SERVICE_NAME && netstat -tlnp 2>/dev/null | grep -q ':5000'; then
    log_success "🎉 CORRECTION RÉUSSIE - APPLICATION OPÉRATIONNELLE !"
    echo ""
    echo "🌐 Application disponible sur :"
    echo "   http://79.137.36.66/"
    echo ""
    echo "👤 Comptes utilisateur :"
    echo "   Admin:    admin / admin123"
    echo "   Operator: operator / operator123" 
    echo "   Viewer:   viewer / viewer123"
    echo ""
    echo "📋 Monitoring continu :"
    echo "   journalctl -u ntp-monitor -f"
    echo "   systemctl status ntp-monitor -l"

elif systemctl is-active --quiet $SERVICE_NAME; then
    log_warning "⚠️ Service actif mais port 5000 non encore accessible"
    echo "L'application peut avoir besoin de quelques minutes supplémentaires pour démarrer complètement."
    echo "Surveillez les logs : journalctl -u ntp-monitor -f"
    
elif [ "$ACCESS_SUCCESS" = true ]; then
    log_warning "⚠️ Application fonctionne manuellement mais pas en service"
    echo "Problème potentiel avec la configuration systemd."
    echo "Vérifiez : systemctl cat ntp-monitor"
    
else
    log_error "❌ Problème persistant"
    echo ""
    echo "🔧 Diagnostic avancé recommandé :"
    echo "   journalctl -u ntp-monitor -f"
    echo "   cd /opt/ntp-monitor && source .venv/bin/activate && python -c 'from backend.app import create_app; print(create_app())'"
    echo ""
    echo "📞 Contact support avec ces informations."
fi

echo ""
echo "📦 Modules Python installés :"
pip list | grep -E "(flask|redis|celery|psutil|ntplib|pymysql|dotenv|pytz)" | head -10

echo ""
echo "📁 Fichiers de configuration :"
echo "   - requirements_complete.txt (tous les modules)"
echo "   - .env (configuration complète)"
echo "   - Service systemd configuré"

deactivate 2>/dev/null || true
log_info "Correction finale terminée." 