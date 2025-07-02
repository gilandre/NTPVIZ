#!/bin/bash

# Script de Déploiement NTP Monitor Enterprise
# Serveur: 79.137.36.66
# À exécuter directement sur le serveur

echo "=============================================="
echo "  DÉPLOIEMENT NTP MONITOR - 79.137.36.66"
echo "=============================================="

# Variables configurées pour gilandre/NTPVIZ
GITHUB_USER="gilandre"        # ✅ Configuré
GITHUB_REPO="NTPVIZ"          # ✅ Configuré
GITHUB_BRANCH="dev"           # ✅ Configuré
SERVER_IP="79.137.36.66"

echo "🔧 Configuration:"
echo "   GitHub User: $GITHUB_USER"
echo "   Repository: $GITHUB_REPO"
echo "   Branch: $GITHUB_BRANCH"
echo "   Serveur: $SERVER_IP"
echo ""

# Variables configurées automatiquement pour gilandre/NTPVIZ
echo "✅ Configuration GitHub validée"

echo "1. Mise à jour système..."
apt update -qq

echo "2. Installation outils requis..."
apt install -y wget curl

echo "3. Téléchargement scripts depuis GitHub..."

# URLs des scripts
SCRIPT_BASE_URL="https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${GITHUB_BRANCH}"

echo "   - Téléchargement deploy_github_ubuntu.sh..."
if wget "${SCRIPT_BASE_URL}/deploy_github_ubuntu.sh" -O deploy_github_ubuntu.sh; then
    echo "   ✅ deploy_github_ubuntu.sh téléchargé"
else
    echo "   ❌ Échec téléchargement deploy_github_ubuntu.sh"
    echo "   Vérifiez l'URL: ${SCRIPT_BASE_URL}/deploy_github_ubuntu.sh"
    exit 1
fi

echo "   - Téléchargement update_from_github.sh..."
if wget "${SCRIPT_BASE_URL}/update_from_github.sh" -O update_from_github.sh; then
    echo "   ✅ update_from_github.sh téléchargé"
else
    echo "   ⚠️ update_from_github.sh non téléchargé (optionnel)"
fi

echo "   - Téléchargement deploy_config.env..."
if wget "${SCRIPT_BASE_URL}/deploy_config.env" -O deploy_config.env; then
    echo "   ✅ deploy_config.env téléchargé"
else
    echo "   ⚠️ deploy_config.env non téléchargé (optionnel)"
fi

echo "4. Configuration permissions..."
chmod +x deploy_github_ubuntu.sh update_from_github.sh 2>/dev/null

echo "5. Configuration du script principal..."
# Configuration automatique de l'URL GitHub dans le script
sed -i "s|votre-username|${GITHUB_USER}|g" deploy_github_ubuntu.sh
sed -i "s|ntp-monitor|${GITHUB_REPO}|g" deploy_github_ubuntu.sh
sed -i "s|main|${GITHUB_BRANCH}|g" deploy_github_ubuntu.sh

echo "   ✅ Script configuré avec:"
echo "   - Repository: https://github.com/${GITHUB_USER}/${GITHUB_REPO}.git"
echo "   - Branch: ${GITHUB_BRANCH}"

echo ""
echo "=============================================="
echo "  PRÊT POUR LE DÉPLOIEMENT"
echo "=============================================="
echo ""
echo "6. Exécution du déploiement..."
echo "   Lancement de deploy_github_ubuntu.sh..."
echo ""

# Exécution du script principal
if [[ -f "deploy_github_ubuntu.sh" ]]; then
    bash deploy_github_ubuntu.sh
else
    echo "❌ Script deploy_github_ubuntu.sh non trouvé"
    exit 1
fi

echo ""
echo "=============================================="
echo "         DÉPLOIEMENT TERMINÉ"
echo "=============================================="
echo ""
echo "🌐 Accès à l'application:"
echo "   - URL directe: http://${SERVER_IP}:5000"
echo "   - Via Nginx: http://${SERVER_IP}"
echo ""
echo "👤 Comptes par défaut:"
echo "   - admin / admin123"
echo "   - operator / operator123" 
echo "   - viewer / viewer123"
echo ""
echo "🔧 Commandes utiles:"
echo "   - Status: systemctl status ntp-monitor"
echo "   - Logs: journalctl -u ntp-monitor -f"
echo "   - Redémarrage: systemctl restart ntp-monitor"
echo ""
echo "✅ NTP Monitor Enterprise déployé avec succès!" 