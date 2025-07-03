#!/bin/bash
# Script de Gestion NTP Monitor Enterprise
# Outils de maintenance et dépannage post-déploiement

# Configuration
APP_NAME="ntp-monitor-enterprise"
APP_USER="ntp-monitor"
APP_DIR="/home/$APP_USER/$APP_NAME"
GITHUB_REPO="https://github.com/gilandre/NTPVIZ.git"
GITHUB_BRANCH="dev"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Certaines opérations nécessitent les privilèges root"
        echo "Utilisation: sudo $0 $1"
        exit 1
    fi
}

show_status() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}  STATUT SERVICES NTP MONITOR${NC}"
    echo -e "${BLUE}============================================${NC}"
    
    services=("$APP_NAME" "apache2" "mysql" "redis-server" "ntpsec")
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            echo -e "${GREEN}✅ $service : ACTIF${NC}"
        else
            echo -e "${RED}❌ $service : INACTIF${NC}"
        fi
    done
    
    echo
    echo -e "${BLUE}📊 Utilisation ressources :${NC}"
    echo -e "   CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
    echo -e "   RAM: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
    echo -e "   Disque: $(df -h / | tail -1 | awk '{print $5}')"
    
    if command -v ntpq &> /dev/null; then
        echo
        echo -e "${BLUE}🕐 Statut NTP :${NC}"
        if ntpq -c peers &> /dev/null; then
            SYNC_COUNT=$(ntpq -c peers 2>/dev/null | grep -c "^[*+]" || echo "0")
            echo -e "   Serveurs synchronisés: $SYNC_COUNT"
        else
            echo -e "   ntpsec ne répond pas"
        fi
    fi
    
    echo
    echo -e "${BLUE}🌐 Accès Web :${NC}"
    if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200"; then
        echo -e "   ${GREEN}✅ Application accessible${NC}"
    else
        echo -e "   ${RED}❌ Application inaccessible${NC}"
    fi
}

start_services() {
    check_root
    log "Démarrage de tous les services..."
    
    services=("mysql" "redis-server" "ntpsec" "apache2" "$APP_NAME")
    
    for service in "${services[@]}"; do
        log "Démarrage $service..."
        systemctl start "$service"
        if systemctl is-active --quiet "$service"; then
            log "✅ $service démarré"
        else
            error "❌ Échec démarrage $service"
        fi
    done
}

stop_services() {
    check_root
    log "Arrêt de tous les services..."
    
    services=("$APP_NAME" "apache2" "redis-server")
    
    for service in "${services[@]}"; do
        log "Arrêt $service..."
        systemctl stop "$service"
    done
    
    warn "MySQL et ntpsec conservés actifs"
}

restart_services() {
    check_root
    log "Redémarrage de tous les services..."
    
    services=("$APP_NAME" "apache2" "redis-server")
    
    for service in "${services[@]}"; do
        log "Redémarrage $service..."
        systemctl restart "$service"
        sleep 2
    done
    
    log "✅ Services redémarrés"
}

show_logs() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}  LOGS RÉCENTS${NC}"
    echo -e "${BLUE}============================================${NC}"
    
    case "$1" in
        "app"|"application")
            log "Logs application (30 dernières lignes):"
            journalctl -u "$APP_NAME" -n 30 --no-pager
            ;;
        "apache")
            log "Logs Apache erreur (20 dernières lignes):"
            tail -20 "/var/log/apache2/${APP_NAME}_error.log" 2>/dev/null || echo "Fichier non trouvé"
            ;;
        "mysql")
            log "Logs MySQL (20 dernières lignes):"
            journalctl -u mysql -n 20 --no-pager
            ;;
        "ntpsec"|"ntp")
            log "Logs ntpsec (20 dernières lignes):"
            journalctl -u ntpsec -n 20 --no-pager
            ;;
        *)
            log "Logs application récents:"
            journalctl -u "$APP_NAME" -n 15 --no-pager
            echo
            log "Logs Apache récents:"
            tail -10 "/var/log/apache2/${APP_NAME}_error.log" 2>/dev/null || echo "Fichier non trouvé"
            ;;
    esac
}

update_app() {
    check_root
    log "Mise à jour de l'application depuis GitHub..."
    
    # Arrêter l'application
    systemctl stop "$APP_NAME"
    
    # Sauvegarder configuration
    cp "$APP_DIR/.env" "/tmp/ntp_env_backup"
    
    # Mise à jour
    sudo -u "$APP_USER" bash << EOF
cd "$APP_DIR"
git fetch origin
git pull origin "$GITHUB_BRANCH"
source venv/bin/activate
pip install --upgrade -r requirements_ubuntu.txt
EOF
    
    # Restaurer configuration
    cp "/tmp/ntp_env_backup" "$APP_DIR/.env"
    chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
    
    # Redémarrer
    systemctl start "$APP_NAME"
    
    log "✅ Application mise à jour"
}

backup_data() {
    check_root
    BACKUP_DIR="/home/$APP_USER/backups/$(date +%Y%m%d_%H%M%S)"
    
    log "Création sauvegarde dans $BACKUP_DIR..."
    
    sudo -u "$APP_USER" mkdir -p "$BACKUP_DIR"
    
    # Sauvegarde base de données
    if [[ -f "/root/mysql_credentials.txt" ]]; then
        MYSQL_PASSWORD=$(grep MYSQL_PASSWORD /root/mysql_credentials.txt | cut -d'=' -f2)
        mysqldump -u ntp_user -p"$MYSQL_PASSWORD" ntp_monitor > "$BACKUP_DIR/database.sql"
        log "✅ Base de données sauvegardée"
    fi
    
    # Sauvegarde configuration
    cp "$APP_DIR/.env" "$BACKUP_DIR/"
    cp -r "$APP_DIR/logs" "$BACKUP_DIR/" 2>/dev/null || true
    
    # Sauvegarde ntpsec
    if [[ -f "/etc/ntpsec/ntp.conf" ]]; then
        mkdir -p "$BACKUP_DIR/ntpsec"
        cp /etc/ntpsec/ntp.conf "$BACKUP_DIR/ntpsec/"
        [[ -f "/etc/ntpsec/ntp.keys" ]] && cp /etc/ntpsec/ntp.keys "$BACKUP_DIR/ntpsec/"
    fi
    
    chown -R "$APP_USER:$APP_USER" "$BACKUP_DIR"
    
    log "✅ Sauvegarde terminée: $BACKUP_DIR"
}

test_connectivity() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}  TEST CONNECTIVITÉ${NC}"
    echo -e "${BLUE}============================================${NC}"
    
    # Test MySQL
    log "Test MySQL..."
    if mysqladmin ping &>/dev/null; then
        log "✅ MySQL répond"
    else
        error "❌ MySQL ne répond pas"
    fi
    
    # Test Redis
    log "Test Redis..."
    if redis-cli ping &>/dev/null; then
        log "✅ Redis répond"
    else
        error "❌ Redis ne répond pas"
    fi
    
    # Test ntpsec
    log "Test ntpsec..."
    if ntpq -c peers &>/dev/null; then
        log "✅ ntpsec répond"
        OFFSET=$(ntpq -c peers 2>/dev/null | grep "^*" | awk '{print $9}' | head -1)
        [[ -n "$OFFSET" ]] && log "   Offset: ${OFFSET}ms"
    else
        error "❌ ntpsec ne répond pas"
    fi
    
    # Test Apache
    log "Test Apache..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200"; then
        log "✅ Apache répond (HTTP 200)"
    else
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost)
        error "❌ Apache problème (HTTP $HTTP_CODE)"
    fi
    
    # Test application
    log "Test application..."
    if curl -s http://localhost | grep -q "NTP Monitor" 2>/dev/null; then
        log "✅ Application répond"
    else
        error "❌ Application ne répond pas correctement"
    fi
}

clean_logs() {
    check_root
    log "Nettoyage des logs anciens..."
    
    # Logs application
    find "$APP_DIR/logs" -name "*.log" -mtime +30 -delete 2>/dev/null || true
    
    # Logs Apache
    find /var/log/apache2 -name "${APP_NAME}_*.log.*" -mtime +30 -delete 2>/dev/null || true
    
    # Logs système
    journalctl --vacuum-time=30d &>/dev/null || true
    
    log "✅ Nettoyage terminé"
}

reset_admin_password() {
    check_root
    log "Réinitialisation du mot de passe administrateur..."
    
    sudo -u "$APP_USER" bash << EOF
cd "$APP_DIR"
source venv/bin/activate
python -c "
from app import app
from backend.models.user import User
from backend.database_manager import db_manager

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        admin.set_password('admin123')
        db_manager.session.commit()
        print('Mot de passe admin réinitialisé: admin123')
    else:
        print('Utilisateur admin non trouvé')
"
EOF
    
    log "✅ Mot de passe admin réinitialisé: admin123"
}

show_info() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}  INFORMATIONS SYSTÈME${NC}"
    echo -e "${BLUE}============================================${NC}"
    
    echo -e "${BLUE}📁 Répertoires :${NC}"
    echo -e "   Application: $APP_DIR"
    echo -e "   Logs: $APP_DIR/logs"
    echo -e "   Sauvegardes: /home/$APP_USER/backups"
    
    echo -e "\n${BLUE}🔧 Services :${NC}"
    echo -e "   Principal: $APP_NAME"
    echo -e "   Web: apache2"
    echo -e "   Base: mysql"
    echo -e "   Cache: redis-server"
    echo -e "   Temps: ntpsec"
    
    echo -e "\n${BLUE}🌐 URLs :${NC}"
    echo -e "   Local: http://localhost"
    IP=$(ip route get 1 | awk '{print $7}' | head -1)
    echo -e "   Réseau: http://$IP"
    
    echo -e "\n${BLUE}📋 Fichiers config :${NC}"
    echo -e "   App: $APP_DIR/.env"
    echo -e "   Apache: /etc/apache2/sites-available/$APP_NAME.conf"
    echo -e "   MySQL: /root/mysql_credentials.txt"
    echo -e "   Service: /etc/systemd/system/$APP_NAME.service"
    
    echo -e "\n${BLUE}👤 Connexion par défaut :${NC}"
    echo -e "   Utilisateur: admin"
    echo -e "   Mot de passe: admin123"
}

show_help() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}  SCRIPT DE GESTION NTP MONITOR${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo -e "${BLUE}Commandes disponibles :${NC}"
    echo
    echo -e "${GREEN}📊 Monitoring :${NC}"
    echo "  status          Afficher le statut de tous les services"
    echo "  logs [service]  Afficher les logs (app, apache, mysql, ntpsec)"
    echo "  test            Tester la connectivité de tous les services"
    echo
    echo -e "${GREEN}🔧 Gestion Services :${NC}"
    echo "  start           Démarrer tous les services"
    echo "  stop            Arrêter les services (sauf MySQL/ntpsec)"
    echo "  restart         Redémarrer les services"
    echo
    echo -e "${GREEN}🔄 Maintenance :${NC}"
    echo "  update          Mettre à jour l'application depuis GitHub"
    echo "  backup          Créer une sauvegarde complète"
    echo "  clean           Nettoyer les logs anciens"
    echo "  reset-password  Réinitialiser le mot de passe admin"
    echo
    echo -e "${GREEN}ℹ️  Information :${NC}"
    echo "  info            Afficher les informations système"
    echo "  help            Afficher cette aide"
    echo
    echo -e "${BLUE}Exemples :${NC}"
    echo "  $0 status                    # Statut général"
    echo "  $0 logs app                  # Logs application"
    echo "  $0 restart                   # Redémarrage services"
    echo "  sudo $0 update               # Mise à jour"
    echo "  sudo $0 backup               # Sauvegarde"
    echo
}

# Menu principal
case "$1" in
    "status")
        show_status
        ;;
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "logs")
        show_logs "$2"
        ;;
    "update")
        update_app
        ;;
    "backup")
        backup_data
        ;;
    "test")
        test_connectivity
        ;;
    "clean")
        clean_logs
        ;;
    "reset-password")
        reset_admin_password
        ;;
    "info")
        show_info
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        echo -e "${YELLOW}Commande inconnue: $1${NC}"
        show_help
        exit 1
        ;;
esac 