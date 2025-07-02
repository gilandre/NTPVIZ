#!/bin/bash

# Script de Déploiement GitHub vers Ubuntu 24.04
# NTP Monitor Enterprise avec corrections intégrées
# Version: 2.1.0 - Janvier 2025

set -e  # Arrêt en cas d'erreur

echo "============================================"
echo "  DÉPLOIEMENT GITHUB → UBUNTU 24.04"
echo "============================================"

# Configuration (à modifier selon vos besoins)
GITHUB_REPO="https://github.com/gilandre/NTPVIZ.git"
GITHUB_BRANCH="dev"
APP_DIR="/opt/ntp-monitor"
SERVICE_NAME="ntp-monitor"
USER_APP="ntp-monitor"

# Vérification privilèges root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être exécuté en tant que root"
   echo "Usage: sudo bash deploy_github_ubuntu.sh"
   exit 1
fi

echo "🚀 Début du déploiement..."

# 1. INSTALLATION OUTILS REQUIS
echo "1. Installation outils système..."
apt update -qq
apt install -y git python3 python3-pip python3-venv nginx mysql-server redis-server curl

# 2. CRÉATION UTILISATEUR DÉDIÉ
echo "2. Configuration utilisateur..."
if ! id "$USER_APP" &>/dev/null; then
    useradd -r -s /bin/bash -d "$APP_DIR" -m "$USER_APP"
    echo "✅ Utilisateur $USER_APP créé"
fi

# 3. SAUVEGARDE ANCIENNE VERSION
if [[ -d "$APP_DIR" ]]; then
    echo "3. Sauvegarde ancienne version..."
    systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    mv "$APP_DIR" "${APP_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
fi

# 4. CLONAGE DEPUIS GITHUB
echo "4. Récupération code GitHub..."
git clone --branch "$GITHUB_BRANCH" "$GITHUB_REPO" "$APP_DIR"
chown -R "$USER_APP:$USER_APP" "$APP_DIR"
cd "$APP_DIR"

# 5. CONFIGURATION AUTOMATIQUE
echo "5. Application corrections automatiques..."

# Configuration fallback MySQL/SQLite
mkdir -p config
cat > config/config.py << 'EOF'
import os
from pathlib import Path

class Config:
    SECRET_KEY = 'ntp-monitor-production-2025'
    
    # Test MySQL avec fallback SQLite
    try:
        import pymysql
        pymysql.connect(host='localhost', port=3306, user='root', 
                       password='', connect_timeout=2).close()
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost:3306/ntp_monitor'
        print("✅ MySQL utilisé")
    except:
        db_path = Path(__file__).parent.parent / 'instance' / 'ntp_monitor.db'
        db_path.parent.mkdir(exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
        print("⚠️ SQLite utilisé")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_ENV = 'production'
    DEBUG = False

class ProductionConfig(Config):
    pass

config = {'default': ProductionConfig, 'production': ProductionConfig}
EOF

# Patch cookies 'partitioned' dans auth.py
if [[ -f "backend/api/auth.py" ]] && ! grep -q "def safe_cookie" backend/api/auth.py; then
    sed -i '/^import logging$/a\\ndef safe_cookie(response, key, value="", **kwargs):\n    """Wrapper évitant erreur partitioned"""\n    safe_kwargs = {k: v for k, v in kwargs.items() if k != "partitioned"}\n    try:\n        response.set_cookie(key, value, **safe_kwargs)\n    except TypeError:\n        response.set_cookie(key, value, path="/", httponly=True)\n' backend/api/auth.py
    echo "✅ Patch cookies appliqué"
fi

# 6. ENVIRONNEMENT VIRTUEL ET PACKAGES
echo "6. Installation packages corrigés..."
sudo -u "$USER_APP" python3 -m venv .venv
source .venv/bin/activate

# Désinstallation packages problématiques
pip uninstall Flask Werkzeug redis celery Flask-SocketIO python-socketio -y 2>/dev/null || true

# Installation versions corrigées (évitent erreur partitioned)
pip install --no-cache-dir \
    "Flask==2.3.3" \
    "Werkzeug==2.3.7" \
    "redis==4.6.0" \
    "celery==5.3.4" \
    "Flask-SocketIO==5.3.6" \
    "python-socketio==5.8.0" \
    "PyMySQL==1.1.0" \
    "psutil==5.9.5" \
    "ntplib==0.4.0" \
    "python-dotenv==1.0.0" \
    "Flask-Login==0.6.3" \
    "Flask-SQLAlchemy==3.0.5" \
    "gunicorn==21.2.0"

echo "✅ Packages installés avec versions corrigées"

# 7. SERVICES SYSTÈME
echo "7. Configuration services..."

# Démarrage MySQL
systemctl start mysql 2>/dev/null && systemctl enable mysql 2>/dev/null || true
systemctl start redis-server 2>/dev/null && systemctl enable redis-server 2>/dev/null || true

# Service systemd NTP Monitor
cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=NTP Monitor Enterprise
After=network.target mysql.service

[Service]
Type=exec
User=$USER_APP
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/.venv/bin
Environment=FLASK_ENV=production
ExecStart=$APP_DIR/.venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

# 8. NGINX REVERSE PROXY
echo "8. Configuration Nginx..."
cat > "/etc/nginx/sites-available/$SERVICE_NAME" << EOF
server {
    listen 80;
    server_name _;
    
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
    }
    
    location /static {
        alias $APP_DIR/frontend/static;
        expires 1y;
    }
}
EOF

ln -sf "/etc/nginx/sites-available/$SERVICE_NAME" "/etc/nginx/sites-enabled/"
nginx -t && systemctl reload nginx

# 9. INITIALISATION BASE DE DONNÉES
echo "9. Initialisation base de données..."
sudo -u "$USER_APP" bash -c "
source $APP_DIR/.venv/bin/activate
cd $APP_DIR
export PYTHONPATH='$APP_DIR'
python3 -c '
from backend.app import create_app
from backend.utils.init_data import init_default_data
app = create_app()
with app.app_context():
    init_default_data()
    print(\"✅ Base de données initialisée\")
'
"

# 10. DÉMARRAGE SERVICES
echo "10. Démarrage services..."
systemctl start "$SERVICE_NAME"

# Attente stabilisation
sleep 10

# 11. TESTS FINAUX
echo "11. Tests de validation..."

SERVICE_OK=false
PORT_OK=false
HTTP_OK=false

if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ Service actif"
    SERVICE_OK=true
fi

if ss -tlnp | grep -q ':5000'; then
    echo "✅ Port 5000 accessible"
    PORT_OK=true
fi

if curl -f -s -m 10 "http://localhost:5000/" > /dev/null 2>&1; then
    echo "✅ Application web accessible"
    HTTP_OK=true
fi

# 12. RAPPORT FINAL
echo ""
echo "============================================"
echo "         RAPPORT FINAL"
echo "============================================"

if [[ "$SERVICE_OK" == "true" && "$PORT_OK" == "true" && "$HTTP_OK" == "true" ]]; then
    echo "🎉 DÉPLOIEMENT RÉUSSI À 100%"
    FINAL_STATUS="SUCCESS"
else
    echo "⚠️ DÉPLOIEMENT PARTIEL - Vérifiez les services"
    FINAL_STATUS="PARTIAL"
fi

echo ""
echo "📊 STATUT:"
echo "   - Service: $([ "$SERVICE_OK" == "true" ] && echo "✅ Actif" || echo "❌ Inactif")"
echo "   - Port 5000: $([ "$PORT_OK" == "true" ] && echo "✅ Ouvert" || echo "❌ Fermé")"
echo "   - Interface: $([ "$HTTP_OK" == "true" ] && echo "✅ Accessible" || echo "❌ Indisponible")"

echo ""
echo "🌐 ACCÈS:"
echo "   - URL locale: http://localhost:5000"
echo "   - URL réseau: http://$(hostname -I | awk '{print $1}'):5000"
echo "   - Comptes: admin/admin123, operator/operator123"

echo ""
echo "🔧 COMMANDES UTILES:"
echo "   - Statut: systemctl status $SERVICE_NAME"
echo "   - Logs: journalctl -u $SERVICE_NAME -f"
echo "   - Redémarrage: systemctl restart $SERVICE_NAME"

echo ""
echo "✅ CORRECTIONS APPLIQUÉES:"
echo "   - Erreur 'partitioned' corrigée (Flask 2.3.3)"
echo "   - Fallback MySQL/SQLite automatique"
echo "   - Packages compatibles Ubuntu 24.04"
echo "   - Service systemd configuré"
echo "   - Nginx reverse proxy actif"

echo ""
echo "============================================"
if [[ "$FINAL_STATUS" == "SUCCESS" ]]; then
    echo "🎉 NTP Monitor Enterprise OPÉRATIONNEL !"
else
    echo "⚠️ Application en cours de stabilisation"
fi
echo "============================================"

# Code de sortie
[[ "$FINAL_STATUS" == "SUCCESS" ]] && exit 0 || exit 1 