#!/bin/bash
# ============================================================================
# test_github_links.sh - Test des liens GitHub
# Script pour valider que tous les liens GitHub sont accessibles
# ============================================================================

# === CONFIGURATION ===
USERNAME="gilandre"
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

# === FONCTION TEST URL ===
test_url() {
    local url="$1"
    local description="$2"
    
    log_info "Test: $description"
    
    if curl -s --head --request GET "$url" | grep -q "200 OK"; then
        log_success "✅ $description - URL accessible"
        return 0
    else
        log_error "❌ $description - URL inaccessible: $url"
        return 1
    fi
}

# === FONCTION TEST FICHIER ===
test_file_exists() {
    local file="$1"
    local description="$2"
    
    if [ -f "$file" ]; then
        log_success "✅ $description - Fichier existant"
        return 0
    else
        log_error "❌ $description - Fichier manquant: $file"
        return 1
    fi
}

# === FONCTION TEST CONTENU ===
test_content() {
    local file="$1"
    local search="$2"
    local description="$3"
    
    if [ -f "$file" ] && grep -q "$search" "$file"; then
        log_success "✅ $description - Contenu OK"
        return 0
    else
        log_error "❌ $description - Contenu manquant dans $file"
        return 1
    fi
}

# === TESTS PRINCIPAUX ===
run_tests() {
    log_info "🧪 Tests des liens GitHub pour NTP Monitor Enterprise"
    echo
    
    local success_count=0
    local total_count=0
    
    # Test 1: Repository principal
    ((total_count++))
    if test_url "https://github.com/$USERNAME/$REPO_NAME" "Repository principal"; then
        ((success_count++))
    fi
    
    # Test 2: Script d'installation automatique
    ((total_count++))
    if test_url "https://raw.githubusercontent.com/$USERNAME/$REPO_NAME/$BRANCH/scripts/install_auto.sh" "Script install_auto.sh"; then
        ((success_count++))
    fi
    
    # Test 3: Script de vérification
    ((total_count++))
    if test_url "https://raw.githubusercontent.com/$USERNAME/$REPO_NAME/$BRANCH/scripts/verify_installation.sh" "Script verify_installation.sh"; then
        ((success_count++))
    fi
    
    # Test 4: Documentation DEPLOYMENT_GITHUB.md
    ((total_count++))
    if test_url "https://github.com/$USERNAME/$REPO_NAME/blob/$BRANCH/DEPLOYMENT_GITHUB.md" "Documentation DEPLOYMENT_GITHUB.md"; then
        ((success_count++))
    fi
    
    # Test 5: Documentation INSTALLATION_RAPIDE.md
    ((total_count++))
    if test_url "https://github.com/$USERNAME/$REPO_NAME/blob/$BRANCH/INSTALLATION_RAPIDE.md" "Documentation INSTALLATION_RAPIDE.md"; then
        ((success_count++))
    fi
    
    # Test 6: Documentation GUIDE_DEPLOIEMENT_PRODUCTION.md
    ((total_count++))
    if test_url "https://github.com/$USERNAME/$REPO_NAME/blob/$BRANCH/GUIDE_DEPLOIEMENT_PRODUCTION.md" "Documentation GUIDE_DEPLOIEMENT_PRODUCTION.md"; then
        ((success_count++))
    fi
    
    echo
    log_info "=== TESTS LOCAUX ==="
    
    # Test 7: Fichiers locaux
    local files=(
        "scripts/install_auto.sh:Script d'installation automatique"
        "scripts/verify_installation.sh:Script de vérification"
        "DEPLOYMENT_GITHUB.md:Guide déploiement GitHub"
        "INSTALLATION_RAPIDE.md:Installation rapide"
        "GUIDE_DEPLOIEMENT_PRODUCTION.md:Guide production"
        "DEPLOY.md:Guide déploiement"
        "README.md:Documentation README"
    )
    
    for file_info in "${files[@]}"; do
        IFS=':' read -r file desc <<< "$file_info"
        ((total_count++))
        if test_file_exists "$file" "$desc"; then
            ((success_count++))
        fi
    done
    
    echo
    log_info "=== TESTS CONTENU ==="
    
    # Test 8: Contenu des fichiers
    local content_tests=(
        "scripts/install_auto.sh:$USERNAME:Username dans script installation"
        "DEPLOYMENT_GITHUB.md:$USERNAME:Username dans guide déploiement"
        "INSTALLATION_RAPIDE.md:$USERNAME:Username dans installation rapide"
        "GUIDE_DEPLOIEMENT_PRODUCTION.md:$USERNAME:Username dans guide production"
        "DEPLOY.md:$USERNAME:Username dans guide déploiement"
    )
    
    for content_test in "${content_tests[@]}"; do
        IFS=':' read -r file search desc <<< "$content_test"
        ((total_count++))
        if test_content "$file" "$search" "$desc"; then
            ((success_count++))
        fi
    done
    
    echo
    log_info "=== RÉSULTATS ==="
    
    local percentage=$((success_count * 100 / total_count))
    
    if [ $percentage -eq 100 ]; then
        log_success "🎉 Tous les tests réussis ! ($success_count/$total_count - $percentage%)"
    elif [ $percentage -ge 80 ]; then
        log_warning "⚠️  Tests partiellement réussis ($success_count/$total_count - $percentage%)"
    else
        log_error "❌ Plusieurs tests échoués ($success_count/$total_count - $percentage%)"
    fi
    
    return $((total_count - success_count))
}

# === COMMANDES UTILES ===
show_commands() {
    log_info "🔧 Commandes utiles pour le déploiement GitHub :"
    echo
    echo "📋 Installation automatique :"
    echo "   curl -fsSL https://raw.githubusercontent.com/$USERNAME/$REPO_NAME/$BRANCH/scripts/install_auto.sh | sudo bash"
    echo
    echo "✅ Vérification installation :"
    echo "   curl -fsSL https://raw.githubusercontent.com/$USERNAME/$REPO_NAME/$BRANCH/scripts/verify_installation.sh | bash"
    echo
    echo "📚 Documentation :"
    echo "   - Repository: https://github.com/$USERNAME/$REPO_NAME"
    echo "   - Déploiement: https://github.com/$USERNAME/$REPO_NAME/blob/$BRANCH/DEPLOYMENT_GITHUB.md"
    echo "   - Installation: https://github.com/$USERNAME/$REPO_NAME/blob/$BRANCH/INSTALLATION_RAPIDE.md"
    echo "   - Production: https://github.com/$USERNAME/$REPO_NAME/blob/$BRANCH/GUIDE_DEPLOIEMENT_PRODUCTION.md"
    echo
    echo "🔄 Mise à jour :"
    echo "   git add . && git commit -m 'Update GitHub links' && git push origin $BRANCH"
    echo
}

# === AIDE ===
show_help() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -u, --username USER   Username GitHub (défaut: $USERNAME)"
    echo "  -r, --repo REPO       Nom du repository (défaut: $REPO_NAME)"
    echo "  -b, --branch BRANCH   Branche (défaut: $BRANCH)"
    echo "  -c, --commands        Afficher les commandes utiles"
    echo "  -h, --help            Afficher cette aide"
    echo
    echo "Exemples:"
    echo "  $0                    Lancer tous les tests"
    echo "  $0 -u monusername     Tester avec un autre username"
    echo "  $0 -c                 Afficher les commandes utiles"
}

# === TRAITEMENT ARGUMENTS ===
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--username)
            USERNAME="$2"
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
        -c|--commands)
            show_commands
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
log_info "🚀 Test des liens GitHub pour NTP Monitor Enterprise"
echo
log_info "Configuration:"
echo "  👤 Username: $USERNAME"
echo "  📦 Repository: $REPO_NAME"
echo "  🌿 Branche: $BRANCH"
echo

run_tests
exit_code=$?

echo
if [ $exit_code -eq 0 ]; then
    log_success "🎉 Tous les tests sont réussis ! Le déploiement GitHub est prêt."
    echo
    show_commands
else
    log_error "❌ Certains tests ont échoué. Vérifiez la configuration GitHub."
fi

exit $exit_code 