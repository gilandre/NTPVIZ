#!/bin/bash
# Script de réparation complète pour NTP Monitor Enterprise
# Usage: ./repair_installation.sh

set -e

echo "🔧 RÉPARATION COMPLÈTE NTP MONITOR ENTERPRISE"
echo "============================================="

APP_DIR="/opt/ntp-monitor"
APP_USER="ntp-monitor"
SERVICE_NAME="ntp-monitor"

# Vérification des privilèges root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être exécuté en tant que root"
   exit 1
fi

echo "🛑 Arrêt du service existant (si il existe)..."
systemctl stop $SERVICE_NAME 2>/dev/null || echo "Service non actif"
systemctl disable $SERVICE_NAME 2>/dev/null || echo "Service non trouvé"

echo ""
echo "📦 Installation/Mise à jour des dépendances système..."
apt-get update -qq
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    mysql-server \
    mysql-client \
    curl \
    pkg-config \
    libmysqlclient-dev \
    build-essential \
    default-libmysqlclient-dev

echo ""
echo "👤 Vérification de l'utilisateur système..."
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --shell /bin/bash --home "$APP_DIR" --create-home "$APP_USER"
    echo "✅ Utilisateur $APP_USER créé"
else
    echo "✅ Utilisateur $APP_USER existe déjà"
fi

echo ""
echo "📁 Configuration des répertoires..."
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/logs"
mkdir -p "$APP_DIR/backup"

echo ""
echo "🐍 Suppression et recréation de l'environnement virtuel..."
if [ -d "$APP_DIR/.venv" ]; then
    rm -rf "$APP_DIR/.venv"
    echo "✅ Ancien environnement virtuel supprimé"
fi

cd "$APP_DIR"

echo "🐍 Création du nouvel environnement virtuel..."
sudo -u "$APP_USER" python3 -m venv .venv

echo "🐍 Activation et mise à jour de l'environnement..."
sudo -u "$APP_USER" .venv/bin/python -m pip install --upgrade pip setuptools wheel

echo "🐍 Installation des dépendances de base..."
sudo -u "$APP_USER" .venv/bin/pip install \
    setuptools==68.0.0 \
    wheel==0.40.0 \
    Cython==0.29.36

echo "🐍 Installation de mysqlclient..."
sudo -u "$APP_USER" .venv/bin/pip install mysqlclient

echo "🐍 Installation des autres dépendances..."
if [ -f "requirements.txt" ]; then
    # Installation sans numpy d'abord pour éviter les conflits
    sudo -u "$APP_USER" .venv/bin/pip install \
        Flask==2.3.3 \
        Flask-SQLAlchemy==3.0.5 \
        Flask-Login==0.6.3 \
        Flask-WTF==1.1.1 \
        Flask-SocketIO==5.3.6 \
        python-socketio==5.8.0 \
        Werkzeug==2.3.7 \
        ntplib==0.4.0 \
        python-dateutil==2.8.2 \
        bcrypt==4.0.1 \
        requests==2.31.0 \
        PyMySQL==1.1.0
    
    echo "🐍 Installation de numpy (version compatible)..."
    sudo -u "$APP_USER" .venv/bin/pip install "numpy<1.25"
    
    echo "🐍 Installation des dépendances restantes..."
    sudo -u "$APP_USER" .venv/bin/pip install -r requirements.txt || echo "Certaines dépendances optionnelles ont échoué"
else
    echo "⚠️  requirements.txt non trouvé, installation manuelle..."
fi

echo ""
echo "🗄️  Configuration de MySQL..."
if ! systemctl is-active --quiet mysql; then
    systemctl start mysql
    systemctl enable mysql
fi

# Configuration basique MySQL
mysql -u root -e "CREATE DATABASE IF NOT EXISTS ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || true
mysql -u root -e "CREATE USER IF NOT EXISTS 'ntp_monitor'@'localhost' IDENTIFIED BY 'ntp_password_2024';" 2>/dev/null || true
mysql -u root -e "GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_monitor'@'localhost';" 2>/dev/null || true
mysql -u root -e "FLUSH PRIVILEGES;" 2>/dev/null || true

echo ""
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

echo ""
echo "🗄️  Initialisation de la base de données..."
sudo -u "$APP_USER" .venv/bin/python -c "
try:
    from backend.database_manager import db_manager
    db_manager.initialize()
    print('✅ Base de données initialisée')
except Exception as e:
    print(f'⚠️  Erreur DB: {e}')
" || echo "Base de données sera initialisée au démarrage"

sudo -u "$APP_USER" .venv/bin/python -c "
try:
    from backend.utils.init_data import init_default_data
    init_default_data()
    print('✅ Données par défaut initialisées')
except Exception as e:
    print(f'⚠️  Erreur données: {e}')
" || echo "Données par défaut seront initialisées au démarrage"

echo ""
echo "🔧 Installation du service systemd..."
if [ -f "$APP_DIR/deployment/systemd/ntp-monitor.service" ]; then
    cp "$APP_DIR/deployment/systemd/ntp-monitor.service" "/etc/systemd/system/"
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    echo "✅ Service systemd installé"
else
    echo "⚠️  Fichier service non trouvé, création manuelle..."
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=NTP Monitor Enterprise - Monitoring serveurs NTP
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=FLASK_APP=app.py
Environment=FLASK_ENV=production
ExecStart=$APP_DIR/.venv/bin/python app.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Sécurité
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$APP_DIR
ProtectHome=true

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    echo "✅ Service systemd créé et activé"
fi

echo ""
echo "🔧 Configuration des permissions..."
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chmod +x "$APP_DIR/app.py" 2>/dev/null || true

echo ""
echo "🚀 Démarrage du service..."
systemctl start "$SERVICE_NAME"

echo ""
echo "🏥 Vérification du service..."
sleep 5
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ Service démarré avec succès"
    
    echo ""
    echo "🌐 Test de connectivité..."
    sleep 3
    if curl -f -s http://localhost:5000/api/system/status > /dev/null 2>&1; then
        echo "✅ Application accessible"
    else
        echo "⚠️  Application pas encore accessible, vérifiez dans quelques instants"
    fi
else
    echo "⚠️  Problème avec le service, affichage des logs:"
    systemctl status "$SERVICE_NAME" --no-pager -l
    echo ""
    echo "📋 Logs détaillés:"
    journalctl -u "$SERVICE_NAME" --since "5 minutes ago" --no-pager
fi

echo ""
echo "🎉 RÉPARATION TERMINÉE !"
echo "======================"
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