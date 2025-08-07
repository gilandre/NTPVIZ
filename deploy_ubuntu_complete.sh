#!/bin/bash
# deploy_ubuntu_complete.sh
# Déploiement complet depuis GitHub

set -e

echo "🚀 DÉPLOIEMENT COMPLET NTP MONITOR ENTERPRISE"
echo "================================================"

# Vérification des prérequis
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root"
    exit 1
fi

# Variables
REPO_URL="https://github.com/votre-username/NTPVIZ.git"
BRANCH="MacDev"
APP_DIR="/opt/ntp-monitor"
DB_NAME="ntp_monitor"
DB_USER="ntp_user"
DB_PASS="ntp_password_secure_2025"

echo "📋 Configuration :"
echo "  - Repository: $REPO_URL"
echo "  - Branche: $BRANCH"
echo "  - Répertoire: $APP_DIR"
echo "  - Base de données: $DB_NAME"

# Mise à jour du système
echo "🔄 Mise à jour du système..."
apt update && apt upgrade -y

# Installation des paquets requis
echo "📦 Installation des paquets requis..."
apt install -y python3 python3-pip python3-venv git mysql-server mysql-client nginx ufw

# Configuration MySQL
echo "🗄️ Configuration MySQL..."
systemctl start mysql
systemctl enable mysql

# Sécurisation MySQL
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root_password_secure_2025';"
mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';"
mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

# Clonage du repository
echo "📥 Clonage du repository GitHub..."
if [ -d "$APP_DIR" ]; then
    rm -rf "$APP_DIR"
fi

git clone -b $BRANCH $REPO_URL $APP_DIR
cd $APP_DIR

# Configuration de l'environnement Python
echo "🐍 Configuration de l'environnement Python..."
python3 -m venv .venv
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

# Configuration de l'environnement
echo "⚙️ Configuration de l'environnement..."
cp env.example .env
sed -i "s/DB_NAME=.*/DB_NAME=$DB_NAME/" .env
sed -i "s/DB_USER=.*/DB_USER=$DB_USER/" .env
sed -i "s/DB_PASS=.*/DB_PASS=$DB_PASS/" .env
sed -i "s/FLASK_ENV=.*/FLASK_ENV=production/" .env

# Correction du schéma de base de données
echo "🔧 Correction du schéma de base de données..."
python fix_database_schema.py

# Harmonisation des modèles
echo "🔄 Harmonisation des modèles..."
python harmonize_models.py

# Initialisation de la base de données
echo "🗄️ Initialisation de la base de données..."
python initialiser_database.py

# Test de l'application
echo "🧪 Test de l'application..."
python quick_verification.py

# Configuration du firewall
echo "🔥 Configuration du firewall..."
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5001/tcp
ufw --force enable

# Configuration Nginx
echo "🌐 Configuration Nginx..."
cat > /etc/nginx/sites-available/ntp-monitor << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/ntp-monitor /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx

# Configuration systemd
echo "⚙️ Configuration systemd..."
cat > /etc/systemd/system/ntp-monitor.service << EOF
[Unit]
Description=NTP Monitor Enterprise
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/.venv/bin
ExecStart=$APP_DIR/.venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Démarrage du service
echo "🚀 Démarrage du service..."
systemctl daemon-reload
systemctl enable ntp-monitor
systemctl start ntp-monitor

# Vérification finale
echo "✅ Vérification finale..."
sleep 5
systemctl status ntp-monitor --no-pager

echo "🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!"
echo "🌐 Application accessible sur: http://$(hostname -I | awk '{print $1}')"
echo "📊 Dashboard: http://$(hostname -I | awk '{print $1}')/dashboard" 