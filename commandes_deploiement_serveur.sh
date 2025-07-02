#!/bin/bash

# Commandes de Déploiement sur Serveur 79.137.36.66
# NTP Monitor Enterprise - Déploiement GitHub vers Ubuntu 24.04

echo "=========================================="
echo "  DÉPLOIEMENT SUR SERVEUR 79.137.36.66"
echo "=========================================="

# ÉTAPE 1: CONNEXION AU SERVEUR
echo "1. Connexion au serveur..."
echo "ssh root@79.137.36.66"
echo ""

# ÉTAPE 2: TÉLÉCHARGEMENT DES SCRIPTS DEPUIS GITHUB
echo "2. Téléchargement des scripts depuis GitHub..."
echo ""

# === REMPLACEZ 'votre-username' par votre nom d'utilisateur GitHub ===
GITHUB_USER="votre-username"  # À MODIFIER !
GITHUB_REPO="ntp-monitor"     # À MODIFIER si différent !
GITHUB_BRANCH="main"          # À MODIFIER si branch différente !

echo "# Téléchargement scripts principaux"
echo "wget https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${GITHUB_BRANCH}/deploy_github_ubuntu.sh"
echo "wget https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${GITHUB_BRANCH}/update_from_github.sh"
echo "wget https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${GITHUB_BRANCH}/deploy_config.env"
echo ""

echo "# Alternative avec curl si wget indisponible"
echo "curl -o deploy_github_ubuntu.sh https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${GITHUB_BRANCH}/deploy_github_ubuntu.sh"
echo "curl -o update_from_github.sh https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${GITHUB_BRANCH}/update_from_github.sh"
echo "curl -o deploy_config.env https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${GITHUB_BRANCH}/deploy_config.env"
echo ""

# ÉTAPE 3: CONFIGURATION ET EXÉCUTION
echo "3. Configuration et exécution..."
echo ""
echo "# Permissions exécution"
echo "chmod +x deploy_github_ubuntu.sh update_from_github.sh"
echo ""

echo "# Configuration du repository GitHub dans le script"
echo "nano deploy_github_ubuntu.sh"
echo "# Ligne 13: GITHUB_REPO=\"https://github.com/${GITHUB_USER}/${GITHUB_REPO}.git\""
echo ""

echo "# Exécution du déploiement"
echo "sudo bash deploy_github_ubuntu.sh"
echo ""

# ÉTAPE 4: VÉRIFICATION
echo "4. Vérification post-déploiement..."
echo ""
echo "# Vérifier service"
echo "systemctl status ntp-monitor"
echo ""
echo "# Vérifier port"
echo "ss -tlnp | grep :5000"
echo ""
echo "# Test application"
echo "curl -I http://localhost:5000/"
echo ""

# ÉTAPE 5: ACCÈS
echo "5. Accès à l'application..."
echo ""
echo "# URLs d'accès"
echo "echo \"Application accessible sur :\""
echo "echo \"- URL directe: http://79.137.36.66:5000\""
echo "echo \"- Via Nginx: http://79.137.36.66\""
echo "echo \"- Comptes: admin/admin123, operator/operator123\""
echo ""

echo "=========================================="
echo "  COMMANDES PRÊTES POUR EXÉCUTION"
echo "==========================================" 