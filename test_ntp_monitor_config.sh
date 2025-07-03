#!/bin/bash
# Script de Diagnostic Complet NTP Monitor Enterprise
# Vérifie tous les aspects de la configuration et du fonctionnement

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Variables
APP_NAME="ntp-monitor-enterprise"
APP_USER="ntp-monitor"
APP_DIR="/home/$APP_USER/$APP_NAME"
DB_NAME="ntp_monitor"
DB_USER="ntp_user"
SERVER_IP=$(hostname -I | awk '{print $1}')

# Compteurs
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNINGS=0

log_success() {
    echo -e "${GREEN}[✓] $1${NC}"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[✗] $1${NC}"
    ((TESTS_FAILED++))
}

log_warning() {
    echo -e "${YELLOW}[⚠] $1${NC}"
    ((TESTS_WARNINGS++))
}

log_info() {
    echo -e "${BLUE}[ℹ] $1${NC}"
}

section() {
    echo -e "\n${CYAN}============================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}============================================${NC}"
}

test_count() {
    ((TESTS_TOTAL++))
}

# Test des services système
test_system_services() {
    section "VÉRIFICATION SERVICES SYSTÈME"
    
    services=("apache2" "mysql" "redis-server" "ntpsec")
    
    for service in "${services[@]}"; do
        test_count
        if systemctl is-active --quiet "$service"; then
            log_success "Service $service : ACTIF"
        else
            log_error "Service $service : INACTIF"
        fi
    done
    
    # Test service application
    test_count
    if systemctl is-active --quiet "$APP_NAME"; then
        log_success "Service $APP_NAME : ACTIF"
    else
        log_warning "Service $APP_NAME : INACTIF (peut être normal si utilisé via Apache)"
    fi
}

# Test des ports réseau
test_network_ports() {
    section "VÉRIFICATION PORTS RÉSEAU"
    
    ports=("80:Apache" "3306:MySQL" "6379:Redis" "123:NTP")
    
    for port_info in "${ports[@]}"; do
        port=$(echo "$port_info" | cut -d':' -f1)
        service=$(echo "$port_info" | cut -d':' -f2)
        
        test_count
        if netstat -tuln | grep -q ":$port "; then
            log_success "Port $port ($service) : OUVERT"
        else
            log_error "Port $port ($service) : FERMÉ"
        fi
    done
}

# Test des fichiers et permissions
test_files_permissions() {
    section "VÉRIFICATION FICHIERS ET PERMISSIONS"
    
    # Vérifier utilisateur
    test_count
    if id "$APP_USER" &>/dev/null; then
        log_success "Utilisateur $APP_USER : EXISTE"
    else
        log_error "Utilisateur $APP_USER : INEXISTANT"
    fi
    
    # Vérifier répertoire application
    test_count
    if [[ -d "$APP_DIR" ]]; then
        log_success "Répertoire application : EXISTE"
    else
        log_error "Répertoire application : INEXISTANT"
        return
    fi
    
    # Vérifier fichiers critiques
    critical_files=("app.py" "app.wsgi" ".env" "backend/" "frontend/")
    
    for file in "${critical_files[@]}"; do
        test_count
        if [[ -e "$APP_DIR/$file" ]]; then
            log_success "Fichier $file : EXISTE"
        else
            log_error "Fichier $file : MANQUANT"
        fi
    done
    
    # Vérifier permissions
    test_count
    if [[ -r "$APP_DIR" ]]; then
        log_success "Permissions lecture répertoire : OK"
    else
        log_error "Permissions lecture répertoire : PROBLÈME"
    fi
    
    test_count
    if [[ -x "$APP_DIR/app.wsgi" ]]; then
        log_success "Permissions exécution WSGI : OK"
    else
        log_error "Permissions exécution WSGI : PROBLÈME"
    fi
}

# Test configuration Apache
test_apache_config() {
    section "VÉRIFICATION CONFIGURATION APACHE"
    
    # Vérifier site activé
    test_count
    if apache2ctl -S 2>/dev/null | grep -q "$APP_NAME"; then
        log_success "Site Apache activé : OK"
    else
        log_error "Site Apache activé : PROBLÈME"
    fi
    
    # Vérifier mod_wsgi
    test_count
    if apache2ctl -M 2>/dev/null | grep -q "wsgi"; then
        log_success "Module mod_wsgi : CHARGÉ"
    else
        log_error "Module mod_wsgi : NON CHARGÉ"
    fi
    
    # Vérifier configuration syntaxe
    test_count
    if apache2ctl configtest &>/dev/null; then
        log_success "Configuration Apache : SYNTAXE OK"
    else
        log_error "Configuration Apache : ERREUR SYNTAXE"
    fi
    
    # Vérifier accès aux fichiers
    test_count
    if [[ -r "$APP_DIR/frontend" ]]; then
        log_success "Accès répertoire frontend : OK"
    else
        log_error "Accès répertoire frontend : PROBLÈME"
    fi
}

# Test base de données
test_database() {
    section "VÉRIFICATION BASE DE DONNÉES"
    
    # Test connexion MySQL
    test_count
    if mysql -u root -e "SELECT 1;" &>/dev/null; then
        log_success "Connexion MySQL root : OK"
    else
        log_error "Connexion MySQL root : ÉCHEC"
    fi
    
    # Test existence base de données
    test_count
    if mysql -u root -e "USE $DB_NAME; SELECT 1;" &>/dev/null; then
        log_success "Base de données $DB_NAME : EXISTE"
    else
        log_error "Base de données $DB_NAME : INEXISTANTE"
    fi
    
    # Test utilisateur application
    test_count
    if [[ -f "/root/mysql_credentials.txt" ]]; then
        log_success "Credentials MySQL : FICHIER TROUVÉ"
        
        # Extraire le mot de passe
        DB_PASSWORD=$(grep "DB_PASSWORD=" /root/mysql_credentials.txt | cut -d'=' -f2)
        
        if [[ -n "$DB_PASSWORD" ]]; then
            test_count
            if mysql -u "$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" &>/dev/null; then
                log_success "Connexion utilisateur $DB_USER : OK"
            else
                log_error "Connexion utilisateur $DB_USER : ÉCHEC"
            fi
        fi
    else
        log_error "Credentials MySQL : FICHIER MANQUANT"
    fi
}

# Test NTP/ntpsec
test_ntp() {
    section "VÉRIFICATION NTP/NTPSEC"
    
    # Test service ntpsec
    test_count
    if systemctl is-active --quiet ntpsec; then
        log_success "Service ntpsec : ACTIF"
    else
        log_error "Service ntpsec : INACTIF"
    fi
    
    # Test commande ntpq
    test_count
    if command -v ntpq &>/dev/null; then
        log_success "Commande ntpq : DISPONIBLE"
        
        # Test peers
        test_count
        if ntpq -c peers &>/dev/null; then
            sync_count=$(ntpq -c peers 2>/dev/null | grep -c "^[*+]" || echo "0")
            if [[ $sync_count -gt 0 ]]; then
                log_success "Serveurs NTP synchronisés : $sync_count"
            else
                log_warning "Serveurs NTP synchronisés : AUCUN"
            fi
        else
            log_error "Commande ntpq peers : ÉCHEC"
        fi
    else
        log_error "Commande ntpq : INDISPONIBLE"
    fi
}

# Test Redis
test_redis() {
    section "VÉRIFICATION REDIS"
    
    # Test connexion Redis
    test_count
    if redis-cli ping &>/dev/null; then
        log_success "Connexion Redis : OK"
    else
        log_error "Connexion Redis : ÉCHEC"
    fi
    
    # Test écriture/lecture
    test_count
    if redis-cli set test_key "test_value" &>/dev/null && redis-cli get test_key &>/dev/null; then
        log_success "Test écriture/lecture Redis : OK"
        redis-cli del test_key &>/dev/null
    else
        log_error "Test écriture/lecture Redis : ÉCHEC"
    fi
}

# Test accès web
test_web_access() {
    section "VÉRIFICATION ACCÈS WEB"
    
    # Test port 80
    test_count
    if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|302\|403"; then
        log_success "Accès http://localhost : RÉPONSE SERVEUR"
    else
        log_error "Accès http://localhost : AUCUNE RÉPONSE"
    fi
    
    # Test IP externe
    test_count
    if curl -s -o /dev/null -w "%{http_code}" "http://$SERVER_IP" | grep -q "200\|302\|403"; then
        log_success "Accès http://$SERVER_IP : RÉPONSE SERVEUR"
    else
        log_error "Accès http://$SERVER_IP : AUCUNE RÉPONSE"
    fi
    
    # Test détaillé de la réponse
    test_count
    response=$(curl -s -w "%{http_code}" "http://$SERVER_IP" 2>/dev/null)
    http_code=$(echo "$response" | tail -c 4)
    
    case "$http_code" in
        200)
            log_success "Code HTTP : 200 OK - Application fonctionne"
            ;;
        302)
            log_success "Code HTTP : 302 Redirect - Application redirige"
            ;;
        403)
            log_warning "Code HTTP : 403 Forbidden - Problème permissions"
            ;;
        404)
            log_error "Code HTTP : 404 Not Found - Application non trouvée"
            ;;
        500)
            log_error "Code HTTP : 500 Internal Error - Erreur application"
            ;;
        *)
            log_error "Code HTTP : $http_code - Réponse inattendue"
            ;;
    esac
}

# Test logs
test_logs() {
    section "VÉRIFICATION LOGS"
    
    # Logs Apache
    test_count
    if [[ -f "/var/log/apache2/${APP_NAME}_error.log" ]]; then
        log_success "Log Apache erreur : EXISTE"
        
        # Vérifier erreurs récentes
        recent_errors=$(tail -10 "/var/log/apache2/${APP_NAME}_error.log" 2>/dev/null | grep -c "ERROR\|CRITICAL\|Fatal")
        if [[ $recent_errors -gt 0 ]]; then
            log_warning "Erreurs récentes Apache : $recent_errors trouvées"
        else
            log_success "Erreurs récentes Apache : AUCUNE"
        fi
    else
        log_error "Log Apache erreur : INEXISTANT"
    fi
    
    # Logs système
    test_count
    if journalctl -u "$APP_NAME" --since="1 hour ago" --quiet &>/dev/null; then
        log_success "Logs service système : ACCESSIBLES"
    else
        log_warning "Logs service système : INACCESSIBLES"
    fi
}

# Test configuration Python
test_python_config() {
    section "VÉRIFICATION CONFIGURATION PYTHON"
    
    # Test version Python
    test_count
    if python3 --version &>/dev/null; then
        python_version=$(python3 --version 2>&1 | awk '{print $2}')
        log_success "Python version : $python_version"
    else
        log_error "Python : INDISPONIBLE"
    fi
    
    # Test modules Python essentiels
    modules=("flask" "sqlalchemy" "pymysql" "redis")
    
    for module in "${modules[@]}"; do
        test_count
        if python3 -c "import $module" &>/dev/null; then
            log_success "Module Python $module : DISPONIBLE"
        else
            log_error "Module Python $module : MANQUANT"
        fi
    done
    
    # Test environnement virtuel si existe
    test_count
    if [[ -d "$APP_DIR/venv" ]]; then
        log_info "Environnement virtuel détecté"
        if [[ -x "$APP_DIR/venv/bin/python" ]]; then
            log_success "Environnement virtuel : FONCTIONNEL"
        else
            log_error "Environnement virtuel : DÉFAILLANT"
        fi
    else
        log_info "Environnement virtuel : NON UTILISÉ"
    fi
}

# Test firewall
test_firewall() {
    section "VÉRIFICATION FIREWALL"
    
    # Test UFW
    test_count
    if command -v ufw &>/dev/null; then
        if ufw status | grep -q "Status: active"; then
            log_success "UFW : ACTIF"
            
            # Vérifier règles port 80
            test_count
            if ufw status | grep -q "80"; then
                log_success "Règle UFW port 80 : CONFIGURÉE"
            else
                log_warning "Règle UFW port 80 : MANQUANTE"
            fi
        else
            log_info "UFW : INACTIF"
        fi
    else
        log_info "UFW : NON INSTALLÉ"
    fi
    
    # Test iptables
    test_count
    if iptables -L &>/dev/null; then
        rules_count=$(iptables -L | wc -l)
        if [[ $rules_count -gt 10 ]]; then
            log_warning "iptables : $rules_count règles (possibles conflits)"
        else
            log_success "iptables : $rules_count règles (normal)"
        fi
    else
        log_error "iptables : INACCESSIBLE"
    fi
}

# Résumé et recommandations
show_summary() {
    section "RÉSUMÉ DU DIAGNOSTIC"
    
    echo -e "\n${CYAN}📊 STATISTIQUES${NC}"
    echo -e "   Total tests     : $TESTS_TOTAL"
    echo -e "   ${GREEN}Réussis         : $TESTS_PASSED${NC}"
    echo -e "   ${RED}Échoués         : $TESTS_FAILED${NC}"
    echo -e "   ${YELLOW}Avertissements  : $TESTS_WARNINGS${NC}"
    
    echo -e "\n${CYAN}🎯 ÉTAT GÉNÉRAL${NC}"
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "   ${GREEN}✅ SYSTÈME FONCTIONNEL${NC}"
        echo -e "   ${GREEN}🎉 Application prête à l'emploi !${NC}"
    elif [[ $TESTS_FAILED -le 3 ]]; then
        echo -e "   ${YELLOW}⚠️ SYSTÈME PARTIELLEMENT FONCTIONNEL${NC}"
        echo -e "   ${YELLOW}🔧 Quelques corrections nécessaires${NC}"
    else
        echo -e "   ${RED}❌ SYSTÈME DYSFONCTIONNEL${NC}"
        echo -e "   ${RED}🚨 Corrections urgentes nécessaires${NC}"
    fi
    
    echo -e "\n${CYAN}🔧 ACTIONS RECOMMANDÉES${NC}"
    
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "   ${RED}1. Corriger les erreurs listées ci-dessus${NC}"
        echo -e "   ${RED}2. Vérifier les logs : sudo tail -f /var/log/apache2/${APP_NAME}_error.log${NC}"
        echo -e "   ${RED}3. Redémarrer les services : sudo systemctl restart apache2${NC}"
    fi
    
    if [[ $TESTS_WARNINGS -gt 0 ]]; then
        echo -e "   ${YELLOW}4. Examiner les avertissements${NC}"
        echo -e "   ${YELLOW}5. Optimiser la configuration si nécessaire${NC}"
    fi
    
    echo -e "\n${CYAN}🌐 ACCÈS APPLICATION${NC}"
    echo -e "   URL locale    : http://localhost"
    echo -e "   URL réseau    : http://$SERVER_IP"
    echo -e "   Gestion       : ./manage_ntp_monitor.sh"
    
    echo -e "\n${CYAN}📋 COMMANDES UTILES${NC}"
    echo -e "   Statut        : ./manage_ntp_monitor.sh status"
    echo -e "   Logs          : ./manage_ntp_monitor.sh logs"
    echo -e "   Redémarrage   : sudo systemctl restart apache2"
    echo -e "   Ce diagnostic : ./test_ntp_monitor_config.sh"
}

# Fonction principale
main() {
    clear
    echo -e "${CYAN}🔍 DIAGNOSTIC COMPLET NTP MONITOR ENTERPRISE${NC}"
    echo -e "${CYAN}Serveur : $SERVER_IP${NC}"
    echo -e "${CYAN}Date : $(date)${NC}"
    
    # Exécuter tous les tests
    test_system_services
    test_network_ports
    test_files_permissions
    test_apache_config
    test_database
    test_ntp
    test_redis
    test_web_access
    test_logs
    test_python_config
    test_firewall
    
    # Afficher le résumé
    show_summary
    
    echo -e "\n${CYAN}============================================${NC}"
    echo -e "${CYAN}  DIAGNOSTIC TERMINÉ${NC}"
    echo -e "${CYAN}============================================${NC}"
}

# Exécution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 