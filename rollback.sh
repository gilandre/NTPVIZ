#!/bin/bash
# rollback.sh
# Rollback vers une version précédente

set -e

echo "🔄 ROLLBACK"
echo "============"

# Variables
APP_DIR="/opt/ntp-monitor"
BACKUP_DIR="/opt/backups/ntp-monitor"

# Vérification des prérequis
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root"
    exit 1
fi

# Liste des backups disponibles
echo "📋 Backups disponibles:"
ls -la $BACKUP_DIR

# Sélection du backup
read -p "Entrez le nom du backup à restaurer: " BACKUP_NAME

if [ ! -d "$BACKUP_DIR/$BACKUP_NAME" ]; then
    echo "❌ Backup non trouvé: $BACKUP_NAME"
    exit 1
fi

# Arrêt du service
echo "⏹️ Arrêt du service..."
systemctl stop ntp-monitor

# Restauration
echo "🔄 Restauration du backup..."
rm -rf $APP_DIR
cp -r $BACKUP_DIR/$BACKUP_NAME $APP_DIR

# Redémarrage du service
echo "🚀 Redémarrage du service..."
systemctl start ntp-monitor

# Vérification finale
echo "✅ Vérification finale..."
sleep 5
systemctl status ntp-monitor --no-pager

echo "🎉 ROLLBACK TERMINÉ AVEC SUCCÈS!" 