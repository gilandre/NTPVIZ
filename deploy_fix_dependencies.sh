#!/bin/bash

# Script de déploiement pour correction dépendances NTP Monitor
# Résout les conflits redis/celery et modules manquants

echo "======================================================="
echo "   CORRECTION DÉPENDANCES - DÉPLOIEMENT AUTOMATIQUE   "
echo "======================================================="
echo "Correction des problèmes identifiés :"
echo "- Conflit redis/celery versions"
echo "- Module psutil manquant"
echo "- Dépendances Python incomplètes"
echo ""

# Vérification des privilèges root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être exécuté en tant que root"
   echo "Usage: sudo bash deploy_fix_dependencies.sh"
   exit 1
fi

TEMP_DIR="/tmp/ntp-monitor-deps-fix"
GITHUB_RAW="https://raw.githubusercontent.com/gilandre/NTPVIZ/dev"

# Nettoyage préalable
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

echo "📥 Téléchargement du script de correction des dépendances..."

# Téléchargement du script de correction
if curl -fsSL "$GITHUB_RAW/fix_502_dependencies.sh" -o fix_502_dependencies.sh; then
    echo "✅ Script téléchargé avec succès"
else
    echo "❌ Erreur de téléchargement du script"
    echo "Vérifiez votre connexion Internet et l'URL du dépôt"
    exit 1
fi

# Rendre le script exécutable
chmod +x fix_502_dependencies.sh

echo ""
echo "🚀 Exécution de la correction des dépendances..."
echo "Ce processus peut prendre 5-10 minutes..."
echo ""

# Exécution du script de correction
./fix_502_dependencies.sh

# Vérification finale
echo ""
echo "🔍 Vérification post-correction..."

if systemctl is-active --quiet ntp-monitor; then
    echo "✅ Service ntp-monitor actif"
    if netstat -tlnp 2>/dev/null | grep -q ':5000'; then
        echo "✅ Port 5000 accessible"
        echo ""
        echo "🎉 CORRECTION RÉUSSIE !"
        echo "Application disponible sur : http://79.137.36.66/"
    else
        echo "⚠️ Service actif mais port 5000 non accessible"
    fi
else
    echo "❌ Service ntp-monitor toujours inactif"
    echo "Consultez les logs : journalctl -u ntp-monitor -n 20"
fi

# Nettoyage
cd /
rm -rf "$TEMP_DIR"

echo ""
echo "📋 COMMANDES UTILES"
echo "=================="
echo "Statut service  : systemctl status ntp-monitor"
echo "Logs temps réel : journalctl -u ntp-monitor -f"
echo "Redémarrage     : systemctl restart ntp-monitor"
echo "Test manuel     : cd /opt/ntp-monitor && source .venv/bin/activate && python app.py" 