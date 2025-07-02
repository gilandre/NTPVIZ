#!/bin/bash
# Script de déploiement rapide pour corriger SQLAlchemy et service systemd
# Usage: curl -sSL https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/quick_fix_deployment.sh | sudo bash

set -e

echo "🚀 DÉPLOIEMENT RAPIDE - CORRECTIONS NTP MONITOR"
echo "==============================================="

# Vérification des privilèges root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être exécuté en tant que root"
   exit 1
fi

APP_DIR="/opt/ntp-monitor"
GITHUB_REPO="https://raw.githubusercontent.com/gilandre/NTPVIZ/dev"

echo ""
echo "📥 Téléchargement du script de correction..."

# Télécharger le script de correction principal
curl -sSL "$GITHUB_REPO/fix_sqlalchemy_and_service.sh" -o /tmp/fix_sqlalchemy_and_service.sh
chmod +x /tmp/fix_sqlalchemy_and_service.sh

echo "✅ Script téléchargé"

echo ""
echo "🔧 Mise à jour du code application avec les corrections SQLAlchemy..."

# Sauvegarder les fichiers existants
if [ -d "$APP_DIR" ]; then
    echo "📦 Sauvegarde des fichiers existants..."
    cp "$APP_DIR/backend/api/main.py" "$APP_DIR/backend/api/main.py.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    
    # Télécharger les fichiers corrigés
    echo "📥 Téléchargement des corrections SQLAlchemy..."
    
    # Correction API principale
    curl -sSL "$GITHUB_REPO/backend/api/main.py" -o "$APP_DIR/backend/api/main.py"
    
    # Correction script de debug
    mkdir -p "$APP_DIR/deployment/scripts"
    curl -sSL "$GITHUB_REPO/deployment/scripts/debug-500-advanced.sh" -o "$APP_DIR/deployment/scripts/debug-500-advanced.sh"
    chmod +x "$APP_DIR/deployment/scripts/debug-500-advanced.sh"
    
    echo "✅ Fichiers corrigés téléchargés"
fi

echo ""
echo "🔧 Exécution du script de correction complet..."

# Exécuter le script de correction
/tmp/fix_sqlalchemy_and_service.sh

echo ""
echo "🧹 Nettoyage..."
rm -f /tmp/fix_sqlalchemy_and_service.sh

echo ""
echo "🎉 DÉPLOIEMENT RAPIDE TERMINÉ !"
echo "=============================="
echo ""
echo "🔗 Application disponible sur: http://$(hostname -I | awk '{print $1}'):5000"
echo "👤 Login: admin / admin123"
echo ""
echo "📋 Commandes utiles :"
echo "   • systemctl status ntp-monitor"
echo "   • journalctl -u ntp-monitor -f"
echo "   • systemctl restart ntp-monitor"
echo ""
echo "✅ SQLAlchemy 2.x : Corrections appliquées"
echo "✅ Service systemd : Créé et démarré"
echo "✅ Base de données : Configurée" 