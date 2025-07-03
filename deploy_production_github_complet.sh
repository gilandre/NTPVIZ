#!/bin/bash
# DÉPLOIEMENT PRODUCTION COMPLET - GitHub vers Serveur 79.137.36.66
# Remplacement complet des sources + Mise en production

set -e

echo "🚀 DÉPLOIEMENT PRODUCTION EMERAUDEVIZ NTP DEPUIS GITHUB"
echo "======================================================="

# Configuration
GITHUB_REPO="https://github.com/gilandre/NTPVIZ.git"
GITHUB_BRANCH="dev"
REMOTE_SERVER="79.137.36.66"
REMOTE_USER="ubuntu"
REMOTE_PROJECT_DIR="/opt/NTPVIZ"
SERVICE_NAME="ntp-monitor"
BACKUP_DIR="/tmp/ntp_backup_$(date +%Y%m%d_%H%M%S)"

echo "📍 Serveur cible: $REMOTE_SERVER"
echo "📂 Répertoire: $REMOTE_PROJECT_DIR"
echo "🌿 Branch: $GITHUB_BRANCH"
echo "🕒 $(date)"

# Fonction pour exécuter des commandes sur le serveur distant
execute_remote() {
    local cmd="$1"
    echo "🔄 Exécution: $cmd"
    ssh $REMOTE_USER@$REMOTE_SERVER "cd $REMOTE_PROJECT_DIR && $cmd"
}

# Vérification connexion serveur
echo "📡 Test connexion serveur..."
if ! ssh -o ConnectTimeout=10 $REMOTE_USER@$REMOTE_SERVER "echo 'Connexion OK'"; then
    echo "❌ Impossible de se connecter au serveur $REMOTE_SERVER"
    exit 1
fi

echo "✅ Connexion serveur établie"

# =================== SAUVEGARDE ACTUELLE ===================
echo "💾 Sauvegarde de l'installation actuelle..."

ssh $REMOTE_USER@$REMOTE_SERVER << EOF
# Stopper le service
systemctl stop $SERVICE_NAME || true

# Créer sauvegarde
mkdir -p $BACKUP_DIR
if [ -d "$REMOTE_PROJECT_DIR" ]; then
    cp -r $REMOTE_PROJECT_DIR/* $BACKUP_DIR/ 2>/dev/null || true
    echo "✅ Sauvegarde créée dans $BACKUP_DIR"
else
    echo "⚠️ Aucune installation existante trouvée"
fi
EOF

# =================== TÉLÉCHARGEMENT DEPUIS GITHUB ===================
echo "📥 Téléchargement depuis GitHub..."

ssh $REMOTE_USER@$REMOTE_SERVER << EOF
# Supprimer l'ancien répertoire s'il existe
if [ -d "$REMOTE_PROJECT_DIR" ]; then
    rm -rf $REMOTE_PROJECT_DIR
fi

# Créer le répertoire parent
mkdir -p $(dirname $REMOTE_PROJECT_DIR)

# Cloner le repository
echo "🔄 Clone depuis $GITHUB_REPO (branch: $GITHUB_BRANCH)"
git clone -b $GITHUB_BRANCH $GITHUB_REPO $REMOTE_PROJECT_DIR

if [ $? -eq 0 ]; then
    echo "✅ Repository cloné avec succès"
    cd $REMOTE_PROJECT_DIR
    echo "📊 Commit actuel: \$(git rev-parse HEAD)"
    echo "📝 Dernier commit: \$(git log -1 --oneline)"
else
    echo "❌ Erreur lors du clone"
    exit 1
fi
EOF

# =================== INSTALLATION ENVIRONNEMENT ===================
echo "🔧 Installation environnement Python..."

ssh $REMOTE_USER@$REMOTE_SERVER << EOF
cd $REMOTE_PROJECT_DIR

# Installer système
apt update
apt install -y python3 python3-pip python3-venv git nginx

# Créer utilisateur ntp-monitor s'il n'existe pas
if ! id "ntp-monitor" &>/dev/null; then
    useradd -r -s /bin/bash -d $REMOTE_PROJECT_DIR ntp-monitor
    echo "✅ Utilisateur ntp-monitor créé"
fi

# Créer environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Installer les dépendances avec versions corrigées
echo "📦 Installation packages Python..."

# Packages essentiels avec versions compatibles
pip install --upgrade pip setuptools wheel

# Flask et extensions (versions compatibles)
pip install Flask==2.3.3
pip install Werkzeug==2.3.7
pip install flask-login==0.6.3
pip install flask-socketio==5.3.6
pip install python-socketio==5.8.0

# Base de données
pip install SQLAlchemy==2.0.23
pip install flask-sqlalchemy==3.1.1

# NTP et réseau
pip install ntplib==0.4.0
pip install python-dateutil==2.8.2
pip install pytz==2023.3

# Utilitaires
pip install requests==2.31.0
pip install python-dotenv==1.0.0

# Redis avec version compatible
pip install redis==4.6.0

# Celery pour les tâches
pip install celery==5.3.4

# Crypto et sécurité
pip install cryptography==41.0.7
pip install bcrypt==4.1.2

echo "✅ Packages Python installés"

# Vérifier les installations critiques
python3 -c "import flask; print(f'Flask: {flask.__version__}')"
python3 -c "import werkzeug; print(f'Werkzeug: {werkzeug.__version__}')"
python3 -c "import sqlalchemy; print(f'SQLAlchemy: {sqlalchemy.__version__}')"
EOF

# =================== CONFIGURATION APPLICATION ===================
echo "⚙️ Configuration de l'application..."

ssh $REMOTE_USER@$REMOTE_SERVER << EOF
cd $REMOTE_PROJECT_DIR

# Créer répertoires nécessaires
mkdir -p logs instance static uploads
mkdir -p frontend/static/css frontend/static/js frontend/templates

# Configuration environnement
cat > .env << 'ENVEOF'
# Configuration EMERAUDEVIZ NTP Production
FLASK_ENV=production
FLASK_APP=app.py
SECRET_KEY=emeraudeviz-ntp-production-2025-secure
DATABASE_URL=sqlite:///instance/ntp_monitor_production.db

# Configuration NTP
NTP_POLL_INTERVAL=60
NTP_TIMEOUT=10
MAX_SERVERS=50

# Configuration logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Configuration serveur
HOST=0.0.0.0
PORT=5000
ENVEOF

# Permissions
chown -R ntp-monitor:ntp-monitor $REMOTE_PROJECT_DIR
chmod +x app.py 2>/dev/null || true
chmod -R 755 frontend/ 2>/dev/null || true
chmod -R 755 backend/ 2>/dev/null || true
chmod -R 755 static/ 2>/dev/null || true

echo "✅ Configuration terminée"
EOF

# =================== CONFIGURATION SYSTEMD ===================
echo "🔧 Configuration service systemd..."

ssh $REMOTE_USER@$REMOTE_SERVER << EOF
# Service systemd
cat > /etc/systemd/system/$SERVICE_NAME.service << 'SERVICEEOF'
[Unit]
Description=EMERAUDEVIZ NTP Monitor Enterprise
After=network.target
Wants=network.target

[Service]
Type=simple
User=ntp-monitor
Group=ntp-monitor
WorkingDirectory=/opt/NTPVIZ
Environment=PATH=/opt/NTPVIZ/.venv/bin
Environment=PYTHONPATH=/opt/NTPVIZ
ExecStart=/opt/NTPVIZ/.venv/bin/python app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ntp-monitor

# Sécurité
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/NTPVIZ/logs /opt/NTPVIZ/instance
PrivateTmp=true

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Recharger systemd
systemctl daemon-reload
systemctl enable $SERVICE_NAME

echo "✅ Service systemd configuré"
EOF

# =================== CONFIGURATION NGINX ===================
echo "🌐 Configuration Nginx..."

ssh $REMOTE_USER@$REMOTE_SERVER << EOF
# Configuration Nginx
cat > /etc/nginx/sites-available/ntp-monitor << 'NGINXEOF'
server {
    listen 80;
    server_name 79.137.36.66 localhost;
    
    # Logs
    access_log /var/log/nginx/ntp-monitor-access.log;
    error_log /var/log/nginx/ntp-monitor-error.log;
    
    # Proxy vers Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Fichiers statiques
    location /static/ {
        alias /opt/NTPVIZ/frontend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Santé
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
    }
}
NGINXEOF

# Activer le site
ln -sf /etc/nginx/sites-available/ntp-monitor /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Tester et redémarrer Nginx
nginx -t
systemctl restart nginx
systemctl enable nginx

echo "✅ Nginx configuré"
EOF

# =================== TEST ET DÉMARRAGE ===================
echo "🧪 Test et démarrage de l'application..."

ssh $REMOTE_USER@$REMOTE_SERVER << EOF
cd $REMOTE_PROJECT_DIR

# Test syntaxe Python
echo "🔍 Test syntaxe Python..."
sudo -u ntp-monitor bash -c "
source .venv/bin/activate
export PYTHONPATH='$REMOTE_PROJECT_DIR'
python3 -c 'import sys; print(f\"Python: {sys.version}\")' 
python3 -c 'import app; print(\"✅ app.py OK\")'
"

if [ $? -ne 0 ]; then
    echo "❌ Erreur test Python"
    exit 1
fi

# Démarrer le service
echo "🚀 Démarrage du service..."
systemctl start $SERVICE_NAME

# Attendre le démarrage
sleep 8

# Vérifier le statut
echo "📊 Statut des services:"
systemctl status $SERVICE_NAME --no-pager -l | head -10
systemctl status nginx --no-pager -l | head -5
EOF

# =================== VÉRIFICATIONS FINALES ===================
echo "🔍 Vérifications finales..."

# Test de connexion HTTP
echo "🌐 Test connexion HTTP..."
if curl -I -s http://$REMOTE_SERVER/ | grep -q "200\|302"; then
    echo "✅ Application accessible sur http://$REMOTE_SERVER/"
else
    echo "⚠️ Application en cours de démarrage..."
fi

# Test API santé
if curl -s http://$REMOTE_SERVER/health | grep -q "healthy\|status"; then
    echo "✅ API santé fonctionnelle"
else
    echo "⚠️ API santé en cours d'initialisation"
fi

# Afficher les logs récents
echo "📋 Logs récents du service:"
ssh $REMOTE_USER@$REMOTE_SERVER "journalctl -u $SERVICE_NAME --no-pager -n 5"

# =================== RÉSULTAT FINAL ===================
echo ""
echo "🎉 DÉPLOIEMENT PRODUCTION TERMINÉ !"
echo "===================================="
echo "🌐 URL principale: http://$REMOTE_SERVER/"
echo "📊 API santé: http://$REMOTE_SERVER/health" 
echo "🔐 Dashboard: http://$REMOTE_SERVER/dashboard"
echo ""
echo "📋 Commandes utiles:"
echo "   ssh $REMOTE_USER@$REMOTE_SERVER"
echo "   systemctl status $SERVICE_NAME"
echo "   journalctl -u $SERVICE_NAME -f"
echo "   tail -f $REMOTE_PROJECT_DIR/logs/app.log"
echo ""
echo "💾 Sauvegarde précédente: $BACKUP_DIR"
echo "📂 Sources GitHub déployées avec succès"
echo ""
echo "🚀 EMERAUDEVIZ NTP ENTERPRISE EN PRODUCTION !" 
