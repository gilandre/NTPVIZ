#!/bin/bash
# ============================================================================
# verify_installation.sh - Vérification installation NTP Monitor Enterprise
# Script de vérification pour débutants
# ============================================================================

# === COULEURS ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# === FONCTIONS ===
log_info()    { echo -e "${BLUE}ℹ️  $*${NC}"; }
log_success() { echo -e "${GREEN}✅ $*${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $*${NC}"; }
log_error()   { echo -e "${RED}❌ $*${NC}"; }
log_title()   { echo -e "${WHITE}🚀 $*${NC}"; }

# === VARIABLES ===
SCORE=0
TOTAL=0

# === FONCTION DE TEST ===
test_item() {
    local name="$1"
    local command="$2"
    local expected="$3"
    
    TOTAL=$((TOTAL + 1))
    printf "  Testing %-30s " "$name:"
    
    if eval "$command" &>/dev/null; then
        log_success "OK"
        SCORE=$((SCORE + 1))
    else
        log_error "FAIL"
    fi
}

# === DÉBUT VÉRIFICATION ===
log_title "=== VÉRIFICATION NTP MONITOR ENTERPRISE ==="
echo "Date: $(date)"
echo "Serveur: $(hostname -I | awk '{print $1}')"
echo

# === SERVICES ===
log_info "🔧 Vérification des services..."
test_item "NTP Monitor Service" "systemctl is-active --quiet ntp-monitor"
test_item "Apache Web Server" "systemctl is-active --quiet apache2"
test_item "MySQL Database" "systemctl is-active --quiet mysql"
test_item "Redis Cache" "systemctl is-active --quiet redis-server"
test_item "NTP Server (ntpsec)" "systemctl is-active --quiet ntpsec"

# === PORTS ===
log_info "🌐 Vérification des ports..."
test_item "Port 80 (HTTP)" "netstat -tlnp | grep -q ':80 '"
test_item "Port 5000 (App)" "netstat -tlnp | grep -q ':5000 '"
test_item "Port 3306 (MySQL)" "netstat -tlnp | grep -q ':3306 '"
test_item "Port 6379 (Redis)" "netstat -tlnp | grep -q ':6379 '"
test_item "Port 123 (NTP)" "netstat -ulnp | grep -q ':123 '"

# === FICHIERS ===
log_info "📁 Vérification des fichiers..."
test_item "Application installée" "[ -f /opt/ntp-monitor-enterprise/app.py ]"
test_item "Configuration présente" "[ -f /opt/ntp-monitor-enterprise/.env ]"
test_item "Environnement virtuel" "[ -d /opt/ntp-monitor-venv ]"
test_item "Configuration Apache" "[ -f /etc/apache2/sites-available/ntp-monitor.conf ]"
test_item "Service systemd" "[ -f /etc/systemd/system/ntp-monitor.service ]"

# === CONNECTIVITÉ ===
log_info "🔗 Vérification de la connectivité..."
test_item "Interface web (HTTP)" "curl -s http://localhost | grep -q 'NTP Monitor'"
test_item "API Status" "curl -s http://localhost/api/system/status | grep -q 'status'"

# === BASE DE DONNÉES ===
log_info "🗄️  Vérification base de données..."
if [ -f /opt/ntp-monitor-enterprise/.env ]; then
    source /opt/ntp-monitor-enterprise/.env 2>/dev/null || true
    if [[ "$DATABASE_URL" == mysql* ]]; then
        test_item "Connexion MySQL" "mysql -u ntp_user -p$(echo $DATABASE_URL | cut -d':' -f3 | cut -d'@' -f1) ntp_monitor -e 'SELECT 1' 2>/dev/null"
        test_item "Tables créées" "mysql -u ntp_user -p$(echo $DATABASE_URL | cut -d':' -f3 | cut -d'@' -f1) ntp_monitor -e 'SHOW TABLES' 2>/dev/null | grep -q ntp_servers"
    else
        test_item "Base SQLite" "[ -f /opt/ntp-monitor-enterprise/instance/ntp_monitor.db ]"
    fi
else
    log_warning "Fichier .env non trouvé"
fi

# === PERMISSIONS ===
log_info "🔐 Vérification des permissions..."
test_item "Propriétaire correct" "[ $(stat -c '%U' /opt/ntp-monitor-enterprise) = 'ntp-monitor' ]"
test_item "Logs accessibles" "[ -d /var/log/ntp-monitor ]"

# === RÉSUMÉ ===
echo
log_title "=== RÉSUMÉ ==="
PERCENTAGE=$((SCORE * 100 / TOTAL))

if [ $PERCENTAGE -ge 90 ]; then
    log_success "🎉 Excellent ! Score: $SCORE/$TOTAL ($PERCENTAGE%)"
    log_success "Votre installation est parfaitement fonctionnelle !"
elif [ $PERCENTAGE -ge 75 ]; then
    log_warning "⚡ Bon ! Score: $SCORE/$TOTAL ($PERCENTAGE%)"
    log_warning "Installation fonctionnelle avec quelques problèmes mineurs"
elif [ $PERCENTAGE -ge 50 ]; then
    log_warning "⚠️  Moyen ! Score: $SCORE/$TOTAL ($PERCENTAGE%)"
    log_warning "Installation partiellement fonctionnelle"
else
    log_error "❌ Problème ! Score: $SCORE/$TOTAL ($PERCENTAGE%)"
    log_error "Installation non fonctionnelle"
fi

# === INFORMATIONS D'ACCÈS ===
if [ $PERCENTAGE -ge 75 ]; then
    echo
    log_info "📋 Informations d'accès :"
    SERVER_IP=$(hostname -I | awk '{print $1}')
    echo "   🌐 Interface web : http://$SERVER_IP"
    echo "   👤 Utilisateur   : admin"
    echo "   🔒 Mot de passe  : admin123"
    echo
    log_warning "⚠️  IMPORTANT : Changez le mot de passe après la première connexion !"
fi

# === COMMANDES UTILES ===
echo
log_info "🔧 Commandes utiles :"
echo "   • Statut services  : sudo systemctl status ntp-monitor apache2 mysql"
echo "   • Logs application : sudo journalctl -u ntp-monitor -f"
echo "   • Logs Apache      : sudo tail -f /var/log/apache2/ntp-monitor_error.log"
echo "   • Redémarrer app   : sudo systemctl restart ntp-monitor"
echo "   • Test interface   : curl http://localhost"

# === DÉPANNAGE ===
if [ $PERCENTAGE -lt 75 ]; then
    echo
    log_info "🔍 Dépannage :"
    echo "   1. Vérifiez les logs : sudo journalctl -u ntp-monitor"
    echo "   2. Redémarrez les services : sudo systemctl restart ntp-monitor apache2"
    echo "   3. Vérifiez la configuration : nano /opt/ntp-monitor-enterprise/.env"
    echo "   4. Consultez la documentation : README.md"
fi

# === FIN ===
echo
if [ $PERCENTAGE -ge 90 ]; then
    log_success "🚀 Votre NTP Monitor Enterprise est prêt à l'emploi !"
elif [ $PERCENTAGE -ge 75 ]; then
    log_warning "⚡ Votre installation fonctionne mais nécessite quelques ajustements"
else
    log_error "❌ Votre installation nécessite des corrections importantes"
fi

exit 0 