#!/bin/bash
# Script de diagnostic rapide pour erreur 500
# Usage: wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/quick-debug.sh | sudo bash

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 DIAGNOSTIC RAPIDE - ERREUR 500${NC}\n"

APP_DIR="/var/www/ntp-monitor-enterprise"

# 1. Vérifier les logs Apache
echo -e "${YELLOW}📋 Dernières erreurs Apache :${NC}"
echo "════════════════════════════════════════════════════════"
sudo tail -10 /var/log/apache2/ntp-monitor_error.log 2>/dev/null || echo "Pas de logs spécifiques"
sudo tail -10 /var/log/apache2/error.log 2>/dev/null || echo "Pas de logs généraux"
echo "════════════════════════════════════════════════════════"

# 2. Test de l'application Python
echo -e "\n${YELLOW}🐍 Test de l'application Python :${NC}"
cd "$APP_DIR"
if sudo -u ntpmonitor ./venv/bin/python -c "
import sys
sys.path.insert(0, '/var/www/ntp-monitor-enterprise')
from app import app
print('✅ Application OK')
" 2>/dev/null; then
    echo -e "${GREEN}✅ L'application Python fonctionne${NC}"
else
    echo -e "${RED}❌ Erreur dans l'application Python${NC}"
    echo -e "${YELLOW}Détails de l'erreur :${NC}"
    sudo -u ntpmonitor ./venv/bin/python -c "
import sys
sys.path.insert(0, '/var/www/ntp-monitor-enterprise')
try:
    from app import app
    print('Application importée avec succès')
except Exception as e:
    print(f'Erreur : {e}')
    import traceback
    traceback.print_exc()
"
fi

# 3. Test du fichier WSGI
echo -e "\n${YELLOW}🌐 Contenu du fichier WSGI :${NC}"
echo "════════════════════════════════════════════════════════"
cat "$APP_DIR/app.wsgi" 2>/dev/null || echo "❌ Fichier WSGI non trouvé"
echo "════════════════════════════════════════════════════════"

# 4. Test de la configuration Apache
echo -e "\n${YELLOW}⚙️ Configuration Apache :${NC}"
if sudo apache2ctl configtest 2>/dev/null; then
    echo -e "${GREEN}✅ Configuration Apache valide${NC}"
else
    echo -e "${RED}❌ Erreur dans la configuration Apache${NC}"
    sudo apache2ctl configtest
fi

# 5. Status des services
echo -e "\n${YELLOW}📊 Status des services :${NC}"
if sudo systemctl is-active --quiet apache2; then
    echo -e "${GREEN}✅ Apache2 actif${NC}"
else
    echo -e "${RED}❌ Apache2 inactif${NC}"
fi

# 6. Test de connectivité local
echo -e "\n${YELLOW}🌐 Test de connectivité locale :${NC}"
if curl -s -I http://localhost | head -1 | grep -q "200 OK"; then
    echo -e "${GREEN}✅ Application accessible en local${NC}"
elif curl -s -I http://localhost | head -1 | grep -q "500"; then
    echo -e "${RED}❌ Erreur 500 confirmée${NC}"
else
    echo -e "${YELLOW}⚠️ Réponse inattendue :${NC}"
    curl -s -I http://localhost | head -1
fi

# Recommandations
echo -e "\n${BLUE}💡 RECOMMANDATIONS :${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ SOLUTION AUTOMATIQUE :${NC}"
echo "wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/debug-500-advanced.sh | sudo bash"
echo ""
echo -e "${YELLOW}🔍 LOGS EN TEMPS RÉEL :${NC}"
echo "sudo tail -f /var/log/apache2/ntp-monitor_error.log"
echo ""
echo -e "${BLUE}🧪 TEST MANUEL :${NC}"
echo "cd /var/www/ntp-monitor-enterprise"
echo "sudo -u ntpmonitor ./venv/bin/python app.wsgi"
echo "═══════════════════════════════════════════════════════════════" 