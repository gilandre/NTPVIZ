#!/bin/bash
# Script de diagnostic avancé pour erreur 500 persistante
# NTP Monitor Enterprise - Deep Debug
# Usage: wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/debug-500-advanced.sh | sudo bash

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
APP_DIR="/var/www/ntp-monitor-enterprise"
VENV_PATH="$APP_DIR/venv"
WSGI_FILE="$APP_DIR/app.wsgi"
ERROR_LOG="/var/log/apache2/ntp-monitor_error.log"
DEBUG_LOG="/tmp/ntp-debug-$(date +%Y%m%d-%H%M%S).log"

echo -e "${PURPLE}🔬 DIAGNOSTIC AVANCÉ ERREUR 500 - NTP MONITOR ENTERPRISE${NC}\n" | tee "$DEBUG_LOG"

# Fonction de capture des logs en temps réel
capture_live_error() {
    echo -e "${YELLOW}🔍 Capture de l'erreur en temps réel...${NC}" | tee -a "$DEBUG_LOG"
    
    # Vider les anciens logs
    sudo truncate -s 0 "$ERROR_LOG" 2>/dev/null || true
    sudo truncate -s 0 /var/log/apache2/error.log 2>/dev/null || true
    
    # Lancer la capture des logs en arrière-plan
    (sudo tail -f "$ERROR_LOG" 2>/dev/null &) 
    (sudo tail -f /var/log/apache2/error.log 2>/dev/null &)
    
    echo -e "${CYAN}💡 Essayez d'accéder à http://79.137.36.66 maintenant...${NC}" | tee -a "$DEBUG_LOG"
    echo -e "${CYAN}💡 Appuyez sur Entrée après avoir testé l'accès${NC}"
    read -r
    
    # Arrêter la capture
    sudo pkill -f "tail -f" 2>/dev/null || true
    
    echo -e "\n${BLUE}📋 ERREURS CAPTURÉES :${NC}" | tee -a "$DEBUG_LOG"
    echo "═══════════════════════════════════════════════════════════════" | tee -a "$DEBUG_LOG"
    
    if [ -f "$ERROR_LOG" ] && [ -s "$ERROR_LOG" ]; then
        echo -e "${RED}🔴 Logs NTP Monitor :${NC}" | tee -a "$DEBUG_LOG"
        sudo cat "$ERROR_LOG" | tee -a "$DEBUG_LOG"
    else
        echo -e "${YELLOW}⚠️ Aucun log spécifique NTP Monitor${NC}" | tee -a "$DEBUG_LOG"
    fi
    
    echo -e "\n${RED}🔴 Logs Apache généraux :${NC}" | tee -a "$DEBUG_LOG"
    sudo tail -20 /var/log/apache2/error.log | tee -a "$DEBUG_LOG"
    
    echo "═══════════════════════════════════════════════════════════════" | tee -a "$DEBUG_LOG"
}

# Test manuel détaillé de l'application
manual_app_test() {
    echo -e "\n${YELLOW}🧪 Test manuel détaillé de l'application...${NC}" | tee -a "$DEBUG_LOG"
    
    cd "$APP_DIR"
    
    # Test 1: Version Python
    echo -e "${BLUE}1. Version Python dans venv :${NC}" | tee -a "$DEBUG_LOG"
    sudo -u ntpmonitor ./venv/bin/python --version 2>&1 | tee -a "$DEBUG_LOG"
    
    # Test 2: Packages installés
    echo -e "\n${BLUE}2. Packages Python installés :${NC}" | tee -a "$DEBUG_LOG"
    sudo -u ntpmonitor ./venv/bin/pip list | head -20 | tee -a "$DEBUG_LOG"
    
    # Test 3: Import Flask détaillé
    echo -e "\n${BLUE}3. Test import Flask détaillé :${NC}" | tee -a "$DEBUG_LOG"
    sudo -u ntpmonitor ./venv/bin/python << 'EOF' 2>&1 | tee -a "$DEBUG_LOG"
try:
    print("  → Import flask...")
    import flask
    print(f"  ✅ Flask {flask.__version__} OK")
    
    print("  → Import flask_sqlalchemy...")
    import flask_sqlalchemy
    print(f"  ✅ Flask-SQLAlchemy OK")
    
    print("  → Import flask_socketio...")
    import flask_socketio
    print(f"  ✅ Flask-SocketIO OK")
    
    print("  → Test des autres imports...")
    import os, sys, logging
    print("  ✅ Imports système OK")
    
except Exception as e:
    print(f"  ❌ ERREUR IMPORT: {e}")
    import traceback
    traceback.print_exc()
EOF
    
    # Test 4: Import de l'application avec détails
    echo -e "\n${BLUE}4. Test import application avec debug :${NC}" | tee -a "$DEBUG_LOG"
    sudo -u ntpmonitor ./venv/bin/python << 'EOF' 2>&1 | tee -a "$DEBUG_LOG"
import sys
import os
sys.path.insert(0, '/var/www/ntp-monitor-enterprise')
os.chdir('/var/www/ntp-monitor-enterprise')

try:
    print("  → Changement de répertoire...")
    print(f"  📁 Répertoire actuel: {os.getcwd()}")
    
    print("  → Vérification fichier app.py...")
    if os.path.exists('app.py'):
        print("  ✅ app.py existe")
    else:
        print("  ❌ app.py manquant")
        sys.exit(1)
    
    print("  → Import de l'application...")
    from app import app
    print("  ✅ Application importée avec succès")
    
    print("  → Test configuration Flask...")
    print(f"  📋 Debug mode: {app.config.get('DEBUG')}")
    print(f"  📋 Secret key: {'***configurée***' if app.config.get('SECRET_KEY') else 'NON CONFIGURÉE'}")
    print(f"  📋 Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'NON CONFIGURÉE')}")
    
    print("  → Test contexte application...")
    with app.app_context():
        print("  ✅ Contexte application OK")
        
        print("  → Test base de données...")
        from backend.app import db
        try:
            db.create_all()
            print("  ✅ Base de données accessible")
        except Exception as e:
            print(f"  ⚠️ Problème BDD: {e}")
    
    print("\n  🎉 APPLICATION SEMBLE FONCTIONNELLE!")
    
except Exception as e:
    print(f"\n  ❌ ERREUR APPLICATION: {e}")
    print("\n  📋 DÉTAILS DE L'ERREUR:")
    import traceback
    traceback.print_exc()
EOF
}

# Test du fichier WSGI avec debug détaillé
test_wsgi_detailed() {
    echo -e "\n${YELLOW}🌐 Test WSGI avec debug détaillé...${NC}" | tee -a "$DEBUG_LOG"
    
    # Afficher le contenu du fichier WSGI
    echo -e "${BLUE}📄 Contenu du fichier WSGI actuel :${NC}" | tee -a "$DEBUG_LOG"
    echo "───────────────────────────────────────────────────────" | tee -a "$DEBUG_LOG"
    cat "$WSGI_FILE" 2>/dev/null | tee -a "$DEBUG_LOG" || echo "❌ Fichier WSGI non trouvé" | tee -a "$DEBUG_LOG"
    echo "───────────────────────────────────────────────────────" | tee -a "$DEBUG_LOG"
    
    # Test du WSGI
    echo -e "\n${BLUE}🧪 Test exécution WSGI :${NC}" | tee -a "$DEBUG_LOG"
    cd "$APP_DIR"
    
    # Créer un fichier WSGI de test avec plus de debug
    sudo tee "$APP_DIR/test_wsgi.py" > /dev/null << 'EOF'
#!/usr/bin/env python3
import sys
import os
import traceback

print("🔍 DEBUG WSGI - Début du test")
print(f"📁 Répertoire de travail: {os.getcwd()}")
print(f"🐍 Version Python: {sys.version}")
print(f"📋 Python path: {sys.path[:3]}...")

try:
    # Ajouter le répertoire de l'application au path
    sys.path.insert(0, "/var/www/ntp-monitor-enterprise/")
    print("✅ Path ajouté")
    
    # Test changement de répertoire
    os.chdir("/var/www/ntp-monitor-enterprise")
    print(f"✅ Répertoire changé vers: {os.getcwd()}")
    
    # Vérifier l'environnement virtuel
    import site
    site.addsitedir('/var/www/ntp-monitor-enterprise/venv/lib/python3.12/site-packages')
    print("✅ Environnement virtuel activé")
    
    # Test imports
    print("🔍 Test des imports...")
    import flask
    print(f"✅ Flask {flask.__version__}")
    
    import flask_sqlalchemy
    print("✅ Flask-SQLAlchemy")
    
    # Import application
    print("🔍 Import de l'application...")
    from app import app as application
    print("✅ Application importée avec succès")
    
    # Test basique de l'application
    print("🔍 Test contexte application...")
    with application.app_context():
        print(f"✅ Contexte OK - Mode debug: {application.config.get('DEBUG')}")
    
    print("\n🎉 WSGI TEST RÉUSSI - L'application devrait fonctionner!")

except Exception as e:
    print(f"\n❌ ERREUR WSGI: {e}")
    print("\n📋 TRACEBACK COMPLET:")
    traceback.print_exc()
    print("\n🔍 INFORMATIONS DE DEBUG:")
    print(f"  - Répertoire actuel: {os.getcwd()}")
    print(f"  - Fichiers présents: {os.listdir('.')[:10]}")
    print(f"  - Python path: {sys.path[:3]}")
EOF
    
    chmod +x "$APP_DIR/test_wsgi.py"
    chown ntpmonitor:www-data "$APP_DIR/test_wsgi.py"
    
    echo -e "${CYAN}Exécution du test WSGI...${NC}" | tee -a "$DEBUG_LOG"
    sudo -u ntpmonitor ./venv/bin/python test_wsgi.py 2>&1 | tee -a "$DEBUG_LOG"
}

# Test configuration Apache détaillé
test_apache_config() {
    echo -e "\n${YELLOW}⚙️ Test configuration Apache détaillé...${NC}" | tee -a "$DEBUG_LOG"
    
    echo -e "${BLUE}📋 Sites Apache activés :${NC}" | tee -a "$DEBUG_LOG"
    sudo a2ensite | tee -a "$DEBUG_LOG"
    
    echo -e "\n${BLUE}📋 Modules Apache activés :${NC}" | tee -a "$DEBUG_LOG"
    sudo apache2ctl -M | grep wsgi | tee -a "$DEBUG_LOG"
    
    echo -e "\n${BLUE}📋 Configuration VirtualHost :${NC}" | tee -a "$DEBUG_LOG"
    echo "───────────────────────────────────────────────────────" | tee -a "$DEBUG_LOG"
    sudo cat /etc/apache2/sites-available/ntp-monitor.conf 2>/dev/null | tee -a "$DEBUG_LOG" || echo "❌ Configuration VirtualHost non trouvée" | tee -a "$DEBUG_LOG"
    echo "───────────────────────────────────────────────────────" | tee -a "$DEBUG_LOG"
    
    echo -e "\n${BLUE}🧪 Test configuration Apache :${NC}" | tee -a "$DEBUG_LOG"
    sudo apache2ctl configtest 2>&1 | tee -a "$DEBUG_LOG"
    
    echo -e "\n${BLUE}📊 Status Apache :${NC}" | tee -a "$DEBUG_LOG"
    sudo systemctl status apache2 --no-pager | tee -a "$DEBUG_LOG"
}

# Correction avancée basée sur les erreurs trouvées
advanced_fixes() {
    echo -e "\n${YELLOW}🔧 Application des corrections avancées...${NC}" | tee -a "$DEBUG_LOG"
    
    # Fix 1: Recréer le fichier WSGI avec maximum de debug
    echo -e "${BLUE}1. Création fichier WSGI optimisé...${NC}" | tee -a "$DEBUG_LOG"
    sudo tee "$WSGI_FILE" > /dev/null << 'EOF'
#!/usr/bin/python3
import sys
import os
import logging

# Configuration du logging pour debug
logging.basicConfig(
    filename='/var/log/apache2/wsgi-debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('WSGI_DEBUG')

try:
    logger.info("=== DÉBUT WSGI DEBUG ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Changer vers le répertoire de l'application
    os.chdir("/var/www/ntp-monitor-enterprise")
    logger.info(f"Changed to: {os.getcwd()}")
    
    # Ajouter le répertoire de l'application au path
    sys.path.insert(0, "/var/www/ntp-monitor-enterprise/")
    logger.info("Added app directory to path")
    
    # Activer l'environnement virtuel
    import site
    venv_path = '/var/www/ntp-monitor-enterprise/venv/lib/python3.12/site-packages'
    site.addsitedir(venv_path)
    logger.info(f"Activated virtual env: {venv_path}")
    
    # Import de l'application
    logger.info("Importing Flask application...")
    from app import app as application
    logger.info("✅ Application imported successfully")
    
    # Test rapide de l'application
    with application.app_context():
        logger.info(f"Application context OK - Debug: {application.config.get('DEBUG')}")
    
    logger.info("=== WSGI SETUP COMPLETE ===")

except Exception as e:
    logger.error(f"❌ WSGI ERROR: {e}")
    logger.error("Traceback:", exc_info=True)
    raise

if __name__ == "__main__":
    application.run()
EOF
    
    sudo chmod +x "$WSGI_FILE"
    sudo chown ntpmonitor:www-data "$WSGI_FILE"
    echo -e "${GREEN}✅ Fichier WSGI optimisé créé${NC}" | tee -a "$DEBUG_LOG"
    
    # Fix 2: Vérification et correction des permissions étendues
    echo -e "\n${BLUE}2. Correction permissions étendues...${NC}" | tee -a "$DEBUG_LOG"
    cd "$APP_DIR"
    sudo chown -R ntpmonitor:www-data ./
    sudo find . -type f -name "*.py" -exec chmod 644 {} \;
    sudo find . -type d -exec chmod 755 {} \;
    sudo chmod +x app.py app.wsgi
    sudo mkdir -p logs instance
    sudo chmod 775 logs instance
    sudo touch logs/app.log
    sudo chmod 664 logs/app.log
    echo -e "${GREEN}✅ Permissions corrigées${NC}" | tee -a "$DEBUG_LOG"
    
    # Fix 3: Configuration Flask pour production
    echo -e "\n${BLUE}3. Configuration Flask pour production...${NC}" | tee -a "$DEBUG_LOG"
    
    # Créer un fichier de configuration de production
    sudo tee "$APP_DIR/production_config.py" > /dev/null << 'EOF'
import os

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key-change-this'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/ntp_monitor_prod.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    TESTING = False
    
    # Configuration logging
    LOG_TO_STDOUT = False
    LOG_LEVEL = 'INFO'
    
    # Configuration NTP
    NTP_MONITORING_INTERVAL = 60
    ALERT_CHECK_INTERVAL = 300
EOF
    
    sudo chown ntpmonitor:www-data "$APP_DIR/production_config.py"
    echo -e "${GREEN}✅ Configuration production ajoutée${NC}" | tee -a "$DEBUG_LOG"
    
    # Fix 4: Réinitialisation base de données avec gestion d'erreurs
    echo -e "\n${BLUE}4. Réinitialisation base de données...${NC}" | tee -a "$DEBUG_LOG"
    sudo -u ntpmonitor ./venv/bin/python << 'EOF' 2>&1 | tee -a "$DEBUG_LOG"
import sys
sys.path.insert(0, '/var/www/ntp-monitor-enterprise')
import os
os.chdir('/var/www/ntp-monitor-enterprise')

try:
    from app import app
    from backend.app import db
    
    with app.app_context():
        # Créer toutes les tables
        db.create_all()
        print("✅ Base de données initialisée")
        
        # Test de connexion avec syntaxe SQLAlchemy 2.x
        from sqlalchemy import text
        with db.engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).fetchone()
            print("✅ Connexion base de données OK")
        
except Exception as e:
    print(f"❌ Erreur base de données: {e}")
    # Essayer de créer le répertoire instance
    os.makedirs('instance', exist_ok=True)
    print("✅ Répertoire instance créé")
EOF
}

# Test final après corrections
final_test() {
    echo -e "\n${YELLOW}🎯 Test final après corrections...${NC}" | tee -a "$DEBUG_LOG"
    
    # Redémarrer Apache
    echo -e "${BLUE}🔄 Redémarrage Apache...${NC}" | tee -a "$DEBUG_LOG"
    sudo systemctl restart apache2
    sleep 3
    
    if sudo systemctl is-active --quiet apache2; then
        echo -e "${GREEN}✅ Apache redémarré avec succès${NC}" | tee -a "$DEBUG_LOG"
    else
        echo -e "${RED}❌ Problème redémarrage Apache${NC}" | tee -a "$DEBUG_LOG"
        sudo systemctl status apache2 --no-pager | tee -a "$DEBUG_LOG"
        return 1
    fi
    
    # Test automatique de l'application
    echo -e "\n${BLUE}🧪 Test automatique de l'application...${NC}" | tee -a "$DEBUG_LOG"
    
    # Test avec curl
    if curl -s -I http://localhost | head -1 | grep -q "200 OK"; then
        echo -e "${GREEN}✅ Application répond avec succès !${NC}" | tee -a "$DEBUG_LOG"
        curl -s -I http://localhost | head -5 | tee -a "$DEBUG_LOG"
        return 0
    elif curl -s -I http://localhost | head -1 | grep -q "500"; then
        echo -e "${RED}❌ Erreur 500 persiste${NC}" | tee -a "$DEBUG_LOG"
        return 1
    else
        echo -e "${YELLOW}⚠️ Réponse inattendue${NC}" | tee -a "$DEBUG_LOG"
        curl -s -I http://localhost | head -5 | tee -a "$DEBUG_LOG"
        return 1
    fi
}

# Fonction principale
main() {
    echo -e "${BLUE}🚀 Début du diagnostic avancé...${NC}\n" | tee -a "$DEBUG_LOG"
    
    # Étape 1: Capture erreur en temps réel
    capture_live_error
    
    # Étape 2: Test manuel détaillé
    manual_app_test
    
    # Étape 3: Test WSGI détaillé
    test_wsgi_detailed
    
    # Étape 4: Test configuration Apache
    test_apache_config
    
    # Étape 5: Corrections avancées
    advanced_fixes
    
    # Étape 6: Test final
    if final_test; then
        echo -e "\n${GREEN}🎉 SUCCESS! L'application fonctionne maintenant !${NC}" | tee -a "$DEBUG_LOG"
        
        SERVER_IP=$(hostname -I | awk '{print $1}')
        echo -e "\n${CYAN}📋 ACCÈS À L'APPLICATION${NC}" | tee -a "$DEBUG_LOG"
        echo "═══════════════════════════════════════════════════════" | tee -a "$DEBUG_LOG"
        echo -e "${YELLOW}🌐 URL:${NC} http://$SERVER_IP" | tee -a "$DEBUG_LOG"
        echo -e "${YELLOW}👤 Admin:${NC} admin" | tee -a "$DEBUG_LOG"
        echo -e "${YELLOW}🔑 Password:${NC} admin123" | tee -a "$DEBUG_LOG"
        echo "═══════════════════════════════════════════════════════" | tee -a "$DEBUG_LOG"
    else
        echo -e "\n${RED}❌ L'erreur 500 persiste - analyse requise${NC}" | tee -a "$DEBUG_LOG"
        
        echo -e "\n${CYAN}🔍 LOGS DE DEBUG DISPONIBLES${NC}" | tee -a "$DEBUG_LOG"
        echo "═══════════════════════════════════════════════════════" | tee -a "$DEBUG_LOG"
        echo -e "${YELLOW}📄 Log principal:${NC} $DEBUG_LOG" | tee -a "$DEBUG_LOG"
        echo -e "${YELLOW}📄 Log WSGI:${NC} /var/log/apache2/wsgi-debug.log" | tee -a "$DEBUG_LOG"
        echo -e "${YELLOW}📄 Log Apache:${NC} /var/log/apache2/ntp-monitor_error.log" | tee -a "$DEBUG_LOG"
        echo "═══════════════════════════════════════════════════════" | tee -a "$DEBUG_LOG"
        
        echo -e "\n${YELLOW}💡 PROCHAINES ÉTAPES${NC}" | tee -a "$DEBUG_LOG"
        echo "1. Examinez les logs de debug ci-dessus" | tee -a "$DEBUG_LOG"
        echo "2. Partagez le contenu du fichier $DEBUG_LOG" | tee -a "$DEBUG_LOG"
        echo "3. Vérifiez les logs WSGI en temps réel :" | tee -a "$DEBUG_LOG"
        echo "   sudo tail -f /var/log/apache2/wsgi-debug.log" | tee -a "$DEBUG_LOG"
    fi
    
    echo -e "\n${BLUE}📋 Log complet sauvegardé dans: $DEBUG_LOG${NC}"
}

# Gestion d'erreur
trap 'echo -e "\n${RED}❌ Erreur durant le diagnostic avancé${NC}"; exit 1' ERR

# Lancement du diagnostic
main "$@" 