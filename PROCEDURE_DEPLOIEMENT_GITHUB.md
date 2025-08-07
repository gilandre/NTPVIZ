# 🚀 Procédure de Déploiement avec Mise à Jour depuis GitHub

## 📋 Vue d'ensemble

Cette procédure permet de déployer l'application NTP Monitor Enterprise sur un serveur Ubuntu 24.04 avec mise à jour automatique du code depuis GitHub.

## 🎯 Prérequis

### **Serveur Ubuntu 24.04 :**
- ✅ Accès root ou sudo
- ✅ Connexion Internet
- ✅ Au moins 2GB RAM
- ✅ 10GB espace disque libre

### **GitHub :**
- ✅ Repository accessible
- ✅ Branche `MacDev` disponible
- ✅ Clés SSH configurées (optionnel)

## 🔧 Scripts de déploiement

### **1. Script de déploiement initial complet**

```bash
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
pip install --upgrade pip
pip install -r requirements.txt

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
```

### **2. Script de mise à jour depuis GitHub**

```bash
#!/bin/bash
# update_from_github.sh
# Mise à jour du code depuis GitHub

set -e

echo "🔄 MISE À JOUR DEPUIS GITHUB"
echo "=============================="

# Variables
APP_DIR="/opt/ntp-monitor"
BRANCH="MacDev"
BACKUP_DIR="/opt/backups/ntp-monitor"

# Vérification des prérequis
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root"
    exit 1
fi

# Création du backup
echo "💾 Création du backup..."
mkdir -p $BACKUP_DIR
BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
cp -r $APP_DIR $BACKUP_DIR/$BACKUP_NAME
echo "✅ Backup créé: $BACKUP_DIR/$BACKUP_NAME"

# Arrêt du service
echo "⏹️ Arrêt du service..."
systemctl stop ntp-monitor

# Sauvegarde des fichiers de configuration
echo "📁 Sauvegarde des fichiers de configuration..."
cp $APP_DIR/.env $BACKUP_DIR/.env.backup
cp $APP_DIR/config/config.py $BACKUP_DIR/config.py.backup

# Mise à jour depuis GitHub
echo "📥 Mise à jour depuis GitHub..."
cd $APP_DIR
git fetch origin
git reset --hard origin/$BRANCH
git clean -fd

# Restauration des fichiers de configuration
echo "🔄 Restauration des fichiers de configuration..."
cp $BACKUP_DIR/.env.backup $APP_DIR/.env
cp $BACKUP_DIR/config.py.backup $APP_DIR/config/config.py

# Mise à jour des dépendances Python
echo "🐍 Mise à jour des dépendances Python..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Correction du schéma de base de données
echo "🔧 Correction du schéma de base de données..."
python fix_database_schema.py

# Harmonisation des modèles
echo "🔄 Harmonisation des modèles..."
python harmonize_models.py

# Test de l'application
echo "🧪 Test de l'application..."
python quick_verification.py

# Redémarrage du service
echo "🚀 Redémarrage du service..."
systemctl start ntp-monitor

# Vérification finale
echo "✅ Vérification finale..."
sleep 5
systemctl status ntp-monitor --no-pager

echo "🎉 MISE À JOUR TERMINÉE AVEC SUCCÈS!"
echo "🌐 Application accessible sur: http://$(hostname -I | awk '{print $1}')"
```

### **3. Script de rollback**

```bash
#!/bin/bash
# rollback.sh
# Rollback vers une version précédente

set -e

echo "🔄 ROLLBACK"
echo "============"

# Variables
APP_DIR="/opt/ntp-monitor"
BACKUP_DIR="/opt/backups/ntp-monitor"

# Vérification des prérequis
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root"
    exit 1
fi

# Liste des backups disponibles
echo "📋 Backups disponibles:"
ls -la $BACKUP_DIR

# Sélection du backup
read -p "Entrez le nom du backup à restaurer: " BACKUP_NAME

if [ ! -d "$BACKUP_DIR/$BACKUP_NAME" ]; then
    echo "❌ Backup non trouvé: $BACKUP_NAME"
    exit 1
fi

# Arrêt du service
echo "⏹️ Arrêt du service..."
systemctl stop ntp-monitor

# Restauration
echo "🔄 Restauration du backup..."
rm -rf $APP_DIR
cp -r $BACKUP_DIR/$BACKUP_NAME $APP_DIR

# Redémarrage du service
echo "🚀 Redémarrage du service..."
systemctl start ntp-monitor

# Vérification finale
echo "✅ Vérification finale..."
sleep 5
systemctl status ntp-monitor --no-pager

echo "🎉 ROLLBACK TERMINÉ AVEC SUCCÈS!"
```

## 📋 Procédure de déploiement étape par étape

### **Étape 1 : Préparation du serveur**

```bash
# Connexion au serveur
ssh root@votre-serveur-ip

# Mise à jour du système
apt update && apt upgrade -y

# Installation des outils de base
apt install -y curl wget git htop
```

### **Étape 2 : Déploiement initial**

```bash
# Téléchargement du script de déploiement
wget https://raw.githubusercontent.com/votre-username/NTPVIZ/MacDev/deploy_ubuntu_complete.sh

# Exécution du script
chmod +x deploy_ubuntu_complete.sh
./deploy_ubuntu_complete.sh
```

### **Étape 3 : Vérification du déploiement**

```bash
# Vérification du service
systemctl status ntp-monitor

# Vérification de l'application
curl -I http://localhost:5001

# Vérification des logs
journalctl -u ntp-monitor -f
```

### **Étape 4 : Mise à jour depuis GitHub**

```bash
# Téléchargement du script de mise à jour
wget https://raw.githubusercontent.com/votre-username/NTPVIZ/MacDev/update_from_github.sh

# Exécution du script
chmod +x update_from_github.sh
./update_from_github.sh
```

## 🔧 Configuration avancée

### **Configuration SSL avec Let's Encrypt**

```bash
# Installation de Certbot
apt install -y certbot python3-certbot-nginx

# Obtention du certificat SSL
certbot --nginx -d votre-domaine.com

# Configuration automatique du renouvellement
crontab -e
# Ajouter : 0 12 * * * /usr/bin/certbot renew --quiet
```

### **Configuration de la surveillance**

```bash
# Installation de monitoring
apt install -y htop iotop nethogs

# Configuration des logs
cat > /etc/logrotate.d/ntp-monitor << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF
```

## 📊 Monitoring et maintenance

### **Commandes utiles**

```bash
# Statut du service
systemctl status ntp-monitor

# Logs en temps réel
journalctl -u ntp-monitor -f

# Redémarrage du service
systemctl restart ntp-monitor

# Vérification de la base de données
mysql -u ntp_user -p ntp_monitor -e "SELECT COUNT(*) FROM users;"

# Sauvegarde de la base de données
mysqldump -u ntp_user -p ntp_monitor > backup_$(date +%Y%m%d_%H%M%S).sql
```

### **Surveillance des performances**

```bash
# Utilisation CPU et mémoire
htop

# Utilisation disque
df -h

# Utilisation réseau
nethogs

# Logs d'erreur
tail -f $APP_DIR/logs/error.log
```

## 🚨 Dépannage

### **Problèmes courants**

#### **1. Service ne démarre pas**
```bash
# Vérification des logs
journalctl -u ntp-monitor -n 50

# Vérification de la configuration
python quick_verification.py

# Redémarrage manuel
cd /opt/ntp-monitor
source .venv/bin/activate
python app.py
```

#### **2. Erreur de base de données**
```bash
# Vérification de la connexion MySQL
mysql -u ntp_user -p -e "SELECT 1;"

# Correction du schéma
python fix_database_schema.py

# Réinitialisation de la base
python initialiser_database.py
```

#### **3. Erreur de permissions**
```bash
# Correction des permissions
chown -R root:root /opt/ntp-monitor
chmod -R 755 /opt/ntp-monitor
chmod 644 /opt/ntp-monitor/.env
```

## 📈 Métriques de succès

### **Indicateurs de performance**
- ✅ Service démarré et fonctionnel
- ✅ Application accessible sur le port 80/443
- ✅ Base de données connectée et opérationnelle
- ✅ Tests de vérification réussis
- ✅ Logs sans erreur critique

### **Vérifications post-déploiement**
```bash
# Test complet
python quick_verification.py

# Test de l'interface web
curl -I http://localhost

# Test de la base de données
python -c "from backend.database_manager import get_db_session_with_context; print('✅ DB OK')"
```

## 🎉 Conclusion

Cette procédure permet un déploiement complet et automatisé de l'application NTP Monitor Enterprise sur un serveur Ubuntu 24.04 avec :

- ✅ **Déploiement initial** automatisé depuis GitHub
- ✅ **Mises à jour** automatiques depuis la branche MacDev
- ✅ **Rollback** en cas de problème
- ✅ **Monitoring** et maintenance
- ✅ **Sécurité** avec firewall et SSL
- ✅ **Performance** optimisée

**L'application est prête pour la production !** 🚀

---

*Procédure générée le 7 août 2025* 