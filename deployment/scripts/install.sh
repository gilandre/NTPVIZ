#!/bin/bash
# Script d'installation NTP Monitor Enterprise sur serveur Ubuntu/Debian
# Optimisé pour le serveur 79.137.36.66

set -e  # Arrêter en cas d'erreur

echo "🚀 INSTALLATION NTP MONITOR ENTERPRISE"
echo "======================================"

# Configuration
APP_DIR="/opt/ntp-monitor"
APP_USER="ntp-monitor"
REPO_URL="https://github.com/YOUR_USERNAME/NTP_PROJECT.git"
SERVICE_NAME="ntp-monitor"

# Vérification des privilèges root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être exécuté en tant que root"
   exit 1
fi

echo "📦 Mise à jour du système..."
apt-get update -qq

echo "📦 Installation des dépendances système..."
apt-get install -y python3 python3-pip python3-venv git mysql-server mysql-client curl

echo "👤 Création de l'utilisateur système..."
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --shell /bin/bash --home "$APP_DIR" --create-home "$APP_USER"
    echo "✅ Utilisateur $APP_USER créé"
else
    echo "✅ Utilisateur $APP_USER existe déjà"
fi

echo "📁 Configuration des répertoires..."
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/logs"
mkdir -p "$APP_DIR/backup"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

echo "📥 Clonage du dépôt GitHub..."
if [ ! -d "$APP_DIR/.git" ]; then
    sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
else
    cd "$APP_DIR"
    sudo -u "$APP_USER" git fetch origin
    sudo -u "$APP_USER" git reset --hard origin/dev
fi

echo "🐍 Configuration de l'environnement Python..."
cd "$APP_DIR"
sudo -u "$APP_USER" python3 -m venv .venv
sudo -u "$APP_USER" .venv/bin/pip install --upgrade pip
sudo -u "$APP_USER" .venv/bin/pip install -r requirements.txt

echo "🗄️  Configuration de MySQL..."
if ! systemctl is-active --quiet mysql; then
    systemctl start mysql
    systemctl enable mysql
fi

# Configuration basique MySQL si nécessaire
mysql -u root -e "CREATE DATABASE IF NOT EXISTS ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || true
mysql -u root -e "CREATE USER IF NOT EXISTS 'ntp_monitor'@'localhost' IDENTIFIED BY 'ntp_password_2024';" 2>/dev/null || true
mysql -u root -e "GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_monitor'@'localhost';" 2>/dev/null || true
mysql -u root -e "FLUSH PRIVILEGES;" 2>/dev/null || true

echo "⚙️  Configuration de l'application..."
if [ ! -f "$APP_DIR/.env" ]; then
    cat > "$APP_DIR/.env" << EOF
# Configuration production NTP Monitor Enterprise
FLASK_ENV=production
DATABASE_URL=mysql://ntp_monitor:ntp_password_2024@localhost/ntp_monitor
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
HOST=0.0.0.0
PORT=5000
DEBUG=False
EOF
    chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
fi

echo "🗄️  Initialisation de la base de données..."
cd "$APP_DIR"
sudo -u "$APP_USER" .venv/bin/python -c "from backend.database_manager import db_manager; db_manager.initialize()"
sudo -u "$APP_USER" .venv/bin/python -c "from backend.utils.init_data import init_default_data; init_default_data()"

echo "🔧 Installation du service systemd..."
cp "$APP_DIR/deployment/systemd/ntp-monitor.service" "/etc/systemd/system/"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo "🔥 Configuration du pare-feu (si ufw est installé)..."
if command -v ufw &> /dev/null; then
    ufw allow 5000/tcp
    ufw allow 22/tcp
    ufw allow 123/udp  # Port NTP
fi

echo "🚀 Démarrage du service..."
systemctl start "$SERVICE_NAME"

echo "🏥 Vérification du service..."
sleep 3
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ Service démarré avec succès"
else
    echo "⚠️  Problème avec le service, affichage des logs:"
    systemctl status "$SERVICE_NAME" --no-pager -l
fi

echo ""
echo "🎉 INSTALLATION TERMINÉE !"
echo "========================="
echo ""
echo "🔗 Application accessible sur: http://$(hostname -I | awk '{print $1}'):5000"
echo "👤 Identifiants par défaut:"
echo "   • Admin: admin / admin123"
echo "   • Operator: operator / operator123"
echo "   • Viewer: viewer / viewer123"
echo ""
echo "📝 Commandes utiles:"
echo "   • Statut: systemctl status $SERVICE_NAME"
echo "   • Logs: journalctl -u $SERVICE_NAME -f"
echo "   • Redémarrage: systemctl restart $SERVICE_NAME"
echo "   • Arrêt: systemctl stop $SERVICE_NAME"
echo ""
echo "🔧 Fichiers importants:"
echo "   • Application: $APP_DIR"
echo "   • Configuration: $APP_DIR/.env"
echo "   • Logs: $APP_DIR/logs/"
echo "   • Service: /etc/systemd/system/$SERVICE_NAME.service" 