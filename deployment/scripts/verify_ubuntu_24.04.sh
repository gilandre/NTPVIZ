#!/bin/bash
# Script de vérification pour Ubuntu 24.04
# Vérifie que l'application est prête pour la production

set -e

echo "🔍 Vérification Ubuntu 24.04 - NTP Monitor Enterprise"
echo "======================================================"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Vérification du système
check_os() {
    log_info "Vérification du système d'exploitation..."
    
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        if [[ "$ID" == "ubuntu" && "$VERSION_ID" == "24.04" ]]; then
            log_success "Ubuntu 24.04 détecté"
        else
            log_warning "Système détecté: $PRETTY_NAME"
            log_warning "Testé sur Ubuntu 24.04, mais peut fonctionner sur d'autres versions"
        fi
    else
        log_warning "Impossible de détecter la version du système"
    fi
}

# Vérification de Python
check_python() {
    log_info "Vérification de Python..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Python $PYTHON_VERSION détecté"
        
        # Vérifier la version minimale (3.9+)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [[ $PYTHON_MAJOR -ge 3 && $PYTHON_MINOR -ge 9 ]]; then
            log_success "Version Python compatible (3.9+)"
        else
            log_error "Version Python trop ancienne. Requis: 3.9+"
            return 1
        fi
    else
        log_error "Python 3 non installé"
        return 1
    fi
}

# Vérification des dépendances système
check_system_deps() {
    log_info "Vérification des dépendances système..."
    
    DEPS=("git" "mysql" "curl" "wget")
    MISSING_DEPS=()
    
    for dep in "${DEPS[@]}"; do
        if command -v $dep &> /dev/null; then
            log_success "$dep installé"
        else
            log_warning "$dep manquant"
            MISSING_DEPS+=($dep)
        fi
    done
    
    if [[ ${#MISSING_DEPS[@]} -gt 0 ]]; then
        log_warning "Dépendances manquantes: ${MISSING_DEPS[*]}"
        log_info "Installation avec: sudo apt-get install ${MISSING_DEPS[*]}"
    fi
}

# Vérification de l'application
check_app() {
    log_info "Vérification de l'application..."
    
    # Vérifier les fichiers essentiels
    ESSENTIAL_FILES=(
        "app.py"
        "requirements.txt"
        "backend/"
        "frontend/"
        "config/"
        "deployment/"
        "README.md"
    )
    
    MISSING_FILES=()
    for file in "${ESSENTIAL_FILES[@]}"; do
        if [[ -e "$file" ]]; then
            log_success "$file présent"
        else
            log_error "$file manquant"
            MISSING_FILES+=($file)
        fi
    done
    
    if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
        log_error "Fichiers essentiels manquants: ${MISSING_FILES[*]}"
        return 1
    fi
}

# Vérification des dépendances Python
check_python_deps() {
    log_info "Vérification des dépendances Python..."
    
    if [[ -f "requirements.txt" ]]; then
        log_success "requirements.txt présent"
        
        # Vérifier si l'environnement virtuel existe
        if [[ -d ".venv" ]]; then
            log_success "Environnement virtuel détecté"
            
            # Vérifier les packages installés
            if .venv/bin/pip list | grep -q "Flask"; then
                log_success "Flask installé"
            else
                log_warning "Flask non installé"
            fi
            
            if .venv/bin/pip list | grep -q "PyMySQL"; then
                log_success "PyMySQL installé"
            else
                log_warning "PyMySQL non installé"
            fi
        else
            log_warning "Environnement virtuel non détecté"
            log_info "Création avec: python3 -m venv .venv"
        fi
    else
        log_error "requirements.txt manquant"
        return 1
    fi
}

# Vérification de la base de données
check_database() {
    log_info "Vérification de la base de données..."
    
    if command -v mysql &> /dev/null; then
        log_success "MySQL installé"
        
        # Vérifier si le service MySQL fonctionne
        if systemctl is-active --quiet mysql; then
            log_success "Service MySQL actif"
        else
            log_warning "Service MySQL inactif"
            log_info "Démarrage avec: sudo systemctl start mysql"
        fi
    else
        log_warning "MySQL non installé"
        log_info "Installation avec: sudo apt-get install mysql-server"
    fi
}

# Vérification de la configuration
check_config() {
    log_info "Vérification de la configuration..."
    
    if [[ -f ".env" ]]; then
        log_success "Fichier .env présent"
        
        # Vérifier les variables essentielles
        if grep -q "DATABASE_URL" .env; then
            log_success "DATABASE_URL configuré"
        else
            log_warning "DATABASE_URL manquant dans .env"
        fi
        
        if grep -q "SECRET_KEY" .env; then
            log_success "SECRET_KEY configuré"
        else
            log_warning "SECRET_KEY manquant dans .env"
        fi
    else
        log_warning "Fichier .env manquant"
        log_info "Création avec: cp env.example .env"
    fi
}

# Test de l'application
test_app() {
    log_info "Test de l'application..."
    
    if [[ -d ".venv" ]]; then
        # Tester l'import des modules
        if .venv/bin/python -c "import flask; print('Flask OK')" 2>/dev/null; then
            log_success "Import Flask réussi"
        else
            log_error "Import Flask échoué"
            return 1
        fi
        
        if .venv/bin/python -c "import pymysql; print('PyMySQL OK')" 2>/dev/null; then
            log_success "Import PyMySQL réussi"
        else
            log_error "Import PyMySQL échoué"
            return 1
        fi
        
        # Tester l'application
        if .venv/bin/python -c "from backend.app import create_app; app = create_app(); print('App OK')" 2>/dev/null; then
            log_success "Création de l'application réussie"
        else
            log_error "Création de l'application échouée"
            return 1
        fi
    else
        log_warning "Environnement virtuel non disponible pour les tests"
    fi
}

# Résumé
print_summary() {
    echo ""
    echo "📊 RÉSUMÉ DE LA VÉRIFICATION"
    echo "============================"
    
    if [[ $ERRORS -eq 0 ]]; then
        log_success "✅ Application prête pour Ubuntu 24.04"
        echo ""
        echo "🚀 Prochaines étapes:"
        echo "  1. sudo ./deployment/scripts/install.sh"
        echo "  2. sudo systemctl start ntp-monitor"
        echo "  3. sudo systemctl enable ntp-monitor"
        echo "  4. Accéder à http://localhost:5000"
    else
        log_error "❌ $ERRORS problème(s) détecté(s)"
        echo ""
        echo "🔧 Actions recommandées:"
        echo "  1. Installer les dépendances manquantes"
        echo "  2. Configurer l'environnement virtuel"
        echo "  3. Configurer la base de données"
        echo "  4. Relancer la vérification"
    fi
}

# Fonction principale
main() {
    ERRORS=0
    
    check_os || ((ERRORS++))
    check_python || ((ERRORS++))
    check_system_deps
    check_app || ((ERRORS++))
    check_python_deps || ((ERRORS++))
    check_database
    check_config
    test_app || ((ERRORS++))
    
    print_summary
    
    exit $ERRORS
}

main 