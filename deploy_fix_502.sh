#!/bin/bash

# Script de déploiement rapide pour corriger l'erreur 502
# Usage: curl -fsSL https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deploy_fix_502.sh | sudo bash

echo "======================================================="
echo "   DÉPLOIEMENT RAPIDE - CORRECTION ERREUR 502        "
echo "======================================================="
echo "Téléchargement et exécution du script de correction..."
echo ""

# Vérification des privilèges root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être exécuté en tant que root"
   echo "Usage: sudo bash deploy_fix_502.sh"
   exit 1
fi

TEMP_DIR="/tmp/ntp-monitor-fix"
GITHUB_RAW="https://raw.githubusercontent.com/gilandre/NTPVIZ/dev"

# Nettoyage préalable
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

echo "📥 Téléchargement du script de correction..."

# Téléchargement du script de correction
if curl -fsSL "$GITHUB_RAW/fix_502_complete.sh" -o fix_502_complete.sh; then
    echo "✅ Script téléchargé avec succès"
else
    echo "❌ Erreur de téléchargement du script"
    echo "Vérifiez votre connexion Internet et l'URL du dépôt"
    exit 1
fi

# Rendre le script exécutable
chmod +x fix_502_complete.sh

echo ""
echo "🚀 Exécution de la correction..."
echo "Ce processus peut prendre quelques minutes..."
echo ""

# Exécution du script de correction
./fix_502_complete.sh

# Nettoyage
cd /
rm -rf "$TEMP_DIR"

echo ""
echo "🎯 DÉPLOIEMENT TERMINÉ"
echo "====================="
echo ""
echo "Pour vérifier l'état du service :"
echo "  systemctl status ntp-monitor"
echo ""
echo "Pour voir les logs en temps réel :"
echo "  journalctl -u ntp-monitor -f"
echo ""
echo "L'application devrait être accessible sur :"
echo "  http://79.137.36.66/" 