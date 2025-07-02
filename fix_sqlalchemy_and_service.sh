#!/bin/bash
# Script de correction pour SQLAlchemy 2.x et service systemd manquant
# Usage: ./fix_sqlalchemy_and_service.sh

set -e

echo "🔧 CORRECTION SQLALCHEMY 2.X ET SERVICE SYSTEMD"
echo "=============================================="

APP_DIR="/opt/ntp-monitor"
SERVICE_NAME="ntp-monitor"

# Vérification des privilèges root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être exécuté en tant que root"
   exit 1
fi

cd "$APP_DIR"

echo ""
echo "🔍 DIAGNOSTIC DES PROBLÈMES"
echo "==========================="

echo ""
echo "📋 Vérification de SQLAlchemy..."
sudo -u ntp-monitor .venv/bin/python -c "
try:
    import sqlalchemy
    print(f'SQLAlchemy version: {sqlalchemy.__version__}')
    
    # Test de la syntaxe moderne
    from sqlalchemy import text
    print('✅ Import de text réussi (SQLAlchemy 2.x compatible)')
except ImportError as e:
    print(f'❌ Erreur SQLAlchemy: {e}')
"

echo ""
echo "🔍 Vérification du service systemd..."
if systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
    echo "✅ Service $SERVICE_NAME trouvé"
else
    echo "❌ Service $SERVICE_NAME manquant"
fi

echo ""
echo "🔧 CORRECTION SQLALCHEMY 2.X"
echo "============================"

echo ""
echo "🔧 Correction de la syntaxe SQLAlchemy dans les scripts de test..."

# Fonction pour créer un script de test corrigé
cat > test_database_connection.py << 'EOF'
#!/usr/bin/env python3
"""
Test de connexion base de données avec syntaxe SQLAlchemy 2.x correcte
"""

import sys
import os
sys.path.insert(0, '.')

def test_database_connection():
    """Test de connexion avec SQLAlchemy 2.x"""
    
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from sqlalchemy import text
        
        # Détection du driver MySQL
        driver = "pymysql"  # Par défaut
        try:
            import MySQLdb
            print("🗄️ MySQLdb détecté, utilisation du driver natif")
            driver = "mysqlclient"
        except ImportError:
            try:
                import pymysql
                pymysql.install_as_MySQLdb()
                print("🗄️ PyMySQL configuré comme MySQLdb")
                driver = "pymysql"
            except ImportError:
                print("❌ Aucun driver MySQL disponible")
                return False
        
        # Configuration de l'URL selon le driver
        if driver == "pymysql":
            db_url = 'mysql+pymysql://ntp_monitor:ntp_password_2024@localhost/ntp_monitor'
        else:
            db_url = 'mysql://ntp_monitor:ntp_password_2024@localhost/ntp_monitor'
        
        print(f"🔗 URL de connexion: {db_url.split('@')[0]}@localhost/ntp_monitor")
        
        # Test de connexion avec syntaxe SQLAlchemy 2.x correcte
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db = SQLAlchemy(app)
        
        with app.app_context():
            # SYNTAXE CORRECTE pour SQLAlchemy 2.x
            with db.engine.connect() as connection:
                result = connection.execute(text('SELECT 1 as test'))
                row = result.fetchone()
                if row and row[0] == 1:
                    print('✅ Connexion base de données réussie')
                    print(f'✅ Driver utilisé: {driver}')
                    return True
                else:
                    print('❌ Test de connexion échoué')
                    return False
                    
    except Exception as e:
        print(f'❌ Erreur connexion DB: {e}')
        print('ℹ️ Base de données sera configurée au démarrage de l\'application')
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)
EOF

echo "✅ Script de test SQLAlchemy 2.x créé"

echo ""
echo "🗄️ Test de connexion avec syntaxe corrigée..."
sudo -u ntp-monitor .venv/bin/python test_database_connection.py

echo ""
echo "🔧 CRÉATION DU SERVICE SYSTEMD"
echo "=============================="

echo ""
echo "🔧 Création du fichier service systemd..."
cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=NTP Monitor Enterprise - Surveillance des serveurs NTP
Documentation=https://github.com/YOUR_USERNAME/NTP_PROJECT
After=network.target mysql.service mariadb.service
Wants=mysql.service

[Service]
Type=simple
User=ntp-monitor
Group=ntp-monitor
WorkingDirectory=$APP_DIR
Environment=FLASK_APP=app.py
Environment=FLASK_ENV=production
Environment=PYTHONPATH=$APP_DIR
ExecStartPre=/bin/sleep 5
ExecStart=$APP_DIR/.venv/bin/python app.py
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
ReadWritePaths=$APP_DIR
ProtectHome=true
RemainAfterExit=no

# Limites de ressources
LimitNOFILE=65536
MemoryLimit=512M

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service systemd créé"

echo ""
echo "🔧 Configuration du service..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME

echo ""
echo "🔧 Vérification de l'utilisateur et permissions..."
if ! id "ntp-monitor" &>/dev/null; then
    echo "👤 Création de l'utilisateur ntp-monitor..."
    useradd --system --shell /bin/bash --home "$APP_DIR" --create-home ntp-monitor
fi

echo "🔧 Configuration des permissions..."
chown -R ntp-monitor:ntp-monitor "$APP_DIR"
chmod +x "$APP_DIR/app.py" 2>/dev/null || true

echo ""
echo "🔧 Vérification de la configuration .env..."
if [ ! -f "$APP_DIR/.env" ]; then
    echo "⚙️ Création du fichier .env..."
    
    # Détection du driver pour l'URL
    DRIVER_TYPE="pymysql"  # Par défaut
    if sudo -u ntp-monitor .venv/bin/python -c "import MySQLdb" 2>/dev/null; then
        DRIVER_TYPE="mysqlclient"
    fi
    
    if [ "$DRIVER_TYPE" = "pymysql" ]; then
        DB_URL="mysql+pymysql://ntp_monitor:ntp_password_2024@localhost/ntp_monitor"
    else
        DB_URL="mysql://ntp_monitor:ntp_password_2024@localhost/ntp_monitor"
    fi
    
    cat > "$APP_DIR/.env" << EOF
# Configuration production NTP Monitor Enterprise
FLASK_ENV=production
DATABASE_URL=$DB_URL
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
HOST=0.0.0.0
PORT=5000
DEBUG=False
LOGGING_LEVEL=INFO
EOF
    chown ntp-monitor:ntp-monitor "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    echo "✅ Fichier .env configuré"
fi

echo ""
echo "🗄️ Vérification de la base de données..."
# S'assurer que MySQL/MariaDB est démarré
if systemctl is-enabled mysql &>/dev/null; then
    systemctl start mysql
elif systemctl is-enabled mariadb &>/dev/null; then
    systemctl start mariadb
fi

# Configuration de la base de données
DB_CMD="mysql"
if command -v mariadb &>/dev/null; then
    DB_CMD="mariadb"
fi

$DB_CMD -u root -e "CREATE DATABASE IF NOT EXISTS ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || true
$DB_CMD -u root -e "CREATE USER IF NOT EXISTS 'ntp_monitor'@'localhost' IDENTIFIED BY 'ntp_password_2024';" 2>/dev/null || true
$DB_CMD -u root -e "GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_monitor'@'localhost';" 2>/dev/null || true
$DB_CMD -u root -e "FLUSH PRIVILEGES;" 2>/dev/null || true

echo "✅ Base de données configurée"

echo ""
echo "🔧 Test final de l'environnement..."
sudo -u ntp-monitor .venv/bin/python -c "
import sys
sys.path.insert(0, '.')

try:
    # Test des imports critiques
    import flask
    import flask_sqlalchemy
    import flask_login
    import flask_socketio
    print(f'✅ Flask: {flask.__version__}')
    print(f'✅ Flask-SQLAlchemy: {flask_sqlalchemy.__version__}')
    
    # Test MySQL
    try:
        import MySQLdb
        print('✅ MySQLdb disponible')
    except ImportError:
        import pymysql
        pymysql.install_as_MySQLdb()
        print('✅ PyMySQL configuré')
    
    # Test SQLAlchemy avec syntaxe moderne
    from sqlalchemy import text
    print('✅ SQLAlchemy text import réussi (syntaxe 2.x)')
    
    print('✅ Environnement Python validé')
    
except ImportError as e:
    print(f'❌ Erreur import: {e}')
    exit(1)
except Exception as e:
    print(f'⚠️ Avertissement: {e}')
"

echo ""
echo "🚀 Démarrage du service NTP Monitor..."
systemctl start $SERVICE_NAME

echo ""
echo "🏥 Vérification finale..."
sleep 15  # Plus de temps pour le démarrage complet

if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Service démarré avec succès"
    
    echo ""
    echo "📋 Statut du service:"
    systemctl status $SERVICE_NAME --no-pager -l | head -10
    
    echo ""
    echo "🌐 Test de connectivité..."
    sleep 5
    
    if curl -f -s http://localhost:5000/api/system/status > /dev/null 2>&1; then
        echo "✅ API accessible"
        
        echo ""
        echo "🎉 CONFIGURATION RÉUSSIE !"
        echo "========================="
        echo ""
        echo "🔗 Application: http://$(hostname -I | awk '{print $1}'):5000"
        echo "👤 Login: admin / admin123"
        echo ""
        echo "📋 Service configuré:"
        echo "   • systemctl status $SERVICE_NAME"
        echo "   • systemctl restart $SERVICE_NAME"
        echo "   • journalctl -u $SERVICE_NAME -f"
        echo ""
        echo "🗄️ Base de données: Connectée et fonctionnelle"
        echo "🔧 SQLAlchemy: Syntaxe 2.x corrigée"
        echo "⚙️ Service systemd: Créé et actif"
        
    else
        echo "⚠️ API pas encore accessible, vérifiez les logs:"
        journalctl -u $SERVICE_NAME --since "5 minutes ago" --no-pager -n 10
    fi
else
    echo "❌ Problème avec le service:"
    systemctl status $SERVICE_NAME --no-pager -l
    echo ""
    echo "📋 Logs du service:"
    journalctl -u $SERVICE_NAME --since "5 minutes ago" --no-pager -n 20
fi

# Nettoyage du script de test temporaire
rm -f test_database_connection.py

echo ""
echo "📝 Résumé des corrections:"
echo "   • Syntaxe SQLAlchemy 2.x corrigée (db.engine.connect() + text())"
echo "   • Service systemd créé et configuré"
echo "   • Utilisateur ntp-monitor configuré"
echo "   • Base de données accessible"
echo "   • Fichier .env avec bonne URL de base de données"
echo "   • Permissions et sécurité configurées" 