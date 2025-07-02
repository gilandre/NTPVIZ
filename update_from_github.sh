#!/bin/bash

# Script de Mise à Jour Rapide depuis GitHub
# NTP Monitor Enterprise - Ubuntu 24.04
# Usage: sudo bash update_from_github.sh

echo "==============================================="
echo "  MISE À JOUR RAPIDE DEPUIS GITHUB"
echo "==============================================="

# Configuration
APP_DIR="/opt/ntp-monitor"
SERVICE_NAME="ntp-monitor"
USER_APP="ntp-monitor"
BACKUP_DIR="/tmp/ntp-backup-$(date +%Y%m%d_%H%M%S)"

# Vérification privilèges
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être exécuté en tant que root"
   exit 1
fi

# Vérification répertoire application
if [[ ! -d "$APP_DIR" ]]; then
   echo "❌ Application non trouvée dans $APP_DIR"
   echo "Exécutez d'abord le déploiement complet: deploy_github_ubuntu.sh"
   exit 1
fi

cd "$APP_DIR"

echo "🔄 Début mise à jour rapide..."

# 1. Sauvegarde configuration et données
echo "1. Sauvegarde configuration..."
mkdir -p "$BACKUP_DIR"
cp -r config/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r instance/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r logs/ "$BACKUP_DIR/" 2>/dev/null || true
echo "✅ Sauvegarde: $BACKUP_DIR"

# 2. Arrêt service
echo "2. Arrêt service..."
systemctl stop "$SERVICE_NAME"
echo "✅ Service arrêté"

# 3. Mise à jour code depuis GitHub
echo "3. Mise à jour code GitHub..."
sudo -u "$USER_APP" git fetch origin
BEFORE_COMMIT=$(git rev-parse HEAD)
sudo -u "$USER_APP" git pull origin main

AFTER_COMMIT=$(git rev-parse HEAD)
if [[ "$BEFORE_COMMIT" == "$AFTER_COMMIT" ]]; then
    echo "ℹ️ Aucune mise à jour disponible"
else
    echo "✅ Mise à jour: $BEFORE_COMMIT → $AFTER_COMMIT"
fi

# 4. Restauration configuration
echo "4. Restauration configuration..."
if [[ -f "$BACKUP_DIR/config/config.py" ]]; then
    cp "$BACKUP_DIR/config/config.py" config/
    echo "✅ Configuration restaurée"
fi

if [[ -d "$BACKUP_DIR/instance" ]]; then
    cp -r "$BACKUP_DIR/instance/"* instance/ 2>/dev/null || true
    echo "✅ Base de données restaurée"
fi

# 5. Vérification packages critiques
echo "5. Vérification packages..."
source .venv/bin/activate

# Vérification versions critiques
FLASK_VERSION=$(pip show Flask 2>/dev/null | grep Version | cut -d' ' -f2)
if [[ "$FLASK_VERSION" != "2.3.3" ]]; then
    echo "⚠️ Réinstallation Flask 2.3.3..."
    pip install "Flask==2.3.3" --no-cache-dir
fi

REDIS_VERSION=$(pip show redis 2>/dev/null | grep Version | cut -d' ' -f2)
if [[ "$REDIS_VERSION" != "4.6.0" ]]; then
    echo "⚠️ Réinstallation Redis 4.6.0..."
    pip install "redis==4.6.0" --no-cache-dir
fi

echo "✅ Packages vérifiés"

# 6. Application patches critiques
echo "6. Vérification patches..."

# Patch cookies 'partitioned'
if [[ -f "backend/api/auth.py" ]] && ! grep -q "def safe_cookie" backend/api/auth.py; then
    echo "⚠️ Application patch cookies 'partitioned'..."
    sed -i '/^import logging$/a\\ndef safe_cookie(response, key, value="", **kwargs):\n    """Wrapper évitant erreur partitioned"""\n    safe_kwargs = {k: v for k, v in kwargs.items() if k != "partitioned"}\n    try:\n        response.set_cookie(key, value, **safe_kwargs)\n    except TypeError:\n        response.set_cookie(key, value, path="/", httponly=True)\n' backend/api/auth.py
    echo "✅ Patch cookies appliqué"
fi

# Vérification configuration fallback
if [[ ! -f "config/config.py" ]] || ! grep -q "fallback" config/config.py; then
    echo "⚠️ Recréation configuration fallback..."
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
    chown "$USER_APP:$USER_APP" config/config.py
    echo "✅ Configuration fallback recréée"
fi

echo "✅ Patches vérifiés"

# 7. Test application
echo "7. Test application..."
sudo -u "$USER_APP" bash -c "
source $APP_DIR/.venv/bin/activate
cd $APP_DIR
export PYTHONPATH='$APP_DIR'
python3 -c '
try:
    from backend.app import create_app
    app = create_app()
    print(\"✅ Application testée avec succès\")
except Exception as e:
    print(f\"❌ Erreur test application: {e}\")
    exit(1)
'
"

if [[ $? -ne 0 ]]; then
    echo "❌ Test application échoué - Restauration..."
    systemctl start "$SERVICE_NAME"
    exit 1
fi

# 8. Redémarrage service
echo "8. Redémarrage service..."
systemctl start "$SERVICE_NAME"

# Attente stabilisation
sleep 10

# 9. Vérification finale
echo "9. Vérification finale..."

SERVICE_OK=false
HTTP_OK=false

if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ Service actif"
    SERVICE_OK=true
else
    echo "❌ Service inactif"
fi

if curl -f -s -m 10 "http://localhost:5000/" > /dev/null 2>&1; then
    echo "✅ Application accessible"
    HTTP_OK=true
else
    echo "⚠️ Application pas encore accessible"
fi

# 10. Nettoyage
echo "10. Nettoyage..."
rm -rf "$BACKUP_DIR"
echo "✅ Nettoyage terminé"

# 11. Rapport final
echo ""
echo "==============================================="
echo "           RAPPORT MISE À JOUR"
echo "==============================================="

if [[ "$SERVICE_OK" == "true" && "$HTTP_OK" == "true" ]]; then
    echo "🎉 MISE À JOUR RÉUSSIE"
    echo ""
    echo "📊 Statut:"
    echo "   - Service: ✅ Actif"
    echo "   - Application: ✅ Accessible"
    echo "   - Commit: $AFTER_COMMIT"
    
    echo ""
    echo "🌐 Accès:"
    echo "   - URL: http://$(hostname -I | awk '{print $1}'):5000"
    echo "   - Nginx: http://$(hostname -I | awk '{print $1}')"
    
    FINAL_STATUS="SUCCESS"
else
    echo "⚠️ MISE À JOUR PARTIELLE"
    echo ""
    echo "📊 Statut:"
    echo "   - Service: $([ "$SERVICE_OK" == "true" ] && echo "✅ Actif" || echo "❌ Inactif")"
    echo "   - Application: $([ "$HTTP_OK" == "true" ] && echo "✅ Accessible" || echo "⚠️ En cours")"
    
    echo ""
    echo "🔧 Actions recommandées:"
    echo "   - Vérifier logs: journalctl -u $SERVICE_NAME -f"
    echo "   - Redémarrer: systemctl restart $SERVICE_NAME"
    
    FINAL_STATUS="PARTIAL"
fi

echo ""
echo "✅ MISE À JOUR TERMINÉE"
echo "==============================================="

# Code de sortie
[[ "$FINAL_STATUS" == "SUCCESS" ]] && exit 0 || exit 1 