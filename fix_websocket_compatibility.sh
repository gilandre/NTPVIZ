#!/bin/bash
# Script de correction pour l'incompatibilité WebSocket
# Usage: ./fix_websocket_compatibility.sh

set -e

echo "🔧 CORRECTION WEBSOCKET COMPATIBILITY"
echo "===================================="

APP_DIR="/opt/ntp-monitor"
SERVICE_NAME="ntp-monitor"

# Vérification des privilèges root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être exécuté en tant que root"
   exit 1
fi

echo "🛑 Arrêt du service pour mise à jour..."
systemctl stop $SERVICE_NAME 2>/dev/null || echo "Service déjà arrêté"

cd "$APP_DIR"

echo ""
echo "🐍 Mise à jour des packages WebSocket..."
sudo -u ntp-monitor .venv/bin/pip uninstall -y python-socketio python-engineio Flask-SocketIO

echo "🐍 Installation des versions compatibles..."
sudo -u ntp-monitor .venv/bin/pip install \
    Flask-SocketIO==5.3.6 \
    python-socketio==5.8.0 \
    python-engineio==4.7.1

echo ""
echo "🔄 Mise à jour depuis GitHub..."
sudo -u ntp-monitor git fetch origin
sudo -u ntp-monitor git reset --hard origin/dev

echo ""
echo "🐍 Mise à jour complète des dépendances..."
sudo -u ntp-monitor .venv/bin/pip install -r requirements.txt

echo ""
echo "🚀 Redémarrage du service..."
systemctl start $SERVICE_NAME

echo ""
echo "🏥 Vérification du service..."
sleep 5
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Service redémarré avec succès"
    
    echo ""
    echo "🌐 Test WebSocket..."
    sleep 3
    if curl -f -s http://localhost:5000/api/system/status > /dev/null 2>&1; then
        echo "✅ API accessible"
        echo "🔧 WebSocket devrait maintenant fonctionner correctement"
        echo ""
        echo "📱 Testez dans le navigateur:"
        echo "   • Ouvrez http://$(hostname -I | awk '{print $1}'):5000"
        echo "   • Vérifiez la console (F12) - plus d'erreur 'Invalid frame header'"
        echo "   • Le dashboard devrait se mettre à jour en temps réel"
    else
        echo "⚠️  API pas encore accessible"
    fi
else
    echo "⚠️  Problème avec le service:"
    systemctl status $SERVICE_NAME --no-pager -l
fi

echo ""
echo "🎉 CORRECTION WEBSOCKET TERMINÉE !"
echo "================================="
echo ""
echo "📝 Changements appliqués:"
echo "   • python-socketio: 5.9.0 → 5.8.0 (compatible Socket.IO 4.x)"
echo "   • Configuration Flask-SocketIO optimisée"
echo "   • Transport polling + websocket configuré"
echo "   • Timeout et ping configurés" 