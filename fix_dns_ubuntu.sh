#!/bin/bash
# Script de Correction DNS pour Ubuntu 24.04
# Corrige les problèmes de résolution DNS

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
        error "Ce script doit être exécuté en tant que root (sudo)"
        exit 1
    fi
}

section() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

diagnose_dns() {
    section "DIAGNOSTIC DNS"
    
    log "État actuel du DNS..."
    
    # Vérifier systemd-resolved
    if systemctl is-active --quiet systemd-resolved; then
        log "✅ systemd-resolved est actif"
        systemd-resolve --status | head -20
    else
        warn "⚠️ systemd-resolved inactif"
    fi
    
    echo
    log "Configuration DNS actuelle :"
    echo "--- /etc/resolv.conf ---"
    cat /etc/resolv.conf
    
    echo
    log "Test de résolution manuelle :"
    nslookup google.com || echo "❌ Échec nslookup"
    dig google.com @8.8.8.8 +short || echo "❌ Échec dig direct"
}

fix_dns_resolved() {
    section "CORRECTION DNS VIA SYSTEMD-RESOLVED"
    
    log "Configuration systemd-resolved..."
    
    # Sauvegarder configuration actuelle
    cp /etc/systemd/resolved.conf /etc/systemd/resolved.conf.backup
    
    # Créer nouvelle configuration
    cat > /etc/systemd/resolved.conf << 'EOF'
[Resolve]
DNS=8.8.8.8 1.1.1.1 8.8.4.4 1.0.0.1
FallbackDNS=208.67.222.222 208.67.220.220
Domains=~.
DNSSEC=no
DNSOverTLS=no
Cache=yes
DNSStubListener=yes
ReadEtcHosts=yes
EOF
    
    log "✅ Configuration systemd-resolved mise à jour"
    
    # Redémarrer systemd-resolved
    systemctl restart systemd-resolved
    
    # Recréer le lien symbolique
    ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
    
    log "✅ systemd-resolved redémarré"
}

fix_dns_manual() {
    section "CORRECTION DNS MANUELLE"
    
    log "Configuration DNS manuelle..."
    
    # Sauvegarder resolv.conf actuel
    cp /etc/resolv.conf /etc/resolv.conf.backup
    
    # Créer nouvelle configuration DNS
    cat > /etc/resolv.conf << 'EOF'
# Configuration DNS corrigée pour NTP Monitor
nameserver 8.8.8.8
nameserver 1.1.1.1
nameserver 8.8.4.4
nameserver 1.0.0.1
search localdomain
options timeout:2
options attempts:3
options rotate
EOF
    
    log "✅ Configuration DNS manuelle appliquée"
}

fix_dns_netplan() {
    section "CORRECTION DNS VIA NETPLAN"
    
    log "Vérification configuration Netplan..."
    
    # Trouver le fichier netplan actuel
    NETPLAN_FILE=$(find /etc/netplan -name "*.yaml" | head -1)
    
    if [[ -n "$NETPLAN_FILE" ]]; then
        log "Fichier Netplan trouvé : $NETPLAN_FILE"
        
        # Sauvegarder
        cp "$NETPLAN_FILE" "${NETPLAN_FILE}.backup"
        
        # Vérifier si DNS est déjà configuré
        if grep -q "nameservers:" "$NETPLAN_FILE"; then
            log "DNS déjà configuré dans Netplan"
        else
            log "Ajout configuration DNS dans Netplan..."
            
            # Créer configuration temporaire
            cat > /tmp/netplan_dns.yaml << 'EOF'
        nameservers:
          addresses:
            - 8.8.8.8
            - 1.1.1.1
            - 8.8.4.4
            - 1.0.0.1
EOF
            
            # Insérer dans le fichier existant (après la première interface)
            sed -i '/dhcp4: true/a\        nameservers:\n          addresses:\n            - 8.8.8.8\n            - 1.1.1.1\n            - 8.8.4.4\n            - 1.0.0.1' "$NETPLAN_FILE"
            
            log "✅ Configuration DNS ajoutée à Netplan"
            
            # Appliquer la configuration
            netplan apply
            
            log "✅ Configuration Netplan appliquée"
        fi
    else
        warn "⚠️ Aucun fichier Netplan trouvé"
    fi
}

test_dns_resolution() {
    section "TEST RÉSOLUTION DNS"
    
    log "Test des serveurs DNS..."
    
    # Tests multiples
    DOMAINS=("google.com" "github.com" "ubuntu.com" "cloudflare.com")
    
    for domain in "${DOMAINS[@]}"; do
        log "Test résolution $domain..."
        
        if nslookup "$domain" >/dev/null 2>&1; then
            log "✅ $domain : Résolution OK"
        else
            error "❌ $domain : Échec résolution"
        fi
    done
    
    # Test ping
    log "Test ping DNS..."
    if ping -c 1 -W 3 8.8.8.8 >/dev/null 2>&1; then
        log "✅ Ping 8.8.8.8 : OK"
    else
        error "❌ Ping 8.8.8.8 : Échec"
    fi
    
    if ping -c 1 -W 3 google.com >/dev/null 2>&1; then
        log "✅ Ping google.com : OK"
    else
        error "❌ Ping google.com : Échec"
    fi
}

show_final_status() {
    section "STATUT FINAL"
    
    echo
    log "Configuration DNS finale :"
    echo "--- /etc/resolv.conf ---"
    cat /etc/resolv.conf
    
    echo
    log "Test final de résolution :"
    if nslookup github.com >/dev/null 2>&1; then
        log "🎉 DNS CORRIGÉ - Résolution fonctionne !"
        echo
        info "Vous pouvez maintenant relancer :"
        info "sudo ./check_prerequisites.sh"
        echo
        return 0
    else
        error "❌ DNS toujours problématique"
        echo
        warn "Actions supplémentaires possibles :"
        warn "1. Redémarrer le serveur : sudo reboot"
        warn "2. Vérifier configuration réseau"
        warn "3. Contacter l'administrateur réseau"
        echo
        return 1
    fi
}

main() {
    clear
    section "CORRECTION DNS UBUNTU 24.04"
    
    check_root
    
    log "Début de la correction DNS..."
    
    # Diagnostic initial
    diagnose_dns
    
    # Essayer différentes méthodes de correction
    log "Tentative 1 : Correction via systemd-resolved..."
    fix_dns_resolved
    
    sleep 3
    
    # Test intermédiaire
    if nslookup google.com >/dev/null 2>&1; then
        log "✅ DNS corrigé avec systemd-resolved"
    else
        warn "⚠️ systemd-resolved insuffisant, tentative méthode manuelle..."
        fix_dns_manual
        
        sleep 2
        
        if nslookup google.com >/dev/null 2>&1; then
            log "✅ DNS corrigé manuellement"
        else
            warn "⚠️ Tentative via Netplan..."
            fix_dns_netplan
            sleep 3
        fi
    fi
    
    # Tests finaux
    test_dns_resolution
    
    # Statut final
    show_final_status
}

# Exécution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 