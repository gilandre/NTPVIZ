#!/bin/bash
# Script de déploiement complet NTP Monitor Enterprise
# Met à jour depuis GitHub et configure tout automatiquement
# Usage: curl -sSL https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deploy_complete_update.sh | sudo bash

set -e

echo "======================================================"
echo "     DEPLOIEMENT COMPLET NTP MONITOR ENTERPRISE      "
echo "======================================================"
echo "Mise à jour depuis GitHub avec toutes les corrections"
echo ""

# Vérification privilèges root
if [[ $EUID -ne 0 ]]; then
   echo "❌ ERREUR: Ce script doit être exécuté en tant que root"
   exit 1
fi

# Variables
GITHUB_REPO="https://github.com/gilandre/NTPVIZ.git"
BRANCH="dev"
OLD_APP_DIR="/var/www/ntp-monitor-enterprise"
NEW_APP_DIR="/opt/ntp-monitor"
SERVICE_NAME="ntp-monitor"
BACKUP_DIR="/opt/backup_ntp_$(date +%Y%m%d_%H%M%S)"

echo "🔍 DIAGNOSTIC INITIAL"
echo "===================="

# Vérifier l'état actuel
echo "• Vérification des services existants..."
if systemctl list-units --type=service | grep -q "apache2"; then
    echo "  ✓ Apache2 détecté"
    APACHE_RUNNING=true
else
    APACHE_RUNNING=false
fi

if systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
    echo "  ✓ Service $SERVICE_NAME existe"
    SERVICE_EXISTS=true
else
    echo "  ✗ Service $SERVICE_NAME n'existe pas"
    SERVICE_EXISTS=false
fi

# Vérifier les répertoires existants
if [ -d "$OLD_APP_DIR" ]; then
    echo "  ✓ Ancien répertoire trouvé: $OLD_APP_DIR"
    OLD_DIR_EXISTS=true
else
    OLD_DIR_EXISTS=false
fi

if [ -d "$NEW_APP_DIR" ]; then
    echo "  ✓ Nouveau répertoire trouvé: $NEW_APP_DIR"
    NEW_DIR_EXISTS=true
else
    echo "  ✗ Nouveau répertoire absent: $NEW_APP_DIR"
    NEW_DIR_EXISTS=false
fi

echo ""
echo "📦 SAUVEGARDE ET ARRET DES SERVICES"
echo "=================================="

# Arrêter Apache si nécessaire
if [ "$APACHE_RUNNING" = true ]; then
    echo "• Arrêt d'Apache2..."
    systemctl stop apache2 || true
fi

# Arrêter le service NTP Monitor s'il existe
if [ "$SERVICE_EXISTS" = true ]; then
    echo "• Arrêt du service $SERVICE_NAME..."
    systemctl stop $SERVICE_NAME || true
    systemctl disable $SERVICE_NAME || true
fi

# Sauvegarde des anciennes installations
echo "• Création de la sauvegarde dans $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"

if [ "$OLD_DIR_EXISTS" = true ]; then
    echo "  - Sauvegarde de $OLD_APP_DIR..."
    cp -r "$OLD_APP_DIR" "$BACKUP_DIR/old_app/" || true
fi

if [ "$NEW_DIR_EXISTS" = true ]; then
    echo "  - Sauvegarde de $NEW_APP_DIR..."
    cp -r "$NEW_APP_DIR" "$BACKUP_DIR/new_app/" || true
fi

echo ""
echo "📥 TELECHARGER LA DERNIERE VERSION"
echo "================================="

# Supprimer les anciens répertoires
if [ "$OLD_DIR_EXISTS" = true ]; then
    echo "• Suppression de l'ancien répertoire..."
    rm -rf "$OLD_APP_DIR"
fi

if [ "$NEW_DIR_EXISTS" = true ]; then
    echo "• Suppression du nouveau répertoire existant..."
    rm -rf "$NEW_APP_DIR"
fi

# Installer git si nécessaire
if ! command -v git &> /dev/null; then
    echo "• Installation de Git..."
    apt update
    apt install -y git
fi

# Cloner le repository
echo "• Clonage du repository depuis GitHub..."
git clone -b "$BRANCH" "$GITHUB_REPO" "$NEW_APP_DIR"
cd "$NEW_APP_DIR"

echo "✅ Version téléchargée: $(git log -1 --format='%h - %s')"

echo ""
echo "🔧 INSTALLATION DES DEPENDANCES"
echo "==============================="

# Installer les dépendances système
echo "• Installation des dépendances système..."
apt update
apt install -y python3 python3-pip python3-venv python3-dev build-essential \
    pkg-config libmysqlclient-dev default-libmysqlclient-dev \
    mysql-server curl wget htop nano \
    apache2-dev libapr1-dev libaprutil1-dev libpcre3-dev

# Créer l'environnement virtuel
echo "• Création de l'environnement virtuel..."
python3 -m venv .venv
source .venv/bin/activate

# Mettre à jour pip
echo "• Mise à jour de pip..."
pip install --upgrade pip setuptools wheel

# Installer les dépendances Python
echo "• Installation des dépendances Python..."
if ! pip install -r requirements.txt; then
    echo "⚠️ Erreur installation globale, tentative package par package..."
    
    # Lire le fichier requirements.txt et installer package par package
    while IFS= read -r package || [ -n "$package" ]; do
        # Ignorer les lignes vides et commentaires
        if [[ -n "$package" && ! "$package" =~ ^[[:space:]]*# ]]; then
            echo "  • Installation de $package..."
            if ! pip install "$package"; then
                echo "    ⚠️ Erreur avec $package, on continue..."
                # Packages problématiques connus
                if [[ "$package" == *"mod-wsgi"* ]]; then
                    echo "    ℹ️ mod-wsgi ignoré (Apache proxy utilisé à la place)"
                elif [[ "$package" == *"mysqlclient"* ]]; then
                    echo "    ℹ️ Tentative PyMySQL à la place..."
                    pip install PyMySQL || echo "    ⚠️ PyMySQL échoué aussi"
                fi
            fi
        fi
    done < requirements.txt
    
    echo "• Installation des packages essentiels..."
    # S'assurer que les packages critiques sont installés
    pip install flask flask-sqlalchemy flask-login flask-socketio python-socketio pymysql || true
fi

echo ""
echo "🔍 VERIFICATION PACKAGES CRITIQUES"
echo "=================================="

echo "• Vérification des packages Python essentiels..."
MISSING_PACKAGES=()

# Vérifier les packages critiques (format: package_pip:module_import)
CRITICAL_PACKAGES=(
    "flask:flask"
    "flask-sqlalchemy:flask_sqlalchemy" 
    "flask-login:flask_login"
    "flask-socketio:flask_socketio"
    "sqlalchemy:sqlalchemy"
    "pymysql:pymysql"
)

for pkg_info in "${CRITICAL_PACKAGES[@]}"; do
    pip_name="${pkg_info%:*}"
    import_name="${pkg_info#*:}"
    
    if ! sudo -u ntp-monitor "$NEW_APP_DIR/.venv/bin/python" -c "import $import_name" 2>/dev/null; then
        echo "  ⚠️ Package manquant: $pip_name"
        MISSING_PACKAGES+=("$pip_name")
    else
        echo "  ✓ $pip_name disponible"
    fi
done

# Installer les packages manquants
if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "• Installation des packages manquants..."
    for package in "${MISSING_PACKAGES[@]}"; do
        echo "  • Installation de $package..."
        sudo -u ntp-monitor "$NEW_APP_DIR/.venv/bin/pip" install "$package" || echo "    ⚠️ Erreur avec $package"
    done
fi

echo ""
echo "👤 CONFIGURATION UTILISATEUR"
echo "============================"

# Créer l'utilisateur ntp-monitor
if ! id "ntp-monitor" &>/dev/null; then
    echo "• Création de l'utilisateur ntp-monitor..."
    useradd --system --shell /bin/bash --home "$NEW_APP_DIR" ntp-monitor
else
    echo "• Utilisateur ntp-monitor existe déjà"
fi

# Configurer les permissions
echo "• Configuration des permissions..."
chown -R ntp-monitor:ntp-monitor "$NEW_APP_DIR"
chmod +x "$NEW_APP_DIR/app.py"

echo ""
echo "🗄️ CONFIGURATION BASE DE DONNEES"
echo "==============================="

# Démarrer MySQL
echo "• Démarrage de MySQL..."
systemctl start mysql
systemctl enable mysql

# Détecter le driver MySQL disponible
echo "• Détection du driver MySQL..."
DRIVER_TYPE="pymysql"

# S'assurer qu'au moins PyMySQL est installé
sudo -u ntp-monitor "$NEW_APP_DIR/.venv/bin/pip" install PyMySQL 2>/dev/null || true

if sudo -u ntp-monitor "$NEW_APP_DIR/.venv/bin/python" -c "import MySQLdb" 2>/dev/null; then
    DRIVER_TYPE="mysqlclient"
    echo "  ✓ Driver MySQLdb disponible"
elif sudo -u ntp-monitor "$NEW_APP_DIR/.venv/bin/python" -c "import pymysql" 2>/dev/null; then
    DRIVER_TYPE="pymysql"
    echo "  ✓ Driver PyMySQL disponible"
    # Configurer PyMySQL comme MySQLdb
    sudo -u ntp-monitor "$NEW_APP_DIR/.venv/bin/python" -c "import pymysql; pymysql.install_as_MySQLdb()" 2>/dev/null || true
else
    echo "  ⚠️ Aucun driver MySQL trouvé, installation PyMySQL..."
    sudo -u ntp-monitor "$NEW_APP_DIR/.venv/bin/pip" install PyMySQL
    DRIVER_TYPE="pymysql"
fi

# Configurer la base de données
echo "• Configuration de la base de données MySQL..."
mysql -u root -e "CREATE DATABASE IF NOT EXISTS ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || true
mysql -u root -e "CREATE USER IF NOT EXISTS 'ntp_monitor'@'localhost' IDENTIFIED BY 'ntp_password_2024';" 2>/dev/null || true
mysql -u root -e "GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_monitor'@'localhost';" 2>/dev/null || true
mysql -u root -e "FLUSH PRIVILEGES;" 2>/dev/null || true

# Créer le fichier .env
echo "• Création du fichier .env..."
if [ "$DRIVER_TYPE" = "pymysql" ]; then
    DB_URL="mysql+pymysql://ntp_monitor:ntp_password_2024@localhost/ntp_monitor"
else
    DB_URL="mysql://ntp_monitor:ntp_password_2024@localhost/ntp_monitor"
fi

cat > "$NEW_APP_DIR/.env" << EOF
# Configuration production NTP Monitor Enterprise
FLASK_ENV=production
DATABASE_URL=$DB_URL
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
HOST=0.0.0.0
PORT=5000
DEBUG=False
LOGGING_LEVEL=INFO
EOF

chown ntp-monitor:ntp-monitor "$NEW_APP_DIR/.env"
chmod 600 "$NEW_APP_DIR/.env"

echo ""
echo "🔧 CORRECTION SQLALCHEMY 2.X"
echo "============================"

# Corriger la syntaxe SQLAlchemy dans les fichiers
echo "• Application des corrections SQLAlchemy 2.x..."

# Correction dans backend/api/main.py
if [ -f "$NEW_APP_DIR/backend/api/main.py" ]; then
    sed -i "s/db\.session\.execute('SELECT 1')/from sqlalchemy import text; db.session.execute(text('SELECT 1'))/g" "$NEW_APP_DIR/backend/api/main.py"
    echo "  ✓ backend/api/main.py corrigé"
fi

# Correction dans d'autres fichiers si nécessaire
find "$NEW_APP_DIR" -name "*.py" -type f -exec grep -l "db\.engine\.execute" {} \; | while read file; do
    echo "  • Correction de $file..."
    sed -i 's/db\.engine\.execute(\([^)]*\))/with db.engine.connect() as connection: connection.execute(text(\1))/g' "$file"
done

echo ""
echo "⚙️ CREATION SERVICE SYSTEMD"
echo "==========================="

# Créer le service systemd
echo "• Création du service systemd..."
cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=NTP Monitor Enterprise - Surveillance des serveurs NTP
Documentation=https://github.com/gilandre/NTPVIZ
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=simple
User=ntp-monitor
Group=ntp-monitor
WorkingDirectory=$NEW_APP_DIR
Environment=FLASK_APP=app.py
Environment=FLASK_ENV=production
Environment=PYTHONPATH=$NEW_APP_DIR
ExecStartPre=/bin/sleep 5
ExecStart=$NEW_APP_DIR/.venv/bin/python app.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Sécurité
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$NEW_APP_DIR
ProtectHome=true
RemainAfterExit=no

# Limites de ressources
LimitNOFILE=65536
MemoryLimit=512M

[Install]
WantedBy=multi-user.target
EOF

# Activer et démarrer le service
systemctl daemon-reload
systemctl enable $SERVICE_NAME

echo ""
echo "🌐 CONFIGURATION APACHE PROXY"
echo "============================="

# Installer Apache si pas présent
if ! command -v apache2 &> /dev/null; then
    echo "• Installation d'Apache2..."
    apt install -y apache2
fi

# Activer les modules nécessaires
echo "• Activation des modules Apache..."
a2enmod proxy
a2enmod proxy_http
a2enmod rewrite

# Créer la configuration Apache
echo "• Configuration d'Apache pour rediriger vers l'application..."
cat > /etc/apache2/sites-available/ntp-monitor.conf << EOF
<VirtualHost *:80>
    ServerName $(hostname -I | awk '{print $1}')
    
    # Redirection vers l'application Flask
    ProxyPreserveHost On
    ProxyRequests Off
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/
    
    # Headers pour WebSocket
    ProxyPass /socket.io/ http://127.0.0.1:5000/socket.io/
    ProxyPassReverse /socket.io/ http://127.0.0.1:5000/socket.io/
    
    # Logs
    ErrorLog \${APACHE_LOG_DIR}/ntp-monitor_error.log
    CustomLog \${APACHE_LOG_DIR}/ntp-monitor_access.log combined
</VirtualHost>
EOF

# Désactiver le site par défaut et activer le nôtre
a2dissite 000-default
a2ensite ntp-monitor

echo ""
echo "🗄️ INITIALISATION BASE DE DONNEES"
echo "================================"

echo "• Initialisation de la base de données..."
sudo -u ntp-monitor "$NEW_APP_DIR/.venv/bin/python" -c "
import sys
sys.path.insert(0, '$NEW_APP_DIR')
import os
os.chdir('$NEW_APP_DIR')

try:
    from app import app
    from backend.database import init_db
    
    with app.app_context():
        init_db()
        print('✅ Base de données initialisée avec succès')
        
except Exception as e:
    print(f'⚠️ Erreur initialisation DB: {e}')
    # Essayer avec init_data
    try:
        from backend.utils.init_data import init_database
        init_database()
        print('✅ Base de données initialisée avec init_data')
    except Exception as e2:
        print(f'⚠️ Erreur init_data: {e2}')
        print('ℹ️ La base sera initialisée au premier démarrage')
"

echo ""
echo "🚀 DEMARRAGE DES SERVICES"
echo "========================"

# Démarrer le service NTP Monitor
echo "• Démarrage du service NTP Monitor..."
systemctl start $SERVICE_NAME

# Attendre que le service démarre
echo "• Attente du démarrage complet..."
sleep 15

# Vérifier le statut du service
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Service NTP Monitor démarré avec succès"
else
    echo "❌ Problème avec le service NTP Monitor"
    echo "📋 Logs du service:"
    journalctl -u $SERVICE_NAME --since "2 minutes ago" --no-pager -n 10
fi

# Démarrer Apache
echo "• Démarrage d'Apache..."
systemctl start apache2
systemctl enable apache2

echo ""
echo "🧪 TESTS DE VERIFICATION"
echo "======================="

# Test de l'API
echo "• Test de l'API sur le port 5000..."
sleep 5
if curl -f -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ API accessible sur le port 5000"
    API_OK=true
else
    echo "❌ API non accessible sur le port 5000"
    API_OK=false
fi

# Test du proxy Apache
echo "• Test du proxy Apache sur le port 80..."
if curl -f -s http://localhost/ > /dev/null 2>&1; then
    echo "✅ Proxy Apache fonctionnel"
    PROXY_OK=true
else
    echo "❌ Proxy Apache non fonctionnel"
    PROXY_OK=false
fi

# Test de la base de données
echo "• Test de la base de données..."
if sudo -u ntp-monitor "$NEW_APP_DIR/.venv/bin/python" -c "
import sys
sys.path.insert(0, '$NEW_APP_DIR')
from sqlalchemy import create_engine, text
engine = create_engine('$DB_URL')
with engine.connect() as conn:
    conn.execute(text('SELECT 1'))
print('✅ Base de données accessible')
" 2>/dev/null; then
    DB_OK=true
else
    echo "❌ Problème avec la base de données"
    DB_OK=false
fi

echo ""
echo "======================================================"
echo "           DEPLOIEMENT TERMINE                        "
echo "======================================================"

SERVER_IP=$(hostname -I | awk '{print $1}')

if [ "$API_OK" = true ] && [ "$PROXY_OK" = true ]; then
    echo ""
    echo "🎉 SUCCES ! Application déployée avec succès !"
    echo ""
    echo "🔗 ACCES A L'APPLICATION:"
    echo "   • URL principale: http://$SERVER_IP/"
    echo "   • URL directe:    http://$SERVER_IP:5000/"
    echo ""
    echo "👤 COMPTES DE CONNEXION:"
    echo "   • Admin:    admin / admin123"
    echo "   • Operator: operator / operator123"
    echo "   • Viewer:   viewer / viewer123"
    echo ""
    echo "📋 GESTION DU SERVICE:"
    echo "   • Statut:     systemctl status $SERVICE_NAME"
    echo "   • Redémarrer: systemctl restart $SERVICE_NAME"
    echo "   • Logs:       journalctl -u $SERVICE_NAME -f"
    echo ""
    echo "🗂️ REPERTOIRES:"
    echo "   • Application: $NEW_APP_DIR"
    echo "   • Sauvegarde:  $BACKUP_DIR"
    echo ""
    echo "✅ Version déployée: $(cd $NEW_APP_DIR && git log -1 --format='%h - %s')"
    
else
    echo ""
    echo "⚠️ DEPLOIEMENT PARTIEL"
    echo ""
    echo "📋 STATUT:"
    echo "   • API (port 5000):  $([ "$API_OK" = true ] && echo "✅ OK" || echo "❌ KO")"
    echo "   • Proxy (port 80):  $([ "$PROXY_OK" = true ] && echo "✅ OK" || echo "❌ KO")"
    echo "   • Base de données:  $([ "$DB_OK" = true ] && echo "✅ OK" || echo "❌ KO")"
    echo ""
    echo "🔍 DIAGNOSTIC:"
    echo "   • Logs service: journalctl -u $SERVICE_NAME -f"
    echo "   • Logs Apache:  tail -f /var/log/apache2/ntp-monitor_error.log"
    echo "   • Test manuel:  curl -v http://localhost:5000/health"
fi

echo ""
echo "📝 RESUME TECHNIQUE:"
echo "   • Ancienne version sauvegardée dans: $BACKUP_DIR"
echo "   • Nouvelle version depuis GitHub branche: $BRANCH"
echo "   • Driver base de données: $DRIVER_TYPE"
echo "   • Service systemd: $SERVICE_NAME"
echo "   • Configuration Apache: /etc/apache2/sites-available/ntp-monitor.conf"
echo ""
echo "🔄 Pour mettre à jour à nouveau:"
echo "   curl -sSL https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deploy_complete_update.sh | sudo bash"
echo ""
echo "======================================================" 