#!/bin/bash
# update_from_github.sh
# Mise à jour du code depuis GitHub

set -e

echo "🔄 MISE À JOUR DEPUIS GITHUB"
echo "=============================="

# Variables
APP_DIR="/opt/ntp-monitor"
BRANCH="MacDev"
BACKUP_DIR="/opt/backups/ntp-monitor"

# Vérification des prérequis
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root"
    exit 1
fi

# Création du backup
echo "💾 Création du backup..."
mkdir -p $BACKUP_DIR
BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
cp -r $APP_DIR $BACKUP_DIR/$BACKUP_NAME
echo "✅ Backup créé: $BACKUP_DIR/$BACKUP_NAME"

# Arrêt du service
echo "⏹️ Arrêt du service..."
systemctl stop ntp-monitor

# Sauvegarde des fichiers de configuration
echo "📁 Sauvegarde des fichiers de configuration..."
cp $APP_DIR/.env $BACKUP_DIR/.env.backup
cp $APP_DIR/config/config.py $BACKUP_DIR/config.py.backup

# Mise à jour depuis GitHub
echo "📥 Mise à jour depuis GitHub..."
cd $APP_DIR
git fetch origin
git reset --hard origin/$BRANCH
git clean -fd

# Restauration des fichiers de configuration
echo "🔄 Restauration des fichiers de configuration..."
cp $BACKUP_DIR/.env.backup $APP_DIR/.env
cp $BACKUP_DIR/config.py.backup $APP_DIR/config/config.py

# Mise à jour des dépendances Python
echo "🐍 Mise à jour des dépendances Python..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Correction du schéma de base de données
echo "🔧 Correction du schéma de base de données..."
python fix_database_schema.py

# Harmonisation des modèles
echo "🔄 Harmonisation des modèles..."
python harmonize_models.py

# Test de l'application
echo "🧪 Test de l'application..."
python quick_verification.py

# Redémarrage du service
echo "🚀 Redémarrage du service..."
systemctl start ntp-monitor

# Vérification finale
echo "✅ Vérification finale..."
sleep 5
systemctl status ntp-monitor --no-pager

echo "🎉 MISE À JOUR TERMINÉE AVEC SUCCÈS!"
echo "🌐 Application accessible sur: http://$(hostname -I | awk '{print $1}')" 