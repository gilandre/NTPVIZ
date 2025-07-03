#!/bin/bash
# DÉPLOIEMENT PRODUCTION CORRIGÉ - Gestion Ubuntu + sudo
set -e

echo "🚀 DÉPLOIEMENT EMERAUDEVIZ NTP - VERSION CORRIGÉE"
echo "================================================"

GITHUB_REPO="https://github.com/gilandre/NTPVIZ.git"
GITHUB_BRANCH="dev"
REMOTE_SERVER="79.137.36.66"
REMOTE_USER="ubuntu"
PROJECT_DIR="/opt/NTPVIZ"
SERVICE_NAME="ntp-monitor"

echo "📍 Serveur: $REMOTE_SERVER"
echo "👤 Utilisateur: $REMOTE_USER"
echo "🕒 $(date)"

# Test connexion
if ! ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_SERVER "echo 'SSH OK'"; then
    echo "❌ Connexion SSH échouée"
    exit 1
fi

echo "✅ Connexion SSH établie"

# Créer et transférer le script de déploiement
echo "📝 Transfert du script sur le serveur..."

cat > /tmp/deploy_server.sh << 'EOF'
#!/bin/bash
set -e

echo "🔄 Déploiement sur serveur..."

GITHUB_REPO="https://github.com/gilandre/NTPVIZ.git"
GITHUB_BRANCH="dev"
PROJECT_DIR="/opt/NTPVIZ"
SERVICE_NAME="ntp-monitor"
BACKUP_DIR="/tmp/ntp_backup_$(date +%Y%m%d_%H%M%S)"

# Vérification sudo
if ! sudo -n true 2>/dev/null; then
    echo "❌ Privilèges sudo requis"
    echo "Configuration: sudo visudo"
    echo "Ajouter: $USER ALL=(ALL) NOPASSWD:ALL"
    exit 1
fi

# Stopper service
echo "🛑 Arrêt service..."
sudo systemctl stop $SERVICE_NAME 2>/dev/null || true

# Sauvegarde
echo "💾 Sauvegarde..."
mkdir -p $BACKUP_DIR
if [ -d "$PROJECT_DIR" ]; then
    sudo cp -r $PROJECT_DIR/* $BACKUP_DIR/ 2>/dev/null || true
    echo "✅ Sauvegarde: $BACKUP_DIR"
fi

# Clone GitHub
echo "📥 Clone GitHub..."
sudo rm -rf $PROJECT_DIR
sudo git clone -b $GITHUB_BRANCH $GITHUB_REPO $PROJECT_DIR
cd $PROJECT_DIR

echo "✅ Repository cloné: $(git rev-parse HEAD | cut -c1-8)"

# Installation système
echo "🔧 Installation système..."
sudo apt update -qq
sudo apt install -y python3 python3-pip python3-venv git nginx sqlite3

# Utilisateur service
if ! id "ntp-monitor" &>/dev/null; then
    sudo useradd -r -s /bin/bash -d $PROJECT_DIR ntp-monitor
fi

# Environnement Python
echo "🐍 Configuration Python..."
sudo python3 -m venv .venv
sudo chown -R ntp-monitor:ntp-monitor .venv

# Installation packages
sudo -u ntp-monitor bash << 'PYINSTALL'
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q Flask==2.3.3 Werkzeug==2.3.7
pip install -q flask-login==0.6.3 flask-socketio==5.3.6
pip install -q SQLAlchemy==2.0.23 flask-sqlalchemy==3.1.1
pip install -q ntplib==0.4.0 python-dateutil==2.8.2 pytz==2023.3
pip install -q requests==2.31.0 redis==4.6.0 celery==5.3.4
echo "✅ Packages installés"
PYINSTALL

# Configuration
echo "⚙️ Configuration..."
sudo mkdir -p logs instance
sudo chown -R ntp-monitor:ntp-monitor logs instance

# Fichier .env
sudo tee .env > /dev/null << 'ENVEOF'
FLASK_ENV=production
FLASK_APP=app.py
SECRET_KEY=emeraudeviz-ntp-production
DATABASE_URL=sqlite:///instance/ntp_monitor.db
HOST=0.0.0.0
PORT=5000
ENVEOF

# Service systemd
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << 'SYSEOF'
[Unit]
Description=EMERAUDEVIZ NTP Enterprise
After=network.target

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

[Install]
WantedBy=multi-user.target
SYSEOF

# Configuration Nginx
sudo tee /etc/nginx/sites-available/ntp-monitor > /dev/null << 'NGXEOF'
server {
    listen 80;
    server_name 79.137.36.66 localhost;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location /static/ {
        alias /opt/NTPVIZ/frontend/static/;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
    }
}
NGXEOF

sudo ln -sf /etc/nginx/sites-available/ntp-monitor /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Permissions
sudo chown -R ntp-monitor:ntp-monitor $PROJECT_DIR
sudo chmod +x $PROJECT_DIR/app.py 2>/dev/null || true

# Tests
echo "🧪 Tests..."
sudo -u ntp-monitor bash -c "
cd $PROJECT_DIR
source .venv/bin/activate
export PYTHONPATH='$PROJECT_DIR'
python3 -c 'import app; print(\"✅ App OK\")'
"

if [ $? -ne 0 ]; then
    echo "❌ Tests échoués"
    exit 1
fi

# Démarrage services
echo "🚀 Démarrage..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo nginx -t && sudo systemctl restart nginx
sudo systemctl start $SERVICE_NAME

sleep 8

# Statut
echo "📊 Statut:"
sudo systemctl is-active $SERVICE_NAME
sudo systemctl is-active nginx

# Logs récents
echo "📋 Logs récents:"
sudo journalctl -u $SERVICE_NAME --no-pager -n 5

echo ""
echo "🎉 DÉPLOIEMENT TERMINÉ !"
echo "======================="
echo "🌐 URL: http://79.137.36.66/"
echo "📊 Santé: http://79.137.36.66/health"
echo "💾 Sauvegarde: $BACKUP_DIR"

if [ -f /var/run/reboot-required ]; then
    echo "⚠️ Redémarrage système recommandé: sudo reboot"
fi
EOF

# Transférer et exécuter
scp /tmp/deploy_server.sh $REMOTE_USER@$REMOTE_SERVER:/tmp/
ssh -t $REMOTE_USER@$REMOTE_SERVER "chmod +x /tmp/deploy_server.sh && /tmp/deploy_server.sh"

# Vérifications finales
echo ""
echo "🔍 Vérifications finales..."
sleep 3

if curl -I -s --connect-timeout 10 http://$REMOTE_SERVER/ | grep -q "200\|302"; then
    echo "✅ Application accessible"
else
    echo "⚠️ Application en démarrage"
fi

# Nettoyage
rm -f /tmp/deploy_server.sh
ssh $REMOTE_USER@$REMOTE_SERVER "rm -f /tmp/deploy_server.sh"

echo ""
echo "🎉 DÉPLOIEMENT GITHUB → PRODUCTION TERMINÉ !"
echo "============================================"
echo "🌐 URL: http://$REMOTE_SERVER/"
echo "📊 Santé: http://$REMOTE_SERVER/health"
echo "🔧 SSH: ssh $REMOTE_USER@$REMOTE_SERVER"
echo "📋 Logs: ssh $REMOTE_USER@$REMOTE_SERVER 'sudo journalctl -u ntp-monitor -f'"
echo ""
echo "🚀 EMERAUDEVIZ NTP ENTERPRISE EN PRODUCTION !" 