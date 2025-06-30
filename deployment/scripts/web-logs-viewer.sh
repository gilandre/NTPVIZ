#!/bin/bash
# Script de visualisation des logs web en temps réel
# NTP Monitor Enterprise - Web Logs Viewer
# Usage: wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/web-logs-viewer.sh | sudo bash

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${PURPLE}📊 VISUALISATION LOGS WEB - NTP MONITOR ENTERPRISE${NC}\n"

# Configuration
APP_DIR="/var/www/ntp-monitor-enterprise"
SERVER_IP=$(hostname -I | awk '{print $1}')

echo -e "${BLUE}🌐 Application Web: ${NC}http://$SERVER_IP"
echo -e "${BLUE}📁 Répertoire App: ${NC}$APP_DIR"
echo ""

# Fonction d'affichage des logs récents
show_recent_logs() {
    echo -e "${YELLOW}📋 LOGS RÉCENTS (Dernières 20 lignes)${NC}"
    echo "═══════════════════════════════════════════════════════════════"
    
    echo -e "${CYAN}🔴 Logs Apache NTP Monitor:${NC}"
    if [ -f "/var/log/apache2/ntp-monitor_error.log" ]; then
        sudo tail -20 /var/log/apache2/ntp-monitor_error.log | sed 's/^/  /'
    else
        echo "  ❌ Fichier de log non trouvé"
    fi
    
    echo -e "\n${CYAN}🔴 Logs Apache Généraux:${NC}"
    sudo tail -10 /var/log/apache2/error.log | sed 's/^/  /'
    
    echo -e "\n${CYAN}🔵 Logs d'Accès Apache:${NC}"
    sudo tail -10 /var/log/apache2/access.log | sed 's/^/  /'
    
    echo "═══════════════════════════════════════════════════════════════"
}

# Fonction de test des fichiers statiques
test_static_files() {
    echo -e "\n${YELLOW}🧪 TEST DES FICHIERS STATIQUES${NC}"
    echo "═══════════════════════════════════════════════════════════════"
    
    # Tests des fichiers CSS/JS principaux
    local files=(
        "/static/css/vendor/bootstrap.min.css"
        "/static/css/vendor/fontawesome.min.css"
        "/static/js/vendor/bootstrap.bundle.min.js"
        "/static/css/app.css"
        "/static/js/app.js"
    )
    
    for file in "${files[@]}"; do
        echo -e "${BLUE}🔍 Test: ${NC}$file"
        
        # Test avec curl
        local response=$(curl -s -I "http://localhost$file" | head -1)
        if echo "$response" | grep -q "200 OK"; then
            echo -e "  ✅ ${GREEN}Accessible${NC}"
        elif echo "$response" | grep -q "403"; then
            echo -e "  ❌ ${RED}403 Forbidden${NC}"
        elif echo "$response" | grep -q "404"; then
            echo -e "  ❌ ${RED}404 Not Found${NC}"
        else
            echo -e "  ⚠️ ${YELLOW}Réponse: $response${NC}"
        fi
        
        # Vérifier existence physique du fichier
        local physical_path="$APP_DIR/frontend$file"
        if [ -f "$physical_path" ]; then
            echo -e "  📁 ${GREEN}Fichier existe${NC}"
            ls -la "$physical_path" | sed 's/^/    /'
        else
            echo -e "  📁 ${RED}Fichier manquant${NC}"
        fi
        echo ""
    done
    
    echo "═══════════════════════════════════════════════════════════════"
}

# Fonction de test de connectivité web
test_web_connectivity() {
    echo -e "\n${YELLOW}🌐 TEST DE CONNECTIVITÉ WEB${NC}"
    echo "═══════════════════════════════════════════════════════════════"
    
    # Test page principale
    echo -e "${BLUE}🏠 Test page d'accueil:${NC}"
    local main_response=$(curl -s -I http://localhost | head -1)
    echo "  Réponse: $main_response"
    
    # Test page de login
    echo -e "\n${BLUE}🔐 Test page de connexion:${NC}"
    local login_response=$(curl -s -I http://localhost/auth/login | head -1)
    echo "  Réponse: $login_response"
    
    # Test API
    echo -e "\n${BLUE}🔌 Test API status:${NC}"
    local api_response=$(curl -s -I http://localhost/api/status | head -1)
    echo "  Réponse: $api_response"
    
    echo "═══════════════════════════════════════════════════════════════"
}

# Fonction de diagnostic des permissions
check_permissions() {
    echo -e "\n${YELLOW}🔐 DIAGNOSTIC DES PERMISSIONS${NC}"
    echo "═══════════════════════════════════════════════════════════════"
    
    echo -e "${BLUE}📁 Permissions répertoire frontend:${NC}"
    ls -la "$APP_DIR/" | grep frontend | sed 's/^/  /'
    
    echo -e "\n${BLUE}📁 Permissions répertoire static:${NC}"
    ls -la "$APP_DIR/frontend/" | grep static | sed 's/^/  /'
    
    echo -e "\n${BLUE}📄 Permissions fichiers CSS:${NC}"
    find "$APP_DIR/frontend/static/css/" -name "*.css" -exec ls -la {} \; | head -5 | sed 's/^/  /'
    
    echo -e "\n${BLUE}📄 Permissions fichiers JS:${NC}"
    find "$APP_DIR/frontend/static/js/" -name "*.js" -exec ls -la {} \; | head -5 | sed 's/^/  /'
    
    echo "═══════════════════════════════════════════════════════════════"
}

# Fonction de surveillance en temps réel
monitor_realtime() {
    echo -e "\n${YELLOW}⏱️ SURVEILLANCE EN TEMPS RÉEL${NC}"
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "${CYAN}💡 Accédez à http://$SERVER_IP maintenant...${NC}"
    echo -e "${CYAN}💡 Appuyez sur Ctrl+C pour arrêter la surveillance${NC}"
    echo ""
    
    # Surveiller les logs en temps réel
    sudo tail -f /var/log/apache2/ntp-monitor_error.log /var/log/apache2/error.log /var/log/apache2/access.log
}

# Fonction de génération de rapport
generate_report() {
    local report_file="/tmp/ntp-web-report-$(date +%Y%m%d-%H%M%S).log"
    
    echo -e "\n${YELLOW}📊 GÉNÉRATION DU RAPPORT COMPLET${NC}"
    echo "═══════════════════════════════════════════════════════════════"
    
    {
        echo "═══════════════════════════════════════════════════════════════"
        echo "RAPPORT DIAGNOSTIC WEB - NTP MONITOR ENTERPRISE"
        echo "Généré le: $(date)"
        echo "Serveur: $SERVER_IP"
        echo "═══════════════════════════════════════════════════════════════"
        echo ""
        
        echo "🌐 INFORMATIONS SERVEUR"
        echo "Application: http://$SERVER_IP"
        echo "Répertoire: $APP_DIR"
        echo "Status Apache: $(systemctl is-active apache2)"
        echo ""
        
        echo "📋 LOGS RÉCENTS"
        echo "--- Logs Apache NTP Monitor ---"
        sudo tail -20 /var/log/apache2/ntp-monitor_error.log 2>/dev/null || echo "Fichier non trouvé"
        echo ""
        echo "--- Logs Apache Généraux ---"
        sudo tail -10 /var/log/apache2/error.log
        echo ""
        echo "--- Logs d'Accès ---"
        sudo tail -10 /var/log/apache2/access.log
        echo ""
        
        echo "🧪 TESTS DE CONNECTIVITÉ"
        echo "Page principale: $(curl -s -I http://localhost | head -1)"
        echo "Page login: $(curl -s -I http://localhost/auth/login | head -1)"
        echo "API status: $(curl -s -I http://localhost/api/status | head -1)"
        echo ""
        
        echo "🔐 PERMISSIONS"
        echo "--- Frontend ---"
        ls -la "$APP_DIR/" | grep frontend
        echo "--- Static ---"
        ls -la "$APP_DIR/frontend/" | grep static
        echo ""
        
        echo "📄 CONFIGURATION APACHE"
        sudo apache2ctl -S
        echo ""
        
    } > "$report_file"
    
    echo -e "${GREEN}✅ Rapport généré: $report_file${NC}"
    echo -e "${BLUE}📄 Pour voir le rapport: cat $report_file${NC}"
}

# Menu principal
show_menu() {
    clear
    echo -e "${PURPLE}📊 DIAGNOSTIC WEB - NTP MONITOR ENTERPRISE${NC}"
    echo -e "${BLUE}🌐 Application: http://$SERVER_IP${NC}"
    echo ""
    echo "Choisissez une option :"
    echo "1) 📋 Afficher logs récents"
    echo "2) 🧪 Tester fichiers statiques"
    echo "3) 🌐 Tester connectivité web"
    echo "4) 🔐 Vérifier permissions"
    echo "5) ⏱️ Surveillance temps réel"
    echo "6) 📊 Générer rapport complet"
    echo "7) 🔧 Corriger permissions fichiers statiques"
    echo "0) ❌ Quitter"
    echo ""
    read -p "Votre choix [0-7]: " choice
}

# Fonction de correction des permissions
fix_static_permissions() {
    echo -e "\n${YELLOW}🔧 CORRECTION DES PERMISSIONS FICHIERS STATIQUES${NC}"
    echo "═══════════════════════════════════════════════════════════════"
    
    echo -e "${BLUE}🔄 Correction en cours...${NC}"
    
    # Corriger les permissions
    sudo chown -R ntpmonitor:www-data "$APP_DIR/frontend/static/"
    sudo chmod -R 755 "$APP_DIR/frontend/static/"
    sudo find "$APP_DIR/frontend/static/" -type f -exec chmod 644 {} \;
    
    echo -e "${GREEN}✅ Permissions corrigées${NC}"
    
    # Redémarrer Apache
    echo -e "${BLUE}🔄 Redémarrage Apache...${NC}"
    sudo systemctl restart apache2
    
    if sudo systemctl is-active --quiet apache2; then
        echo -e "${GREEN}✅ Apache redémarré avec succès${NC}"
    else
        echo -e "${RED}❌ Problème avec le redémarrage d'Apache${NC}"
    fi
    
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "${CYAN}💡 Testez maintenant: http://$SERVER_IP${NC}"
    read -p "Appuyez sur Entrée pour continuer..."
}

# Boucle principale
main() {
    while true; do
        show_menu
        case $choice in
            1) show_recent_logs; read -p "Appuyez sur Entrée pour continuer..." ;;
            2) test_static_files; read -p "Appuyez sur Entrée pour continuer..." ;;
            3) test_web_connectivity; read -p "Appuyez sur Entrée pour continuer..." ;;
            4) check_permissions; read -p "Appuyez sur Entrée pour continuer..." ;;
            5) monitor_realtime ;;
            6) generate_report; read -p "Appuyez sur Entrée pour continuer..." ;;
            7) fix_static_permissions ;;
            0) echo -e "${GREEN}Au revoir !${NC}"; exit 0 ;;
            *) echo -e "${RED}Option invalide${NC}"; sleep 2 ;;
        esac
    done
}

# Si appelé avec des arguments, exécuter directement
if [ "$1" == "logs" ]; then
    show_recent_logs
elif [ "$1" == "test" ]; then
    test_static_files
    test_web_connectivity
elif [ "$1" == "fix" ]; then
    fix_static_permissions
elif [ "$1" == "report" ]; then
    generate_report
elif [ "$1" == "monitor" ]; then
    monitor_realtime
else
    main
fi 