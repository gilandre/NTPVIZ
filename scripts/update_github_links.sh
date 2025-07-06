#!/bin/bash
# ============================================================================
# update_github_links.sh - Mise à jour des liens GitHub
# Script utilitaire pour mettre à jour le username GitHub dans tous les fichiers
# ============================================================================

# === CONFIGURATION ===
OLD_USERNAME="votre-username"
NEW_USERNAME="gilandre"
REPO_NAME="ntp-monitor-enterprise"
BRANCH="main"

# === COULEURS ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# === FONCTIONS ===
log_info()    { echo -e "${BLUE}ℹ️  $*${NC}"; }
log_success() { echo -e "${GREEN}✅ $*${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $*${NC}"; }
log_error()   { echo -e "${RED}❌ $*${NC}"; }

# === FONCTION PRINCIPALE ===
update_github_links() {
    log_info "Mise à jour des liens GitHub..."
    
    # Fichiers à mettre à jour
    local files=(
        "README.md"
        "DEPLOY.md"
        "DEPLOYMENT_GITHUB.md"
        "INSTALLATION_RAPIDE.md"
        "GUIDE_DEPLOIEMENT_PRODUCTION.md"
        "scripts/install_auto.sh"
    )
    
    local updated_count=0
    
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            log_info "Traitement de $file..."
            
            # Mise à jour username
            if sed -i "s|$OLD_USERNAME|$NEW_USERNAME|g" "$file" 2>/dev/null; then
                log_success "Username mis à jour dans $file"
                ((updated_count++))
            else
                log_warning "Impossible de mettre à jour $file"
            fi
        else
            log_warning "Fichier $file non trouvé"
        fi
    done
    
    log_success "Mise à jour terminée : $updated_count fichiers traités"
}

# === VÉRIFICATION ===
verify_updates() {
    log_info "Vérification des mises à jour..."
    
    # Chercher les occurrences restantes
    local remaining=$(grep -r "$OLD_USERNAME" . --include="*.md" --include="*.sh" 2>/dev/null | wc -l)
    
    if [ "$remaining" -eq 0 ]; then
        log_success "Aucune occurrence de '$OLD_USERNAME' restante"
    else
        log_warning "$remaining occurrence(s) de '$OLD_USERNAME' encore présente(s)"
        log_info "Occurrences restantes :"
        grep -r "$OLD_USERNAME" . --include="*.md" --include="*.sh" 2>/dev/null
    fi
}

# === GÉNÉRATION LIENS ===
generate_links() {
    log_info "Liens GitHub générés :"
    echo
    echo "📋 Repository principal :"
    echo "   https://github.com/$NEW_USERNAME/$REPO_NAME"
    echo
    echo "🚀 Installation automatique :"
    echo "   curl -fsSL https://raw.githubusercontent.com/$NEW_USERNAME/$REPO_NAME/$BRANCH/scripts/install_auto.sh | sudo bash"
    echo
    echo "✅ Vérification installation :"
    echo "   curl -fsSL https://raw.githubusercontent.com/$NEW_USERNAME/$REPO_NAME/$BRANCH/scripts/verify_installation.sh | bash"
    echo
    echo "📚 Documentation :"
    echo "   - Guide déploiement: https://github.com/$NEW_USERNAME/$REPO_NAME/blob/$BRANCH/DEPLOYMENT_GITHUB.md"
    echo "   - Installation rapide: https://github.com/$NEW_USERNAME/$REPO_NAME/blob/$BRANCH/INSTALLATION_RAPIDE.md"
    echo "   - Production: https://github.com/$NEW_USERNAME/$REPO_NAME/blob/$BRANCH/GUIDE_DEPLOIEMENT_PRODUCTION.md"
    echo
}

# === RÉSUMÉ CONFIGURATION ===
show_summary() {
    log_info "=== RÉSUMÉ CONFIGURATION ==="
    echo "👤 Username GitHub : $NEW_USERNAME"
    echo "📦 Repository      : $REPO_NAME"
    echo "🌿 Branche        : $BRANCH"
    echo
    echo "🔗 URL Repository  : https://github.com/$NEW_USERNAME/$REPO_NAME"
    echo "🔗 Script install : https://raw.githubusercontent.com/$NEW_USERNAME/$REPO_NAME/$BRANCH/scripts/install_auto.sh"
    echo
}

# === AIDE ===
show_help() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -u, --username USER   Nouveau username GitHub (défaut: $NEW_USERNAME)"
    echo "  -r, --repo REPO       Nom du repository (défaut: $REPO_NAME)"
    echo "  -b, --branch BRANCH   Branche (défaut: $BRANCH)"
    echo "  -v, --verify          Vérifier seulement"
    echo "  -l, --links           Générer les liens seulement"
    echo "  -h, --help            Afficher cette aide"
    echo
    echo "Exemples:"
    echo "  $0                    Mise à jour avec paramètres par défaut"
    echo "  $0 -u monusername     Changer le username"
    echo "  $0 -v                 Vérifier les occurrences"
    echo "  $0 -l                 Afficher les liens"
}

# === TRAITEMENT ARGUMENTS ===
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--username)
            NEW_USERNAME="$2"
            shift 2
            ;;
        -r|--repo)
            REPO_NAME="$2"
            shift 2
            ;;
        -b|--branch)
            BRANCH="$2"
            shift 2
            ;;
        -v|--verify)
            verify_updates
            exit 0
            ;;
        -l|--links)
            generate_links
            exit 0
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
done

# === EXÉCUTION PRINCIPALE ===
log_info "🚀 Mise à jour des liens GitHub pour NTP Monitor Enterprise"
echo

show_summary

read -p "Continuer avec cette configuration ? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Opération annulée"
    exit 0
fi

# Mise à jour
update_github_links

# Vérification
verify_updates

# Liens finaux
echo
generate_links

log_success "🎉 Mise à jour des liens GitHub terminée !"
echo
log_info "Prochaines étapes :"
echo "  1. Vérifiez que tous les liens sont corrects"
echo "  2. Committez les changements : git add . && git commit -m 'Update GitHub links'"
echo "  3. Poussez vers GitHub : git push origin main"
echo "  4. Testez l'installation automatique"

exit 0 