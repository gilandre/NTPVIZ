#!/bin/bash
# Script de diagnostic et correction pour erreur 500 Internal Server Error
# NTP Monitor Enterprise - Apache/WSGI/Flask
# Usage: wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/fix-apache-500-error.sh | sudo bash

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Configuration
APP_DIR="/var/www/ntp-monitor-enterprise"
VENV_PATH="$APP_DIR/venv"
WSGI_FILE="$APP_DIR/app.wsgi"
ERROR_LOG="/var/log/apache2/ntp-monitor_error.log"

echo -e "${PURPLE}🔧 DIAGNOSTIC ERREUR 500 - NTP MONITOR ENTERPRISE${NC}\n"

# Fonction de diagnostic des logs
check_error_logs() {
    echo -e "${YELLOW}📋 Analyse des logs Apache...${NC}"
    
    if [ -f "$ERROR_LOG" ]; then
        echo -e "${BLUE}🔍 Dernières erreurs dans les logs :${NC}"
        echo "────────────────────────────────────────────────────────────"
        sudo tail -20 "$ERROR_LOG" | head -10
        echo "────────────────────────────────────────────────────────────"
    else
        echo -e "${RED}❌ Fichier de log $ERROR_LOG non trouvé${NC}"
    fi
    
    echo -e "\n${BLUE}🔍 Erreurs récentes Apache :${NC}"
    sudo tail -5 /var/log/apache2/error.log 2>/dev/null || echo "Pas de logs d'erreur généraux"
}

# Fonction de diagnostic de l'environnement
check_environment() {
    echo -e "\n${YELLOW}🐍 Vérification environnement Python...${NC}"
    
    if [ ! -d "$APP_DIR" ]; then
        echo -e "${RED}❌ Répertoire application non trouvé: $APP_DIR${NC}"
        return 1
    fi
    
    if [ ! -d "$VENV_PATH" ]; then
        echo -e "${RED}❌ Environnement virtuel non trouvé: $VENV_PATH${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Répertoire application OK${NC}"
    echo -e "${GREEN}✅ Environnement virtuel OK${NC}"
    
    # Test de l'activation de l'environnement virtuel
    cd "$APP_DIR"
    if sudo -u ntpmonitor ./venv/bin/python --version; then
        echo -e "${GREEN}✅ Python dans venv fonctionnel${NC}"
    else
        echo -e "${RED}❌ Problème avec Python dans venv${NC}"
        return 1
    fi
}

# Fonction de test des imports Flask
test_flask_imports() {
    echo -e "\n${YELLOW}📦 Test des imports Flask...${NC}"
    
    cd "$APP_DIR"
    
    # Test import Flask
    if sudo -u ntpmonitor ./venv/bin/python -c "import flask; print('✅ Flask OK')"; then
        echo -e "${GREEN}✅ Flask importé correctement${NC}"
    else
        echo -e "${RED}❌ Erreur import Flask${NC}"
        return 1
    fi
    
    # Test import SQLAlchemy
    if sudo -u ntpmonitor ./venv/bin/python -c "import flask_sqlalchemy; print('✅ Flask-SQLAlchemy OK')"; then
        echo -e "${GREEN}✅ Flask-SQLAlchemy OK${NC}"
    else
        echo -e "${RED}❌ Erreur import Flask-SQLAlchemy${NC}"
        return 1
    fi
    
    # Test import de l'application
    if sudo -u ntpmonitor ./venv/bin/python -c "
import sys
sys.path.insert(0, '$APP_DIR')
try:
    from app import app
    print('✅ Application importée OK')
except Exception as e:
    print(f'❌ Erreur import app: {e}')
    exit(1)
"; then
        echo -e "${GREEN}✅ Application principale importée OK${NC}"
    else
        echo -e "${RED}❌ Erreur import application principale${NC}"
        return 1
    fi
}

# Fonction de vérification du fichier WSGI
check_wsgi_file() {
    echo -e "\n${YELLOW}🌐 Vérification fichier WSGI...${NC}"
    
    if [ ! -f "$WSGI_FILE" ]; then
        echo -e "${RED}❌ Fichier WSGI non trouvé: $WSGI_FILE${NC}"
        echo -e "${YELLOW}📝 Création du fichier WSGI...${NC}"
        
        sudo tee "$WSGI_FILE" > /dev/null << 'EOF'
#!/usr/bin/python3
import sys
import os

# Ajouter le répertoire de l'application au path
sys.path.insert(0, "/var/www/ntp-monitor-enterprise/")

# Activer l'environnement virtuel (nouvelle méthode)
import site
site.addsitedir('/var/www/ntp-monitor-enterprise/venv/lib/python3.12/site-packages')

try:
    from app import app as application
except ImportError as e:
    # Log l'erreur pour débogage
    import logging
    logging.basicConfig(filename='/var/log/apache2/wsgi-error.log', level=logging.ERROR)
    logging.error(f"Erreur import dans WSGI: {e}")
    raise

if __name__ == "__main__":
    application.run()
EOF
        
        sudo chmod +x "$WSGI_FILE"
        sudo chown ntpmonitor:www-data "$WSGI_FILE"
        echo -e "${GREEN}✅ Fichier WSGI créé${NC}"
    else
        echo -e "${GREEN}✅ Fichier WSGI existe${NC}"
    fi
    
    # Test du fichier WSGI
    echo -e "${YELLOW}🧪 Test du fichier WSGI...${NC}"
    cd "$APP_DIR"
    if sudo -u ntpmonitor ./venv/bin/python app.wsgi; then
        echo -e "${GREEN}✅ Fichier WSGI fonctionne${NC}"
    else
        echo -e "${RED}❌ Erreur dans le fichier WSGI${NC}"
        return 1
    fi
}

# Fonction de vérification de la base de données
check_database() {
    echo -e "\n${YELLOW}🗃️ Vérification base de données...${NC}"
    
    cd "$APP_DIR"
    
    if sudo -u ntpmonitor ./venv/bin/python init_database.py check; then
        echo -e "${GREEN}✅ Base de données OK${NC}"
    else
        echo -e "${YELLOW}⚠️ Problème avec la base de données, réinitialisation...${NC}"
        sudo -u ntpmonitor ./venv/bin/python init_database.py init
        echo -e "${GREEN}✅ Base de données réinitialisée${NC}"
    fi
}

# Fonction de vérification des permissions
check_permissions() {
    echo -e "\n${YELLOW}🔐 Vérification des permissions...${NC}"
    
    # Corriger les permissions
    sudo chown -R ntpmonitor:www-data "$APP_DIR"
    sudo chmod -R 755 "$APP_DIR"
    sudo chmod -R 644 "$APP_DIR/frontend/static/"
    sudo chmod +x "$APP_DIR/app.py"
    sudo chmod +x "$WSGI_FILE"
    
    # Permissions spéciales pour les dossiers sensibles
    sudo chmod 775 "$APP_DIR/logs" 2>/dev/null || sudo mkdir -p "$APP_DIR/logs" && sudo chmod 775 "$APP_DIR/logs"
    sudo chmod 775 "$APP_DIR/instance" 2>/dev/null || sudo mkdir -p "$APP_DIR/instance" && sudo chmod 775 "$APP_DIR/instance"
    
    echo -e "${GREEN}✅ Permissions corrigées${NC}"
}

# Fonction de vérification de la configuration Apache
check_apache_config() {
    echo -e "\n${YELLOW}⚙️ Vérification configuration Apache...${NC}"
    
    # Vérifier que le module WSGI est activé
    if sudo a2enmod wsgi; then
        echo -e "${GREEN}✅ Module WSGI activé${NC}"
    else
        echo -e "${RED}❌ Problème avec le module WSGI${NC}"
    fi
    
    # Test de la configuration
    if sudo apache2ctl configtest; then
        echo -e "${GREEN}✅ Configuration Apache valide${NC}"
    else
        echo -e "${RED}❌ Erreur dans la configuration Apache${NC}"
        return 1
    fi
}

# Fonction de création d'un script de test manuel
create_test_script() {
    echo -e "\n${YELLOW}📝 Création script de test manuel...${NC}"
    
    sudo tee "$APP_DIR/test_app.py" > /dev/null << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Configuration du path
sys.path.insert(0, '/var/www/ntp-monitor-enterprise')
os.chdir('/var/www/ntp-monitor-enterprise')

try:
    print("🧪 Test de l'application NTP Monitor Enterprise")
    print("=" * 50)
    
    # Test 1: Import des modules
    print("1. Test imports...")
    import flask
    import flask_sqlalchemy
    import flask_socketio
    print("   ✅ Flask modules OK")
    
    # Test 2: Import de l'application
    print("2. Test import application...")
    from app import app
    print("   ✅ Application OK")
    
    # Test 3: Configuration Flask
    print("3. Test configuration Flask...")
    with app.app_context():
        print(f"   📋 Mode debug: {app.config.get('DEBUG', False)}")
        print(f"   📋 Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Non configuré')}")
        print("   ✅ Configuration OK")
    
    # Test 4: Base de données
    print("4. Test base de données...")
    from backend.app import db
    with app.app_context():
        db.create_all()
        print("   ✅ Base de données OK")
    
    print("\n🎉 TOUS LES TESTS RÉUSSIS !")
    print("L'application devrait fonctionner correctement.")
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF
    
    sudo chmod +x "$APP_DIR/test_app.py"
    sudo chown ntpmonitor:www-data "$APP_DIR/test_app.py"
    
    echo -e "${GREEN}✅ Script de test créé: $APP_DIR/test_app.py${NC}"
}

# Fonction principale de diagnostic et correction
main() {
    echo -e "${BLUE}🚀 Début du diagnostic complet...${NC}\n"
    
    # 1. Analyse des logs
    check_error_logs
    
    # 2. Vérification environnement
    if ! check_environment; then
        echo -e "${RED}❌ Erreur environnement critique${NC}"
        exit 1
    fi
    
    # 3. Vérification permissions
    check_permissions
    
    # 4. Test des imports Flask
    if ! test_flask_imports; then
        echo -e "${RED}❌ Problème avec les imports Python${NC}"
        echo -e "${YELLOW}💡 Suggestion: Relancez le script de correction setuptools${NC}"
        echo -e "${YELLOW}wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/fix-python312-setuptools.sh | sudo bash${NC}"
        exit 1
    fi
    
    # 5. Vérification fichier WSGI
    if ! check_wsgi_file; then
        echo -e "${RED}❌ Problème avec le fichier WSGI${NC}"
        exit 1
    fi
    
    # 6. Vérification base de données
    check_database
    
    # 7. Vérification configuration Apache
    if ! check_apache_config; then
        echo -e "${RED}❌ Problème avec la configuration Apache${NC}"
        exit 1
    fi
    
    # 8. Création script de test
    create_test_script
    
    # 9. Test de l'application
    echo -e "\n${YELLOW}🧪 Test final de l'application...${NC}"
    cd "$APP_DIR"
    if sudo -u ntpmonitor ./venv/bin/python test_app.py; then
        echo -e "${GREEN}✅ Application testée avec succès${NC}"
    else
        echo -e "${RED}❌ L'application a encore des problèmes${NC}"
        echo -e "${YELLOW}💡 Consultez les logs pour plus de détails${NC}"
    fi
    
    # 10. Redémarrage Apache
    echo -e "\n${YELLOW}🔄 Redémarrage d'Apache...${NC}"
    sudo systemctl restart apache2
    
    if sudo systemctl is-active --quiet apache2; then
        echo -e "${GREEN}✅ Apache redémarré avec succès${NC}"
    else
        echo -e "${RED}❌ Problème avec le redémarrage d'Apache${NC}"
        sudo systemctl status apache2
        exit 1
    fi
    
    # Résultat final
    echo -e "\n${GREEN}🎉 DIAGNOSTIC ET CORRECTION TERMINÉS !${NC}"
    
    SERVER_IP=$(hostname -I | awk '{print $1}')
    echo -e "\n${BLUE}📋 INFORMATIONS D'ACCÈS${NC}"
    echo "────────────────────────────────────────────────────────────"
    echo -e "${YELLOW}🌐 URL Application:${NC} http://$SERVER_IP"
    echo -e "${YELLOW}👤 Utilisateur Admin:${NC} admin"
    echo -e "${YELLOW}🔑 Mot de passe:${NC} admin123"
    
    echo -e "\n${BLUE}🛠️ COMMANDES DE DIAGNOSTIC UTILES${NC}"
    echo "────────────────────────────────────────────────────────────"
    echo -e "${YELLOW}Logs temps réel:${NC} sudo tail -f $ERROR_LOG"
    echo -e "${YELLOW}Test application:${NC} cd $APP_DIR && sudo -u ntpmonitor ./venv/bin/python test_app.py"
    echo -e "${YELLOW}Status Apache:${NC} sudo systemctl status apache2"
    echo -e "${YELLOW}Redémarrer Apache:${NC} sudo systemctl restart apache2"
    
    echo -e "\n${GREEN}🚀 Votre NTP Monitor Enterprise devrait maintenant être accessible !${NC}"
}

# Gestion d'erreur
trap 'echo -e "\n${RED}❌ Erreur détectée durant le diagnostic${NC}"; exit 1' ERR

# Lancement du diagnostic principal
main "$@" 