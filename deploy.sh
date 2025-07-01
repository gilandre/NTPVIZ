#!/bin/bash
# Script de déploiement simple - NTP Monitor Enterprise
# Usage: ./deploy.sh [server_user@server_ip] [app_directory]

set -e  # Arrêter en cas d'erreur

# Configuration par défaut
DEFAULT_SERVER="root@79.137.36.66"
DEFAULT_APP_DIR="/opt/ntp-monitor"
DEFAULT_SERVICE_NAME="ntp-monitor"

# Paramètres
SERVER_HOST="${1:-$DEFAULT_SERVER}"
APP_DIR="${2:-$DEFAULT_APP_DIR}"
SERVICE_NAME="${3:-$DEFAULT_SERVICE_NAME}"

echo "🚀 DÉPLOIEMENT NTP MONITOR ENTERPRISE"
echo "======================================"
echo "• Serveur cible: $SERVER_HOST"
echo "• Répertoire app: $APP_DIR"
echo "• Service: $SERVICE_NAME"
echo ""

# Fonction pour exécuter des commandes sur le serveur distant
remote_exec() {
    echo "📡 Exécution sur serveur: $1"
    ssh "$SERVER_HOST" "$1"
}

# Fonction pour copier des fichiers vers le serveur
remote_copy() {
    echo "📁 Copie: $1 -> $SERVER_HOST:$2"
    scp -r "$1" "$SERVER_HOST:$2"
}

echo "🔍 Vérification de la connectivité serveur..."
if ! ssh -o ConnectTimeout=10 "$SERVER_HOST" "echo 'Connexion OK'"; then
    echo "❌ Impossible de se connecter au serveur $SERVER_HOST"
    echo "💡 Vérifiez:"
    echo "   - La connectivité réseau"
    echo "   - Les clés SSH"
    echo "   - L'utilisateur et l'adresse"
    exit 1
fi

echo "✅ Connexion serveur établie"

echo ""
echo "🛑 Arrêt du service en cours..."
remote_exec "systemctl stop $SERVICE_NAME 2>/dev/null || echo 'Service non actif'"

echo ""
echo "💾 Sauvegarde de la configuration actuelle..."
remote_exec "mkdir -p $APP_DIR/backup/$(date +%Y%m%d_%H%M%S)"
remote_exec "if [ -f $APP_DIR/config/config.py ]; then cp $APP_DIR/config/config.py $APP_DIR/backup/$(date +%Y%m%d_%H%M%S)/; fi"
remote_exec "if [ -f $APP_DIR/.env ]; then cp $APP_DIR/.env $APP_DIR/backup/$(date +%Y%m%d_%H%M%S)/; fi"

echo ""
echo "📥 Téléchargement des mises à jour depuis GitHub..."
remote_exec "cd $APP_DIR && git fetch origin"
remote_exec "cd $APP_DIR && git reset --hard origin/dev"

echo ""
echo "🔧 Vérification des dépendances système..."
remote_exec "apt-get update -qq && apt-get install -y pkg-config libmysqlclient-dev default-libmysqlclient-dev python3-dev build-essential 2>/dev/null || echo 'Dépendances déjà installées'"

echo ""
echo "🐍 Mise à jour de l'environnement Python..."
remote_exec "cd $APP_DIR && .venv/bin/python -m pip install --upgrade pip"
remote_exec "cd $APP_DIR && .venv/bin/pip install -r requirements.txt"

echo ""
echo "🗄️  Vérification et mise à jour de la base de données..."
remote_exec "cd $APP_DIR && python3 -c 'from backend.database_manager import db_manager; db_manager.initialize()' || echo 'DB déjà initialisée'"
remote_exec "cd $APP_DIR && python3 -c 'from backend.utils.init_data import init_default_data; init_default_data()'"

echo ""
echo "🔧 Configuration des permissions..."
remote_exec "chown -R $USER:$USER $APP_DIR"
remote_exec "chmod +x $APP_DIR/app.py"
remote_exec "chmod +x $APP_DIR/deploy.sh"

echo ""
echo "🚀 Redémarrage du service..."
remote_exec "systemctl start $SERVICE_NAME"
remote_exec "systemctl enable $SERVICE_NAME"

echo ""
echo "🏥 Vérification de l'état du service..."
sleep 3
if remote_exec "systemctl is-active --quiet $SERVICE_NAME"; then
    echo "✅ Service démarré avec succès"
else
    echo "⚠️  Service non actif, vérification des logs..."
    remote_exec "systemctl status $SERVICE_NAME --no-pager -l"
fi

echo ""
echo "🌐 Test de connectivité application..."
if remote_exec "curl -f -s http://localhost:5000/api/system/status > /dev/null"; then
    echo "✅ Application accessible"
else
    echo "⚠️  Application non accessible, vérifiez les logs"
fi

echo ""
echo "📊 Statut final du déploiement:"
echo "=============================="
remote_exec "systemctl status $SERVICE_NAME --no-pager -l | head -10"

echo ""
echo "🎉 DÉPLOIEMENT TERMINÉ !"
echo ""
echo "🔗 Accès application: http://$SERVER_HOST:5000"
echo "👤 Identifiants par défaut:"
echo "   • Admin: admin / admin123"
echo "   • Operator: operator / operator123"
echo "   • Viewer: viewer / viewer123"
echo ""
echo "📝 Commandes utiles:"
echo "   • Logs: ssh $SERVER_HOST 'journalctl -u $SERVICE_NAME -f'"
echo "   • Statut: ssh $SERVER_HOST 'systemctl status $SERVICE_NAME'"
echo "   • Redémarrage: ssh $SERVER_HOST 'systemctl restart $SERVICE_NAME'" 