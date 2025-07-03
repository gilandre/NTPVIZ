#!/bin/bash
# Script de restauration ntpsec - Préserve installation existante fonctionnelle
# Adapté pour serveurs ntpsec déjà opérationnels avec clients connectés

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Vérifier si on est root
if [[ $EUID -ne 0 ]]; then
    error "❌ Ce script doit être exécuté en tant que root (sudo)"
fi

log "🔧 Préservation configuration ntpsec existante"

# Fonction pour vérifier l'état ntpsec
check_ntpsec_status() {
    log "🔍 Vérification de l'état ntpsec actuel..."
    
    # Vérifier si ntpsec est installé
    if command -v ntpq &> /dev/null; then
        log "✅ ntpsec est installé"
        NTPSEC_INSTALLED=true
    else
        warn "⚠️ ntpsec n'est pas installé"
        NTPSEC_INSTALLED=false
    fi
    
    # Vérifier si le service ntpsec est actif
    if systemctl is-active --quiet ntpsec 2>/dev/null; then
        log "✅ Service ntpsec est actif"
        NTPSEC_ACTIVE=true
        
        # Vérifier si ntpq répond
        if ntpq -c peers &> /dev/null; then
            log "✅ ntpq répond correctement"
            NTPSEC_FUNCTIONAL=true
            
            # Compter les serveurs synchronisés
            SYNC_SERVERS=$(ntpq -c peers 2>/dev/null | grep -c "^[*+]" || echo "0")
            if [ "$SYNC_SERVERS" -gt 0 ]; then
                log "✅ $SYNC_SERVERS serveur(s) NTP synchronisé(s)"
                NTPSEC_SYNCHRONIZED=true
            else
                warn "⚠️ Aucun serveur NTP synchronisé actuellement"
                NTPSEC_SYNCHRONIZED=false
            fi
            
            # Vérifier les clients connectés (requêtes NTP entrantes)
            CLIENT_CONNECTIONS=$(ss -u -n | grep :123 | wc -l || echo "0")
            if [ "$CLIENT_CONNECTIONS" -gt 0 ]; then
                log "✅ $CLIENT_CONNECTIONS connexion(s) client(s) NTP détectée(s)"
                NTPSEC_HAS_CLIENTS=true
            else
                info "ℹ️ Aucune connexion client active actuellement"
                NTPSEC_HAS_CLIENTS=false
            fi
        else
            warn "⚠️ ntpq ne répond pas correctement"
            NTPSEC_FUNCTIONAL=false
        fi
    else
        warn "⚠️ Service ntpsec inactif"
        NTPSEC_ACTIVE=false
        NTPSEC_FUNCTIONAL=false
    fi
}

# Fonction pour afficher le statut détaillé
display_ntpsec_status() {
    log "📊 État actuel de ntpsec:"
    echo "   - Installé: $([[ $NTPSEC_INSTALLED == true ]] && echo "✅ Oui" || echo "❌ Non")"
    echo "   - Service actif: $([[ $NTPSEC_ACTIVE == true ]] && echo "✅ Oui" || echo "❌ Non")"
    echo "   - Fonctionnel: $([[ $NTPSEC_FUNCTIONAL == true ]] && echo "✅ Oui" || echo "❌ Non")"
    if [[ $NTPSEC_FUNCTIONAL == true ]]; then
        echo "   - Serveurs synchronisés: $SYNC_SERVERS"
        echo "   - Clients connectés: $([[ $NTPSEC_HAS_CLIENTS == true ]] && echo "✅ Oui ($CLIENT_CONNECTIONS)" || echo "ℹ️ Aucun actuellement")"
    fi
}

# Vérifier l'état de ntpsec
check_ntpsec_status
display_ntpsec_status

# Si ntpsec fonctionne parfaitement, être très prudent
if [[ $NTPSEC_INSTALLED == true && $NTPSEC_ACTIVE == true && $NTPSEC_FUNCTIONAL == true ]]; then
    log "🎉 ntpsec fonctionne déjà parfaitement !"
    
    if [[ $NTPSEC_HAS_CLIENTS == true ]]; then
        warn "⚠️ ATTENTION: Des clients sont connectés à votre serveur ntpsec"
        warn "⚠️ Toute interruption pourrait affecter la synchronisation des clients"
        echo
        log "📋 Actions prévues (non perturbantes):"
        echo "   1. Vérifier et désactiver chrony/timesyncd si nécessaire"
        echo "   2. Configurer l'application pour utiliser ntpsec"  
        echo "   3. Vérifier la configuration existante"
        echo "   4. Tests de validation"
        echo
        read -p "Voulez-vous continuer ? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "👋 Opération annulée - votre configuration ntpsec reste inchangée"
            exit 0
        fi
    fi
fi

# Sauvegarder la configuration ntpsec AVANT toute modification
backup_ntpsec_config() {
    if [[ $NTPSEC_INSTALLED == true ]]; then
        log "💾 Sauvegarde de la configuration ntpsec existante..."
        
        # Créer répertoire de sauvegarde avec timestamp
        BACKUP_DIR="/root/ntpsec_backup/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        # Sauvegarder tous les fichiers importants
        if [ -f "/etc/ntpsec/ntp.conf" ]; then
            cp /etc/ntpsec/ntp.conf "$BACKUP_DIR/ntp.conf.bak"
            log "✅ Configuration ntpsec sauvegardée"
        fi
        
        if [ -f "/etc/ntpsec/ntp.keys" ]; then
            cp /etc/ntpsec/ntp.keys "$BACKUP_DIR/ntp.keys.bak"
            chmod 600 "$BACKUP_DIR/ntp.keys.bak"
            log "✅ Clés ntpsec sauvegardées"
        fi
        
        # Sauvegarder l'état actuel
        systemctl status ntpsec > "$BACKUP_DIR/ntpsec_status.txt" 2>&1 || true
        ntpq -c peers > "$BACKUP_DIR/ntpsec_peers.txt" 2>&1 || true
        ntpq -c associations > "$BACKUP_DIR/ntpsec_associations.txt" 2>&1 || true
        
        echo "$BACKUP_DIR" > /root/last_ntpsec_backup.txt
        log "✅ Sauvegarde complète dans $BACKUP_DIR"
    fi
}

# Arrêter les services concurrents (sans toucher à ntpsec)
stop_conflicting_services() {
    log "🔄 Vérification des services concurrents..."
    
    # Arrêter chrony s'il est actif
    if systemctl is-active --quiet chronyd 2>/dev/null; then
        warn "⚠️ chrony est actif et peut entrer en conflit avec ntpsec"
        log "🔄 Arrêt de chrony..."
        systemctl stop chronyd
        systemctl disable chronyd
        log "✅ chrony arrêté et désactivé"
    else
        log "✅ chrony n'est pas actif"
    fi
    
    # Arrêter systemd-timesyncd s'il est actif
    if systemctl is-active --quiet systemd-timesyncd 2>/dev/null; then
        warn "⚠️ systemd-timesyncd est actif et peut entrer en conflit avec ntpsec"
        log "🔄 Arrêt de systemd-timesyncd..."
        systemctl stop systemd-timesyncd
        systemctl disable systemd-timesyncd
        log "✅ systemd-timesyncd arrêté et désactivé"
    else
        log "✅ systemd-timesyncd n'est pas actif"
    fi
}

# Installer ntpsec si nécessaire (sans perturber l'existant)
ensure_ntpsec_installed() {
    if [[ $NTPSEC_INSTALLED == false ]]; then
        log "📦 Installation de ntpsec..."
        apt update
        apt install -y ntpsec ntpsec-utils ntpsec-doc
        log "✅ ntpsec installé"
    else
        log "✅ ntpsec déjà installé"
    fi
}

# Assurer que ntpsec fonctionne (redémarrage en douceur si nécessaire)
ensure_ntpsec_running() {
    log "🚀 Vérification du service ntpsec..."
    
    if [[ $NTPSEC_ACTIVE == false ]]; then
        log "🔄 Démarrage du service ntpsec..."
        systemctl enable ntpsec
        systemctl start ntpsec
        sleep 5
    elif [[ $NTPSEC_FUNCTIONAL == false ]]; then
        warn "⚠️ ntpsec est actif mais ne répond pas correctement"
        if [[ $NTPSEC_HAS_CLIENTS == true ]]; then
            warn "⚠️ ATTENTION: Des clients sont connectés - redémarrage en douceur"
            log "🔄 Rechargement de la configuration ntpsec..."
            systemctl reload ntpsec || systemctl restart ntpsec
        else
            log "🔄 Redémarrage du service ntpsec..."
            systemctl restart ntpsec
        fi
        sleep 5
    else
        log "✅ ntpsec fonctionne déjà correctement"
    fi
    
    # Vérifier que le service fonctionne après les modifications
    if systemctl is-active --quiet ntpsec; then
        log "✅ Service ntpsec actif"
        
        # Attendre que ntpq réponde (jusqu'à 30 secondes)
        for i in {1..6}; do
            if ntpq -c peers &> /dev/null; then
                log "✅ ntpq répond correctement"
                break
            else
                warn "⚠️ ntpq ne répond pas encore, attente... ($i/6)"
                sleep 5
            fi
        done
    else
        error "❌ Impossible de démarrer ntpsec"
    fi
}

# Configurer l'application pour utiliser ntpsec
configure_application_for_ntpsec() {
    local app_dir="/home/ntp-monitor/ntp-monitor-enterprise"
    
    if [ -d "$app_dir" ]; then
        log "🔧 Configuration de l'application pour ntpsec..."
        
        if [ -f "$app_dir/.env" ]; then
            # Sauvegarder l'ancien fichier
            sudo -u ntp-monitor cp "$app_dir/.env" "$app_dir/.env.backup"
            
            # Mettre à jour les variables pour ntpsec
            sudo -u ntp-monitor bash << 'EOF'
cd /home/ntp-monitor/ntp-monitor-enterprise
# Supprimer les anciennes variables NTP
sed -i '/^NTP_MONITORING_METHOD=/d' .env
sed -i '/^NTP_COMMAND=/d' .env
sed -i '/^NTP_SERVICE=/d' .env

# Ajouter les nouvelles variables pour ntpsec
echo "# Configuration NTP avec ntpsec" >> .env
echo "NTP_MONITORING_METHOD=ntpsec" >> .env
echo "NTP_COMMAND=ntpq" >> .env
echo "NTP_SERVICE=ntpsec" >> .env
EOF
            
            log "✅ Configuration application mise à jour pour ntpsec"
            
            # Redémarrer l'application si elle est active
            if systemctl is-active --quiet ntp-monitor-enterprise 2>/dev/null; then
                log "🔄 Redémarrage de l'application..."
                systemctl restart ntp-monitor-enterprise
                sleep 3
                if systemctl is-active --quiet ntp-monitor-enterprise; then
                    log "✅ Application redémarrée avec succès"
                else
                    warn "⚠️ Problème lors du redémarrage de l'application"
                fi
            else
                info "ℹ️ Application non active actuellement"
            fi
        else
            warn "⚠️ Fichier .env de l'application non trouvé"
        fi
    else
        info "ℹ️ Application NTP Monitor Enterprise non trouvée"
    fi
}

# Tests finaux complets
run_comprehensive_tests() {
    log "🧪 Tests de validation complets..."
    
    # Test 1: Service ntpsec
    if systemctl is-active --quiet ntpsec; then
        log "✅ Service ntpsec actif"
    else
        error "❌ Service ntpsec inactif"
    fi
    
    # Test 2: ntpq répond
    if ntpq -c peers &> /dev/null; then
        log "✅ ntpq répond correctement"
        
        # Afficher l'état des peers
        log "📊 État des serveurs NTP:"
        ntpq -c peers | head -10
    else
        error "❌ ntpq ne répond pas"
    fi
    
    # Test 3: Services concurrents arrêtés
    local chrony_status=$(systemctl is-active chronyd 2>/dev/null || echo "inactive")
    local timesyncd_status=$(systemctl is-active systemd-timesyncd 2>/dev/null || echo "inactive")
    
    if [ "$chrony_status" = "active" ]; then
        warn "⚠️ chrony est encore actif"
    else
        log "✅ chrony inactif: $chrony_status"
    fi
    
    if [ "$timesyncd_status" = "active" ]; then
        warn "⚠️ systemd-timesyncd est encore actif"
    else
        log "✅ systemd-timesyncd inactif: $timesyncd_status"
    fi
    
    # Test 4: Synchronisation
    local sync_servers=$(ntpq -c peers 2>/dev/null | grep -c "^[*+]" || echo "0")
    if [ "$sync_servers" -gt 0 ]; then
        log "✅ $sync_servers serveur(s) NTP synchronisé(s)"
    else
        warn "⚠️ Aucun serveur NTP synchronisé (peut être normal après redémarrage)"
    fi
    
    # Test 5: Application web si disponible
    if curl -s http://localhost > /dev/null 2>&1; then
        log "✅ Interface web accessible"
    else
        info "ℹ️ Interface web non testable (normal si application non installée)"
    fi
    
    # Test 6: Configuration application
    local app_dir="/home/ntp-monitor/ntp-monitor-enterprise"
    if [ -f "$app_dir/.env" ]; then
        if grep -q "NTP_MONITORING_METHOD=ntpsec" "$app_dir/.env"; then
            log "✅ Application configurée pour ntpsec"
        else
            warn "⚠️ Application pas encore configurée pour ntpsec"
        fi
    fi
}

# Affichage des informations finales
display_final_status() {
    log "🎉 Configuration ntpsec préservée et optimisée !"
    
    echo
    echo "=============================================="
    echo "        NTPSEC - ÉTAT FINAL"
    echo "=============================================="
    echo
    
    # État des services
    echo "🔄 Services de synchronisation temporelle:"
    echo "   - ntpsec: $(systemctl is-active ntpsec 2>/dev/null || echo 'inactif')"
    echo "   - chrony: $(systemctl is-active chronyd 2>/dev/null || echo 'inactif')"
    echo "   - systemd-timesyncd: $(systemctl is-active systemd-timesyncd 2>/dev/null || echo 'inactif')"
    echo
    
    # Informations ntpsec
    echo "🕐 Informations ntpsec:"
    echo "   - Configuration: /etc/ntpsec/ntp.conf"
    echo "   - Logs: /var/log/ntpsec/ntp.log"
    echo "   - Sauvegarde: $(cat /root/last_ntpsec_backup.txt 2>/dev/null || echo 'Aucune')"
    echo
    
    # Statistiques
    if ntpq -c peers &> /dev/null; then
        local total_servers=$(ntpq -c peers 2>/dev/null | tail -n +3 | wc -l)
        local sync_servers=$(ntpq -c peers 2>/dev/null | grep -c "^[*+]" || echo "0")
        echo "📊 Statistiques NTP:"
        echo "   - Serveurs configurés: $total_servers"
        echo "   - Serveurs synchronisés: $sync_servers"
    fi
    
    # Clients connectés
    local clients=$(ss -u -n | grep :123 | wc -l || echo "0")
    if [ "$clients" -gt 0 ]; then
        echo "   - Clients connectés: $clients"
    fi
    echo
    
    # Commandes utiles
    echo "🧪 Commandes de vérification:"
    echo "   - ntpq -c peers"
    echo "   - ntpq -c associations"
    echo "   - systemctl status ntpsec"
    echo "   - journalctl -u ntpsec -f"
    echo
    
    # Application
    if [ -f "/home/ntp-monitor/ntp-monitor-enterprise/.env" ]; then
        echo "🌐 Application NTP Monitor:"
        echo "   - Configuration: ntpsec activé"
        echo "   - Interface: http://192.168.10.45"
        echo
    fi
    
    echo "=============================================="
    log "✅ Votre serveur ntpsec est opérationnel et optimisé !"
}

# Fonction principale
main() {
    log "🚀 Préservation et optimisation de ntpsec existant"
    
    # Sauvegarder avant toute modification
    backup_ntpsec_config
    
    # Arrêter les services concurrents
    stop_conflicting_services
    
    # S'assurer que ntpsec est installé
    ensure_ntpsec_installed
    
    # S'assurer que ntpsec fonctionne
    ensure_ntpsec_running
    
    # Configurer l'application
    configure_application_for_ntpsec
    
    # Tests complets
    run_comprehensive_tests
    
    # Affichage final
    display_final_status
    
    log "🎉 Opération terminée avec succès !"
}

# Exécution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 