#!/bin/bash
# fix_python_dependencies.sh
# Correction des dépendances Python sur le serveur Ubuntu

set -e

echo "🔧 CORRECTION DES DÉPENDANCES PYTHON"
echo "======================================"

# Variables
APP_DIR="/opt/ntp-monitor"

# Vérification des prérequis
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root"
    exit 1
fi

if [ ! -d "$APP_DIR" ]; then
    echo "❌ Répertoire de l'application non trouvé: $APP_DIR"
    exit 1
fi

echo "📁 Répertoire de l'application: $APP_DIR"

# Activation de l'environnement virtuel
echo "🐍 Activation de l'environnement virtuel..."
cd $APP_DIR
source .venv/bin/activate

# Vérification de l'environnement virtuel
echo "✅ Environnement virtuel activé: $(which python)"
echo "✅ Version Python: $(python --version)"

# Mise à jour de pip
echo "📦 Mise à jour de pip..."
pip install --upgrade pip

# Installation des dépendances de base
echo "📦 Installation des dépendances de base..."
pip install flask flask-login flask-socketio sqlalchemy pymysql

# Installation complète depuis requirements.txt
echo "📦 Installation complète depuis requirements.txt..."
pip install -r requirements.txt

# Vérification des modules installés
echo "🔍 Vérification des modules installés..."
python -c "import flask; print('✅ Flask installé')"
python -c "import flask_login; print('✅ Flask-Login installé')"
python -c "import flask_socketio; print('✅ Flask-SocketIO installé')"
python -c "import sqlalchemy; print('✅ SQLAlchemy installé')"
python -c "import pymysql; print('✅ PyMySQL installé')"

# Test de l'application
echo "🧪 Test de l'application..."
python quick_verification.py

echo "🎉 CORRECTION DES DÉPENDANCES TERMINÉE AVEC SUCCÈS!" 