#!/bin/bash
# Script de correction compatibilité Flask-Login / Werkzeug
# NTP Monitor Enterprise - Fix ImportError url_decode
# Usage: wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/fix-flask-login-werkzeug.sh | sudo bash

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

echo -e "${PURPLE}🔧 CORRECTION COMPATIBILITÉ FLASK-LOGIN / WERKZEUG${NC}\n"

# Fonction de diagnostic des versions actuelles
check_current_versions() {
    echo -e "${YELLOW}📋 Versions actuelles installées...${NC}"
    
    cd "$APP_DIR"
    echo -e "${BLUE}🔍 Versions Python packages :${NC}"
    sudo -u ntpmonitor ./venv/bin/pip list | grep -E "(Flask|Werkzeug|flask-login)" || echo "Packages non trouvés"
    
    echo -e "\n${BLUE}🧪 Test import Werkzeug :${NC}"
    sudo -u ntpmonitor ./venv/bin/python << 'EOF'
try:
    import werkzeug
    print(f"✅ Werkzeug version: {werkzeug.__version__}")
    
    # Test de l'import problématique
    try:
        from werkzeug.urls import url_decode
        print("✅ url_decode disponible dans werkzeug.urls")
    except ImportError:
        print("❌ url_decode NON disponible dans werkzeug.urls")
        
        # Vérifier où il se trouve maintenant
        try:
            from werkzeug.http import url_decode
            print("✅ url_decode trouvé dans werkzeug.http")
        except ImportError:
            try:
                from werkzeug.utils import url_decode
                print("✅ url_decode trouvé dans werkzeug.utils")
            except ImportError:
                print("❌ url_decode introuvable")
    
except ImportError as e:
    print(f"❌ Erreur import Werkzeug: {e}")
EOF
}

# Fonction de correction avec versions compatibles
fix_compatibility() {
    echo -e "\n${YELLOW}🔧 Installation des versions compatibles...${NC}"
    
    cd "$APP_DIR"
    
    # Solution 1: Versions testées et compatibles
    echo -e "${BLUE}📦 Installation versions compatibles Flask ecosystem...${NC}"
    
    # Désinstaller les versions problématiques
    sudo -u ntpmonitor ./venv/bin/pip uninstall -y flask-login werkzeug flask flask-sqlalchemy flask-socketio 2>/dev/null || true
    
    # Installer versions spécifiques compatibles
    echo -e "${CYAN}⬇️ Installation Flask ecosystem compatible...${NC}"
    
    # Versions testées compatibles (Flask 2.x avec Werkzeug 2.x)
    sudo -u ntpmonitor ./venv/bin/pip install \
        'Werkzeug==2.3.7' \
        'Flask==2.3.3' \
        'Flask-Login==0.6.3' \
        'Flask-SQLAlchemy==3.0.5' \
        'Flask-SocketIO==5.3.6' \
        --no-cache-dir --force-reinstall
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Versions compatibles installées${NC}"
    else
        echo -e "${RED}❌ Erreur installation - tentative solution alternative${NC}"
        
        # Solution alternative avec versions plus anciennes
        echo -e "${YELLOW}🔄 Tentative avec versions Flask 2.2.x...${NC}"
        sudo -u ntpmonitor ./venv/bin/pip install \
            'Werkzeug==2.2.3' \
            'Flask==2.2.5' \
            'Flask-Login==0.6.2' \
            'Flask-SQLAlchemy==3.0.5' \
            'Flask-SocketIO==5.3.4' \
            --no-cache-dir --force-reinstall
    fi
}

# Fonction de test après correction
test_after_fix() {
    echo -e "\n${YELLOW}🧪 Test après correction...${NC}"
    
    cd "$APP_DIR"
    
    # Test 1: Import Flask-Login
    echo -e "${BLUE}1. Test import Flask-Login...${NC}"
    if sudo -u ntpmonitor ./venv/bin/python -c "
import flask_login
print(f'✅ Flask-Login {flask_login.__version__} OK')
" 2>/dev/null; then
        echo -e "${GREEN}✅ Flask-Login fonctionne${NC}"
    else
        echo -e "${RED}❌ Flask-Login encore problématique${NC}"
        return 1
    fi
    
    # Test 2: Import application complète
    echo -e "\n${BLUE}2. Test import application...${NC}"
    if sudo -u ntpmonitor ./venv/bin/python -c "
import sys
sys.path.insert(0, '/var/www/ntp-monitor-enterprise')
from app import app
print('✅ Application importée avec succès')
" 2>/dev/null; then
        echo -e "${GREEN}✅ Application fonctionne${NC}"
        return 0
    else
        echo -e "${RED}❌ Application encore problématique${NC}"
        echo -e "${YELLOW}Détails de l'erreur :${NC}"
        sudo -u ntpmonitor ./venv/bin/python -c "
import sys
sys.path.insert(0, '/var/www/ntp-monitor-enterprise')
try:
    from app import app
    print('Application OK')
except Exception as e:
    print(f'Erreur: {e}')
    import traceback
    traceback.print_exc()
"
        return 1
    fi
}

# Fonction de mise à jour du requirements.txt
update_requirements() {
    echo -e "\n${YELLOW}📝 Mise à jour requirements.txt...${NC}"
    
    cd "$APP_DIR"
    
    # Backup de l'ancien requirements.txt
    if [ -f "requirements.txt" ]; then
        sudo cp requirements.txt requirements.txt.backup
        echo -e "${BLUE}💾 Backup de requirements.txt créé${NC}"
    fi
    
    # Générer nouveau requirements.txt avec versions fixées
    echo -e "${BLUE}📋 Génération nouveau requirements.txt...${NC}"
    sudo -u ntpmonitor ./venv/bin/pip freeze > requirements_new.txt
    
    # Créer requirements.txt avec versions spécifiques
    sudo tee requirements.txt > /dev/null << 'EOF'
# Flask ecosystem avec versions compatibles
Flask==2.3.3
Werkzeug==2.3.7
Flask-Login==0.6.3
Flask-SQLAlchemy==3.0.5
Flask-SocketIO==5.3.6

# Base de données
SQLAlchemy==2.0.23

# Utilitaires
python-socketio==5.9.0
python-engineio==4.7.1
requests==2.31.0
python-dateutil==2.8.2

# Production
eventlet==0.33.3
gunicorn==21.2.0

# Optionnel (si nécessaire)
redis==5.0.1
psutil==5.9.6
EOF
    
    sudo chown ntpmonitor:www-data requirements.txt
    echo -e "${GREEN}✅ requirements.txt mis à jour avec versions compatibles${NC}"
}

# Fonction principale
main() {
    echo -e "${BLUE}🚀 Début de la correction Flask-Login / Werkzeug...${NC}\n"
    
    # 1. Diagnostic des versions actuelles
    check_current_versions
    
    # 2. Correction avec versions compatibles
    fix_compatibility
    
    # 3. Test après correction
    if test_after_fix; then
        echo -e "\n${GREEN}🎉 CORRECTION RÉUSSIE !${NC}"
        
        # 4. Mise à jour requirements.txt
        update_requirements
        
        # 5. Redémarrage Apache
        echo -e "\n${YELLOW}🔄 Redémarrage Apache...${NC}"
        sudo systemctl restart apache2
        
        if sudo systemctl is-active --quiet apache2; then
            echo -e "${GREEN}✅ Apache redémarré avec succès${NC}"
        else
            echo -e "${RED}❌ Problème redémarrage Apache${NC}"
            sudo systemctl status apache2 --no-pager
            return 1
        fi
        
        # Test final
        echo -e "\n${YELLOW}🧪 Test final de l'application...${NC}"
        sleep 3
        
        if curl -s -I http://localhost | head -1 | grep -q "200 OK"; then
            echo -e "${GREEN}✅ APPLICATION FONCTIONNE !${NC}"
            
            SERVER_IP=$(hostname -I | awk '{print $1}')
            echo -e "\n${CYAN}🎯 ACCÈS À L'APPLICATION${NC}"
            echo "════════════════════════════════════════════════════════════"
            echo -e "${YELLOW}🌐 URL:${NC} http://$SERVER_IP"
            echo -e "${YELLOW}👤 Admin:${NC} admin"
            echo -e "${YELLOW}🔑 Password:${NC} admin123"
            echo "════════════════════════════════════════════════════════════"
            
        elif curl -s -I http://localhost | head -1 | grep -q "500"; then
            echo -e "${YELLOW}⚠️ Erreur 500 persiste - vérification des logs...${NC}"
            sudo tail -5 /var/log/apache2/ntp-monitor_error.log
            return 1
        else
            echo -e "${YELLOW}⚠️ Réponse inattendue du serveur${NC}"
            curl -s -I http://localhost | head -3
            return 1
        fi
        
    else
        echo -e "\n${RED}❌ La correction n'a pas résolu le problème${NC}"
        echo -e "${YELLOW}💡 Informations de debug :${NC}"
        echo "1. Vérifiez les versions installées :"
        echo "   cd $APP_DIR && sudo -u ntpmonitor ./venv/bin/pip list | grep -E '(Flask|Werkzeug|flask-login)'"
        echo "2. Testez l'import manuellement :"
        echo "   cd $APP_DIR && sudo -u ntpmonitor ./venv/bin/python -c 'import flask_login; print(\"OK\")'"
        return 1
    fi
}

# Gestion d'erreur
trap 'echo -e "\n${RED}❌ Erreur durant la correction${NC}"; exit 1' ERR

# Lancement de la correction
main "$@" 