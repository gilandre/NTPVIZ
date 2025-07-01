#!/bin/bash
# Script de correction pour installer les dépendances MySQL manquantes
# Usage: ./fix_mysql_dependencies.sh

set -e

echo "🔧 CORRECTION DES DÉPENDANCES MYSQL"
echo "=================================="

# Vérification des privilèges root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être exécuté en tant que root"
   exit 1
fi

echo "📦 Installation des dépendances MySQL pour Python..."
apt-get update -qq

# Installation des packages de développement nécessaires
apt-get install -y \
    pkg-config \
    libmysqlclient-dev \
    default-libmysqlclient-dev \
    python3-dev \
    build-essential

echo "✅ Dépendances système installées"

echo ""
echo "🐍 Réinstallation des packages Python..."
APP_DIR="/opt/ntp-monitor"

if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    
    # Activer l'environnement virtuel
    if [ -d ".venv" ]; then
        echo "🔄 Activation de l'environnement virtuel..."
        source .venv/bin/activate
        
        echo "🔄 Mise à jour de pip..."
        pip install --upgrade pip
        
        echo "🔄 Réinstallation de mysqlclient..."
        pip uninstall -y mysqlclient 2>/dev/null || true
        pip install mysqlclient
        
        echo "🔄 Installation des autres dépendances..."
        pip install -r requirements.txt
        
        echo "✅ Packages Python installés avec succès"
    else
        echo "❌ Environnement virtuel non trouvé dans $APP_DIR"
        exit 1
    fi
else
    echo "❌ Répertoire application non trouvé: $APP_DIR"
    exit 1
fi

echo ""
echo "🚀 Redémarrage du service..."
systemctl restart ntp-monitor

echo ""
echo "🏥 Vérification du service..."
sleep 3
if systemctl is-active --quiet ntp-monitor; then
    echo "✅ Service ntp-monitor redémarré avec succès"
else
    echo "⚠️  Problème avec le service, affichage des logs:"
    systemctl status ntp-monitor --no-pager -l
fi

echo ""
echo "🎉 CORRECTION TERMINÉE !"
echo ""
echo "📝 Le service devrait maintenant fonctionner correctement."
echo "📋 Vérifiez avec: systemctl status ntp-monitor" 