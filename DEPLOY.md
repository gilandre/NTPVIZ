# 🚀 Guide de Déploiement - NTP Monitor Enterprise v2.1.0

Guide complet pour déployer NTP Monitor Enterprise sur Ubuntu 24.04 avec tous les prérequis et optimisations.

## 📋 Prérequis Système

- **OS** : Ubuntu 24.04 LTS (compatible 22.04/20.04)
- **RAM** : 2GB minimum, 4GB recommandé
- **Disque** : 10GB libre minimum  
- **Accès** : Privilèges sudo/root
- **Réseau** : Connexion Internet pour synchronisation

## 🚀 Installation One-Click (Recommandée)

### Méthode 1 : Installation complète automatique
```bash
# Installation complète en une seule commande
curl -fsSL https://raw.githubusercontent.com/votre-username/ntp-monitor-enterprise/main/quick_install_ubuntu24.sh | sudo bash
```

### Méthode 2 : Installation étape par étape
```bash
# 1. Vérifier les prérequis
curl -fsSL https://raw.githubusercontent.com/votre-username/ntp-monitor-enterprise/main/check_prerequisites.sh | bash

# 2. Installer les dépendances
curl -fsSL https://raw.githubusercontent.com/votre-username/ntp-monitor-enterprise/main/install_dependencies.sh | sudo bash

# 3. Déployer l'application
curl -fsSL https://raw.githubusercontent.com/votre-username/ntp-monitor-enterprise/main/deploy_application.sh | sudo bash
```

## 🔧 Installation Manuelle

### 1. Cloner le repository
```bash
# Cloner depuis GitHub (branche main pour production)
git clone https://github.com/votre-username/ntp-monitor-enterprise.git
cd ntp-monitor-enterprise

# Ou depuis votre serveur Git
git clone -b main https://your-git-server.com/ntp-monitor-enterprise.git
cd ntp-monitor-enterprise
```

### 2. Installer les prérequis système
```bash
# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Installer les packages essentiels
sudo apt install -y \
    python3 python3-pip python3-venv python3-dev \
    mysql-server mysql-client libmysqlclient-dev \
    apache2 libapache2-mod-wsgi-py3 \
    redis-server \
    ntpsec ntpdate \
    curl wget git htop vim tree \
    build-essential pkg-config \
    ufw

# Configurer le pare-feu
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5000/tcp
sudo ufw --force enable
```

### 3. Configurer MySQL
```bash
# Sécuriser MySQL
sudo mysql_secure_installation

# Créer la base de données et l'utilisateur
sudo mysql -e "
CREATE DATABASE ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ntp_user'@'localhost' IDENTIFIED BY 'mot_de_passe_securise';
GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_user'@'localhost';
FLUSH PRIVILEGES;"
```

### 4. Créer l'environnement virtuel Python
```bash
# Créer l'environnement virtuel
python3 -m venv /opt/ntp-monitor-venv

# Activer l'environnement virtuel
source /opt/ntp-monitor-venv/bin/activate

# Mettre à jour pip
pip install --upgrade pip setuptools wheel

# Installer les dépendances
pip install -r requirements.txt
```

### 5. Configurer l'application
```bash
# Copier la configuration exemple
cp .env.example .env

# Éditer la configuration
nano .env
```

**Configuration .env pour production :**
```env
# Configuration NTP Monitor Enterprise
FLASK_ENV=production
SECRET_KEY=changez-cette-clé-secrète-très-longue-et-sécurisée
DEBUG=false
HOST=0.0.0.0
PORT=5000

# Base de données MySQL
DATABASE_URL=mysql+pymysql://ntp_user:mot_de_passe_securise@localhost/ntp_monitor

# Configuration NTP
DEFAULT_NTP_SERVERS=pool.ntp.org,time.google.com,time.cloudflare.com
LOCAL_NTP_SERVERS=192.168.1.100,10.0.0.50

# Seuils d'alertes (en millisecondes)
ALERT_OFFSET_THRESHOLD=100
ALERT_DELAY_THRESHOLD=500

# Redis pour le cache
REDIS_URL=redis://localhost:6379/0

# Logs
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5
```

### 6. Initialiser la base de données
```bash
# Initialiser la base de données avec les données par défaut
python init_database.py

# Vérifier que les tables sont créées
mysql -u ntp_user -p ntp_monitor -e "SHOW TABLES;"
```

### 7. Configurer Apache
```bash
# Créer la configuration Apache
sudo tee /etc/apache2/sites-available/ntp-monitor.conf << 'EOF'
<VirtualHost *:80>
    ServerName votre-domaine.com
    WSGIDaemonProcess ntp-monitor python-home=/opt/ntp-monitor-venv python-path=/opt/ntp-monitor-enterprise
    WSGIProcessGroup ntp-monitor
    WSGIScriptAlias / /opt/ntp-monitor-enterprise/app.wsgi
    
    <Directory /opt/ntp-monitor-enterprise>
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
    
    Alias /static /opt/ntp-monitor-enterprise/frontend/static
    <Directory /opt/ntp-monitor-enterprise/frontend/static>
        Require all granted
    </Directory>
    
    ErrorLog ${APACHE_LOG_DIR}/ntp-monitor_error.log
    CustomLog ${APACHE_LOG_DIR}/ntp-monitor_access.log combined
</VirtualHost>
EOF

# Activer le site et les modules
sudo a2ensite ntp-monitor
sudo a2enmod wsgi
sudo a2dissite 000-default
sudo systemctl reload apache2
```

### 8. Configurer le service systemd
```bash
# Créer le service systemd
sudo tee /etc/systemd/system/ntp-monitor.service << 'EOF'
[Unit]
Description=NTP Monitor Enterprise
After=network.target mysql.service redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/ntp-monitor-enterprise
Environment=PATH=/opt/ntp-monitor-venv/bin
ExecStart=/opt/ntp-monitor-venv/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Activer et démarrer le service
sudo systemctl daemon-reload
sudo systemctl enable ntp-monitor
sudo systemctl start ntp-monitor
```

## 🎯 Configuration Par Défaut

| Paramètre | Valeur |
|-----------|--------|
| **Interface web** | http://votre-serveur |
| **Port direct** | 5000 |
| **Répertoire** | /opt/ntp-monitor-enterprise |
| **Service** | ntp-monitor |
| **Base de données** | MySQL (ntp_monitor) |
| **Logs** | /var/log/ntp-monitor/ |

## 👤 Identifiants Par Défaut

| Utilisateur | Mot de passe | Rôle |
|-------------|--------------|------|
| admin | admin123 | Administrateur |
| operator | operator123 | Opérateur |
| viewer | viewer123 | Visualiseur |

⚠️ **Important** : Changez ces mots de passe après la première connexion !

## 🔄 Mise à Jour

### Mise à jour depuis GitHub
```bash
# Arrêter l'application
sudo systemctl stop ntp-monitor

# Sauvegarder la configuration
sudo cp /opt/ntp-monitor-enterprise/.env /tmp/ntp-monitor-backup.env

# Mettre à jour le code
cd /opt/ntp-monitor-enterprise
sudo git pull origin main

# Activer l'environnement virtuel
source /opt/ntp-monitor-venv/bin/activate

# Mettre à jour les dépendances
pip install --upgrade -r requirements.txt

# Restaurer la configuration
sudo cp /tmp/ntp-monitor-backup.env /opt/ntp-monitor-enterprise/.env

# Redémarrer l'application
sudo systemctl start ntp-monitor
```

## 📝 Commandes Utiles

### Statut et logs
```bash
# Statut des services
sudo systemctl status ntp-monitor apache2 mysql redis-server

# Logs en temps réel
sudo journalctl -u ntp-monitor -f

# Logs Apache
sudo tail -f /var/log/apache2/ntp-monitor_error.log

# Vérification de l'application
curl http://localhost/api/system/status
```

### Maintenance
```bash
# Redémarrage complet
sudo systemctl restart ntp-monitor apache2

# Sauvegarde base de données
sudo mysqldump -u ntp_user -p ntp_monitor > backup_$(date +%Y%m%d_%H%M%S).sql

# Nettoyage des logs
sudo find /var/log/ntp-monitor -name "*.log" -mtime +30 -delete
```

## 🛠️ Dépannage

### Service ne démarre pas
```bash
# Diagnostic détaillé
sudo systemctl status ntp-monitor --no-pager
sudo journalctl -u ntp-monitor --no-pager

# Vérifier les permissions
sudo chown -R www-data:www-data /opt/ntp-monitor-enterprise
sudo chmod +x /opt/ntp-monitor-enterprise/app.py
```

### Interface web inaccessible
```bash
# Vérifier Apache
sudo systemctl status apache2
sudo apache2ctl configtest

# Vérifier la configuration
sudo apache2ctl -S

# Redémarrer Apache
sudo systemctl restart apache2
```

### Problèmes de base de données
```bash
# Test de connexion MySQL
mysql -u ntp_user -p ntp_monitor -e "SELECT 1"

# Réinitialiser la base de données
sudo systemctl stop ntp-monitor
cd /opt/ntp-monitor-enterprise
source /opt/ntp-monitor-venv/bin/activate
python init_database.py
sudo systemctl start ntp-monitor
```

## 🔐 Sécurité Production

### SSL/HTTPS avec Let's Encrypt
```bash
# Installer certbot
sudo apt install certbot python3-certbot-apache

# Obtenir un certificat SSL
sudo certbot --apache -d votre-domaine.com

# Test de renouvellement automatique
sudo certbot renew --dry-run
```

### Durcissement sécuritaire
```bash
# Changer les mots de passe par défaut
# (via l'interface web après connexion)

# Désactiver les comptes inutiles
sudo usermod -L guest 2>/dev/null || true

# Configurer des seuils d'alertes stricts
# (via l'interface web admin)
```

## 📊 Monitoring

### Métriques surveillées
- **8 serveurs NTP** simultanés (3 mondiaux + 5 locaux)
- **Offset, delay, jitter** par serveur
- **Alertes automatiques** selon seuils configurés
- **Clients connectés** au serveur NTP local
- **Métriques système** (CPU, RAM, disque)

### Tableau de bord
- **Interface web** : http://votre-serveur
- **API REST** : http://votre-serveur/api/
- **WebSocket** : Mises à jour temps réel
- **Graphiques** : Historique avec zoom interactif

---

## 🎉 Vérification du Déploiement

Une fois le déploiement terminé, vérifiez que tout fonctionne :

```bash
# Services actifs
sudo systemctl is-active ntp-monitor apache2 mysql redis-server

# Interface web accessible
curl -s http://localhost | grep -q "NTP Monitor" && echo "✅ Interface OK" || echo "❌ Interface KO"

# API fonctionnelle
curl -s http://localhost/api/system/status | grep -q "status" && echo "✅ API OK" || echo "❌ API KO"

# Base de données
mysql -u ntp_user -p ntp_monitor -e "SELECT COUNT(*) FROM ntp_servers" 2>/dev/null && echo "✅ BDD OK" || echo "❌ BDD KO"
```

**🚀 Votre NTP Monitor Enterprise est maintenant déployé et opérationnel !**

Accédez à votre interface web et connectez-vous avec les identifiants par défaut pour commencer le monitoring NTP. 