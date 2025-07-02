#!/bin/bash

# Commandes Exactes pour Serveur 79.137.36.66
# GitHub: gilandre/NTPVIZ branch dev
# NTP Monitor Enterprise - Déploiement Production

echo "=============================================="
echo "  DÉPLOIEMENT SUR SERVEUR 79.137.36.66"
echo "  GitHub: gilandre/NTPVIZ (branch: dev)"
echo "=============================================="

# Variables configurées
GITHUB_USER="gilandre"
GITHUB_REPO="NTPVIZ"
GITHUB_BRANCH="dev"
SERVER_IP="79.137.36.66"

# URLs exactes des scripts
SCRIPT_BASE_URL="https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${GITHUB_BRANCH}"

echo "🔗 URLs des scripts:"
echo "   ${SCRIPT_BASE_URL}/deploy_github_ubuntu.sh"
echo "   ${SCRIPT_BASE_URL}/update_from_github.sh"
echo "   ${SCRIPT_BASE_URL}/deploy_config.env"
echo ""

echo "📋 COMMANDES À EXÉCUTER SUR LE SERVEUR:"
echo "=========================================="
echo ""

echo "# 1. CONNEXION AU SERVEUR"
echo "ssh root@79.137.36.66"
echo ""

echo "# 2. TÉLÉCHARGEMENT DES SCRIPTS"
echo "wget https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deploy_github_ubuntu.sh"
echo "wget https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/update_from_github.sh"
echo "wget https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deploy_config.env"
echo ""

echo "# 3. PERMISSIONS"
echo "chmod +x deploy_github_ubuntu.sh update_from_github.sh"
echo ""

echo "# 4. CONFIGURATION AUTOMATIQUE"
echo "sed -i 's|votre-username|gilandre|g' deploy_github_ubuntu.sh"
echo "sed -i 's|ntp-monitor|NTPVIZ|g' deploy_github_ubuntu.sh"
echo "sed -i 's|main|dev|g' deploy_github_ubuntu.sh"
echo ""

echo "# 5. DÉPLOIEMENT"
echo "sudo bash deploy_github_ubuntu.sh"
echo ""

echo "# 6. VÉRIFICATION"
echo "systemctl status ntp-monitor"
echo "ss -tlnp | grep :5000"
echo "curl -I http://localhost:5000/"
echo ""

echo "🌐 ACCÈS FINAL:"
echo "   - URL directe: http://79.137.36.66:5000"
echo "   - Via Nginx: http://79.137.36.66"
echo "   - Comptes: admin/admin123, operator/operator123"
echo ""

echo "=============================================="
echo "  PRÊT POUR COPIER-COLLER"
echo "==============================================" 