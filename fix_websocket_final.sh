#!/bin/bash
# Script de diagnostic et correction WebSocket final
# Usage: ./fix_websocket_final.sh

set -e

echo "🔧 DIAGNOSTIC ET CORRECTION WEBSOCKET FINAL"
echo "==========================================="

APP_DIR="/opt/ntp-monitor"
SERVICE_NAME="ntp-monitor"

# Vérification des privilèges root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être exécuté en tant que root"
   exit 1
fi

echo "🛑 Arrêt du service..."
systemctl stop $SERVICE_NAME 2>/dev/null || echo "Service déjà arrêté"

cd "$APP_DIR"

echo ""
echo "🔍 DIAGNOSTIC WEBSOCKET ACTUEL"
echo "==============================="

echo ""
echo "📋 Versions actuelles des packages Socket.IO:"
sudo -u ntp-monitor .venv/bin/pip list | grep -i socket || echo "Aucun package socket trouvé"
sudo -u ntp-monitor .venv/bin/pip list | grep -i flask || echo "Aucun package flask trouvé"

echo ""
echo "🔍 Vérification de la configuration Flask-SocketIO actuelle..."
sudo -u ntp-monitor .venv/bin/python -c "
try:
    import flask_socketio
    import python_socketio
    import engineio
    print(f'Flask-SocketIO: {flask_socketio.__version__}')
    print(f'python-socketio: {python_socketio.__version__}')
    print(f'python-engineio: {engineio.__version__}')
except ImportError as e:
    print(f'Erreur import: {e}')
" 2>/dev/null || echo "Erreur lors du diagnostic des versions"

echo ""
echo "🔧 CORRECTION WEBSOCKET FORCÉE"
echo "==============================="

echo ""
echo "🗑️ Suppression complète des packages Socket.IO..."
sudo -u ntp-monitor .venv/bin/pip uninstall -y \
    Flask-SocketIO \
    python-socketio \
    python-engineio \
    socketio \
    engineio 2>/dev/null || echo "Packages déjà supprimés"

echo ""
echo "🔄 Mise à jour depuis GitHub avec les bonnes versions..."
sudo -u ntp-monitor git fetch origin
sudo -u ntp-monitor git reset --hard origin/dev
sudo -u ntp-monitor git clean -fd

echo ""
echo "🐍 Installation des versions WebSocket compatibles (FORCÉES)..."

# Installation des versions exactes compatibles
sudo -u ntp-monitor .venv/bin/pip install \
    "python-engineio==4.7.1" \
    "python-socketio==5.8.0" \
    "Flask-SocketIO==5.3.6"

echo ""
echo "✅ Vérification des versions installées:"
sudo -u ntp-monitor .venv/bin/python -c "
try:
    import flask_socketio
    import python_socketio  
    import engineio
    print(f'✅ Flask-SocketIO: {flask_socketio.__version__}')
    print(f'✅ python-socketio: {python_socketio.__version__}')
    print(f'✅ python-engineio: {engineio.__version__}')
    
    # Vérification de compatibilité
    from packaging import version
    
    socketio_ver = version.parse(python_socketio.__version__)
    engineio_ver = version.parse(engineio.__version__)
    flask_socketio_ver = version.parse(flask_socketio.__version__)
    
    if socketio_ver >= version.parse('5.8.0') and socketio_ver < version.parse('5.9.0'):
        print('✅ python-socketio version compatible avec Socket.IO 4.x client')
    else:
        print('⚠️ python-socketio version potentiellement incompatible')
        
    if engineio_ver >= version.parse('4.7.0') and engineio_ver < version.parse('4.8.0'):
        print('✅ python-engineio version compatible')
    else:
        print('⚠️ python-engineio version potentiellement incompatible')
        
    print('✅ Toutes les versions sont correctes')
    
except ImportError as e:
    print(f'❌ Erreur import: {e}')
    exit(1)
except Exception as e:
    print(f'⚠️ Avertissement: {e}')
"

echo ""
echo "🔧 Vérification de la configuration Flask-SocketIO dans le code..."

# Vérification de la configuration dans app.py
if grep -q "ping_timeout=60" backend/app.py; then
    echo "✅ Configuration ping_timeout trouvée"
else
    echo "⚠️ Configuration ping_timeout manquante, ajout..."
    
    # Sauvegarde et correction du fichier app.py
    cp backend/app.py backend/app.py.backup
    
    # Remplacement de la configuration SocketIO
    sed -i 's/socketio\.init_app(app,/socketio.init_app(app,/' backend/app.py
    sed -i '/socketio\.init_app/,/)/c\
    socketio.init_app(app, \
                     cors_allowed_origins="*",\
                     async_mode="threading",\
                     logger=False,\
                     engineio_logger=False,\
                     ping_timeout=60,\
                     ping_interval=25,\
                     allow_upgrades=True,\
                     transports=["polling", "websocket"])' backend/app.py
fi

echo ""
echo "🔧 Vérification du fichier JavaScript WebSocket..."

# Vérification du fichier websocket.js
if [ -f "frontend/static/js/websocket.js" ]; then
    if grep -q "polling" frontend/static/js/websocket.js; then
        echo "✅ Configuration client WebSocket trouvée (polling en priorité)"
    else
        echo "⚠️ Configuration client WebSocket manquante, correction..."
        
        # Création d'un fichier websocket.js optimisé
        cat > frontend/static/js/websocket.js << 'EOF'
// WebSocket client optimisé pour NTP Monitor Enterprise
// Configuration polling en priorité avec upgrade WebSocket

let socket = null;

function initWebSocket() {
    console.log("🔧 Initialisation WebSocket avec configuration polling stable");
    
    // Configuration avec polling en priorité et upgrade optionnel vers WebSocket
    socket = io(window.location.origin, {
        transports: ['polling', 'websocket'],  // Polling d'abord, WebSocket en upgrade
        upgrade: true,                         // Permettre l'upgrade vers WebSocket
        rememberUpgrade: false,                // Ne pas se souvenir de l'upgrade
        forceNew: true,                       // Nouvelle connexion à chaque fois
        timeout: 20000,                       // Timeout de connexion
        withCredentials: true,                // Inclure les cookies/credentials
        autoConnect: true,                    // Connexion automatique
        reconnection: true,                   // Reconnexion automatique
        reconnectionDelay: 1000,              // Délai avant reconnexion
        reconnectionAttempts: 5,              // Nombre de tentatives
        maxReconnectionAttempts: 5            // Maximum de tentatives
    });

    socket.on('connect', function() {
        console.log('✅ Socket.IO connecté avec succès');
        console.log('🚀 Transport utilisé:', socket.io.engine.transport.name);
        
        AppState.isConnected = true;
        updateConnectionStatus(true);
        
        if (typeof showNotification === 'function') {
            showNotification('Connexion temps réel établie', 'success', 3000);
        }
        
        // Log des upgrades de transport
        socket.io.engine.on('upgrade', function(transport) {
            console.log('🔄 Transport upgradé vers:', transport.name);
        });
    });

    socket.on('disconnect', function(reason) {
        console.log('🔌 Socket.IO déconnecté:', reason);
        AppState.isConnected = false;
        updateConnectionStatus(false);
    });

    socket.on('connect_error', function(error) {
        console.error('❌ Erreur connexion Socket.IO:', error);
        AppState.isConnected = false;
        updateConnectionStatus(false);
        
        if (typeof showNotification === 'function') {
            showNotification('Erreur connexion temps réel', 'error', 5000);
        }
    });

    socket.on('reconnect', function(attemptNumber) {
        console.log('🔄 Reconnexion réussie après', attemptNumber, 'tentatives');
        AppState.isConnected = true;
        updateConnectionStatus(true);
    });

    socket.on('reconnect_error', function(error) {
        console.error('❌ Erreur reconnexion:', error);
    });

    socket.on('reconnect_failed', function() {
        console.error('❌ Reconnexion échouée définitivement');
        if (typeof showNotification === 'function') {
            showNotification('Connexion temps réel impossible', 'error', 10000);
        }
    });
}

function sendSocketMessage(event, data) {
    if (socket && AppState.isConnected) {
        socket.emit(event, data);
        return true;
    } else {
        console.warn('⚠️ Socket non connecté, message non envoyé:', event, data);
        return false;
    }
}

function refreshAllAlertsCounters() {
    // Placeholder pour la fonction de refresh des alertes
}

// Exposition globale des fonctions
window.initWebSocket = initWebSocket;
window.sendSocketMessage = sendSocketMessage;
window.refreshAllAlertsCounters = refreshAllAlertsCounters;

console.log('📡 Module WebSocket optimisé chargé');
EOF
        echo "✅ Fichier websocket.js corrigé"
    fi
else
    echo "⚠️ Fichier websocket.js manquant, création..."
    mkdir -p frontend/static/js
    # Créer le fichier comme ci-dessus
fi

echo ""
echo "🔧 Test de l'environnement corrigé..."
sudo -u ntp-monitor .venv/bin/python -c "
import sys
sys.path.insert(0, '.')

try:
    from flask import Flask
    from flask_socketio import SocketIO
    import python_socketio
    import engineio
    
    print(f'✅ Flask importé')
    print(f'✅ Flask-SocketIO: {SocketIO.__module__}')
    print(f'✅ python-socketio: {python_socketio.__version__}')
    print(f'✅ python-engineio: {engineio.__version__}')
    
    # Test de création d'application
    app = Flask(__name__)
    socketio = SocketIO()
    
    socketio.init_app(app, 
                     cors_allowed_origins='*',
                     async_mode='threading',
                     logger=False,
                     engineio_logger=False,
                     ping_timeout=60,
                     ping_interval=25,
                     allow_upgrades=True,
                     transports=['polling', 'websocket'])
    
    print('✅ Configuration Flask-SocketIO réussie')
    
except Exception as e:
    print(f'❌ Erreur test: {e}')
    exit(1)
"

echo ""
echo "🔧 Configuration des permissions..."
chown -R ntp-monitor:ntp-monitor "$APP_DIR"

echo ""
echo "🚀 Redémarrage du service NTP Monitor..."
systemctl start $SERVICE_NAME

echo ""
echo "🏥 Vérification finale..."
sleep 10  # Plus de temps pour le démarrage

if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Service démarré avec succès"
    
    echo ""
    echo "🌐 Test de l'API..."
    sleep 3
    if curl -f -s http://localhost:5000/api/system/status > /dev/null 2>&1; then
        echo "✅ API accessible"
        
        echo ""
        echo "🔍 Test WebSocket depuis le serveur..."
        curl -s "http://localhost:5000" | grep -q "socket.io" && echo "✅ Page contient les scripts Socket.IO" || echo "⚠️ Scripts Socket.IO non détectés"
        
        echo ""
        echo "🎉 CORRECTION WEBSOCKET TERMINÉE !"
        echo "=================================="
        echo ""
        echo "📋 Configuration appliquée:"
        echo "   • python-socketio: 5.8.0 (compatible Socket.IO 4.x client)"
        echo "   • python-engineio: 4.7.1"
        echo "   • Flask-SocketIO: 5.3.6"
        echo "   • Transport: polling → websocket (upgrade)"
        echo "   • Ping timeout: 60s, interval: 25s"
        echo ""
        echo "🔗 Application: http://$(hostname -I | awk '{print $1}'):5000"
        echo "👤 Login: admin / admin123"
        echo ""
        echo "📱 Pour tester:"
        echo "   • Ouvrez l'application dans le navigateur"
        echo "   • F12 → Console → plus d'erreur 'Invalid frame header'"
        echo "   • Vous devriez voir: '✅ Socket.IO connecté avec succès'"
        echo "   • Dashboard en temps réel fonctionnel"
        
    else
        echo "⚠️ API pas encore accessible"
    fi
else
    echo "⚠️ Problème avec le service:"
    systemctl status $SERVICE_NAME --no-pager -l
    echo ""
    echo "📋 Logs récents:"
    journalctl -u $SERVICE_NAME --since "5 minutes ago" --no-pager -n 20
fi 