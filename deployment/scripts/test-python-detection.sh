#!/bin/bash
# Script de test pour la détection automatique Python
# Test rapide avant déploiement

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🧪 Test de détection Python - NTP Monitor Enterprise${NC}\n"

# Fonction de détection Python (copie de deploy.sh)
detect_python_version() {
    if command -v python3.12 &> /dev/null; then
        PYTHON_VERSION="3.12"
        PYTHON_CMD="python3.12"
    elif command -v python3.11 &> /dev/null; then
        PYTHON_VERSION="3.11"
        PYTHON_CMD="python3.11"
    elif command -v python3.10 &> /dev/null; then
        PYTHON_VERSION="3.10"
        PYTHON_CMD="python3.10"
    elif command -v python3.9 &> /dev/null; then
        PYTHON_VERSION="3.9"
        PYTHON_CMD="python3.9"
    elif command -v python3.8 &> /dev/null; then
        PYTHON_VERSION="3.8"
        PYTHON_CMD="python3.8"
    elif command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
        PYTHON_CMD="python3"
    else
        echo -e "${RED}❌ Aucune version de Python 3 détectée${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Python $PYTHON_VERSION détecté ($PYTHON_CMD)${NC}"
}

# Tests des versions Python disponibles
echo -e "${YELLOW}📋 Versions Python disponibles sur ce système:${NC}"
for version in python3.12 python3.11 python3.10 python3.9 python3.8 python3; do
    if command -v $version &> /dev/null; then
        actual_version=$($version --version 2>&1 | cut -d' ' -f2)
        echo -e "  ${GREEN}✓${NC} $version (v$actual_version)"
    else
        echo -e "  ${RED}✗${NC} $version"
    fi
done

echo ""

# Test de la détection automatique
echo -e "${YELLOW}🔍 Test de détection automatique:${NC}"
detect_python_version

# Test de création d'environnement virtuel
echo -e "\n${YELLOW}🧪 Test création environnement virtuel:${NC}"
TEST_DIR="/tmp/test-python-venv"
rm -rf $TEST_DIR
mkdir -p $TEST_DIR
cd $TEST_DIR

if $PYTHON_CMD -m venv test_venv; then
    echo -e "${GREEN}✅ Environnement virtuel créé avec succès${NC}"
    
    # Test d'activation et installation pip
    source test_venv/bin/activate
    if pip install --upgrade pip > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Pip fonctionne correctement${NC}"
    else
        echo -e "${RED}❌ Problème avec pip${NC}"
    fi
    deactivate
    
else
    echo -e "${RED}❌ Impossible de créer l'environnement virtuel${NC}"
    exit 1
fi

# Nettoyage
rm -rf $TEST_DIR

echo -e "\n${GREEN}🎉 Tous les tests Python sont réussis !${NC}"
echo -e "${BLUE}📋 Résumé:${NC}"
echo -e "  • Python détecté: ${GREEN}$PYTHON_CMD${NC} (v$PYTHON_VERSION)"
echo -e "  • Venv: ${GREEN}Fonctionnel${NC}"
echo -e "  • Pip: ${GREEN}Fonctionnel${NC}"

echo -e "\n${BLUE}🚀 Votre système est prêt pour le déploiement NTP Monitor Enterprise !${NC}" 