# 🚀 Guide de Déploiement Production - NTP Monitor Enterprise v2.1.0

Guide complet pour déployer NTP Monitor Enterprise en production sur Ubuntu 24.04 avec tous les prérequis et optimisations.

## 📋 Table des Matières

1. [Prérequis Système](#prérequis-système)
2. [Installation One-Click](#installation-one-click)
3. [Installation Manuelle](#installation-manuelle)
4. [Configuration Production](#configuration-production)
5. [Déploiement GitHub](#déploiement-github)
6. [Monitoring et Maintenance](#monitoring-et-maintenance)
7. [Sécurité](#sécurité)
8. [Dépannage](#dépannage)

---

## 📋 Prérequis Système

### Configuration Minimale
- **OS** : Ubuntu 24.04 LTS (compatible 22.04/20.04)
- **RAM** : 2GB minimum, 4GB recommandé
- **Disque** : 10GB libre minimum
- **CPU** : 2 cores minimum
- **Réseau** : Connexion Internet stable

### Ports Requis
- **22** : SSH
- **80** : HTTP
- **443** : HTTPS
- **5000** : Application (développement)
- **123** : NTP (UDP)
- **3306** : MySQL (local)
- **6379** : Redis (local)

---

## 🚀 Installation One-Click

### Méthode Recommandée
```bash
# Installation complète en une seule commande
curl -fsSL https://raw.githubusercontent.com/votre-username/ntp-monitor-enterprise/main/scripts/quick_install.sh | sudo bash
```

### Vérification Post-Installation
```bash
# Vérifier que tous les services sont actifs
sudo systemctl status ntp-monitor apache2 mysql redis-server

# Test de l'interface web
curl -s http://localhost | grep -q "NTP Monitor" && echo "✅ OK" || echo "❌ KO"
```

---

## 🔧 Installation Manuelle

### Étape 1 : Préparation du Système
```bash
# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installation des packages essentiels
sudo apt install -y \
    python3 python3-pip python3-venv python3-dev \
    mysql-server mysql-client libmysqlclient-dev \
    apache2 libapache2-mod-wsgi-py3 apache2-utils \
    redis-server \
    ntpsec ntpdate ntpstat \
    curl wget git htop vim tree net-tools unzip \
    build-essential pkg-config \
    ufw fail2ban \
    certbot python3-certbot-apache
```

### Étape 2 : Configuration Sécurisée
```bash
# Configuration du pare-feu
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 123/udp
sudo ufw --force enable

# Configuration fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Étape 3 : Base de Données MySQL
```bash
# Sécurisation MySQL
sudo mysql_secure_installation

# Création base de données et utilisateur
sudo mysql << 'EOF'
CREATE DATABASE ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ntp_user'@'localhost' IDENTIFIED BY 'MOT_DE_PASSE_FORT';
GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_user'@'localhost';
FLUSH PRIVILEGES;
EOF
```

### Étape 4 : Installation Application
```bash
# Création utilisateur dédié
sudo useradd -m -s /bin/bash ntp-monitor
sudo mkdir -p /opt/ntp-monitor-enterprise
sudo chown ntp-monitor:ntp-monitor /opt/ntp-monitor-enterprise

# Cloner l'application
sudo -u ntp-monitor git clone https://github.com/votre-username/ntp-monitor-enterprise.git /opt/ntp-monitor-enterprise

# Environnement virtuel Python
sudo -u ntp-monitor python3 -m venv /opt/ntp-monitor-venv
sudo -u ntp-monitor /opt/ntp-monitor-venv/bin/pip install --upgrade pip setuptools wheel

# Installation des dépendances
cd /opt/ntp-monitor-enterprise
sudo -u ntp-monitor /opt/ntp-monitor-venv/bin/pip install -r requirements.txt
```

### Étape 5 : Configuration Application
```bash
# Configuration .env
sudo -u ntp-monitor cp .env.example .env
sudo -u ntp-monitor nano .env
```

**Configuration Production (.env) :**
```env
# === CONFIGURATION PRODUCTION ===
FLASK_ENV=production
DEBUG=false
SECRET_KEY=CHANGEZ_CETTE_CLE_SECRETE_TRES_LONGUE_ET_UNIQUE
HOST=0.0.0.0
PORT=5000

# === BASE DE DONNÉES ===
DATABASE_URL=mysql+pymysql://ntp_user:MOT_DE_PASSE_FORT@localhost/ntp_monitor

# === CONFIGURATION NTP ===
DEFAULT_NTP_SERVERS=pool.ntp.org,time.google.com,time.cloudflare.com
LOCAL_NTP_SERVERS=192.168.1.100,10.0.0.50

# === ALERTES ===
ALERT_OFFSET_THRESHOLD=100
ALERT_DELAY_THRESHOLD=500
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP=smtp.gmail.com
ALERT_EMAIL_PORT=587
ALERT_EMAIL_USERNAME=ntp-monitor@votre-domaine.com
ALERT_EMAIL_PASSWORD=MOT_DE_PASSE_EMAIL

# === CACHE REDIS ===
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300

# === LOGS ===
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_FILE=/var/log/ntp-monitor/app.log
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5
LOG_ROTATION=daily

# === SÉCURITÉ ===
SESSION_PERMANENT=false
PERMANENT_SESSION_LIFETIME=3600
WTF_CSRF_ENABLED=true
BCRYPT_LOG_ROUNDS=12

# === MONITORING ===
MONITORING_INTERVAL=30
MAX_LOG_RETENTION_DAYS=30
AUTO_CLEANUP_ENABLED=true
ENABLE_METRICS=true
```

### Étape 6 : Initialisation Base de Données
```bash
# Initialisation avec données par défaut
cd /opt/ntp-monitor-enterprise
sudo -u ntp-monitor /opt/ntp-monitor-venv/bin/python init_database.py

# Vérification des tables
mysql -u ntp_user -p ntp_monitor -e "SHOW TABLES;"
```

### Étape 7 : Configuration Apache
```bash
# Configuration Apache
sudo tee /etc/apache2/sites-available/ntp-monitor.conf << 'EOF'
<VirtualHost *:80>
    ServerName votre-domaine.com
    ServerAlias www.votre-domaine.com
    
    DocumentRoot /opt/ntp-monitor-enterprise/frontend/static
    
    WSGIDaemonProcess ntp-monitor \
        python-home=/opt/ntp-monitor-venv \
        python-path=/opt/ntp-monitor-enterprise \
        user=ntp-monitor \
        group=ntp-monitor \
        processes=2 \
        threads=5 \
        maximum-requests=1000
    
    WSGIProcessGroup ntp-monitor
    WSGIScriptAlias / /opt/ntp-monitor-enterprise/app.wsgi
    
    <Directory /opt/ntp-monitor-enterprise>
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
    
    Alias /static /opt/ntp-monitor-enterprise/frontend/static
    <Directory /opt/ntp-monitor-enterprise/frontend/static>
        Require all granted
        ExpiresActive On
        ExpiresDefault "access plus 1 month"
    </Directory>
    
    # Logs
    ErrorLog ${APACHE_LOG_DIR}/ntp-monitor_error.log
    CustomLog ${APACHE_LOG_DIR}/ntp-monitor_access.log combined
    LogLevel info
    
    # Sécurité
    ServerTokens Prod
    ServerSignature Off
    
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
</VirtualHost>
EOF

# Activation du site
sudo a2ensite ntp-monitor
sudo a2enmod wsgi headers expires
sudo a2dissite 000-default
sudo systemctl reload apache2
```

### Étape 8 : Service Systemd
```bash
# Configuration service systemd
sudo tee /etc/systemd/system/ntp-monitor.service << 'EOF'
[Unit]
Description=NTP Monitor Enterprise Service
After=network.target mysql.service redis.service apache2.service
Wants=mysql.service redis.service
Requires=network.target

[Service]
Type=simple
User=ntp-monitor
Group=ntp-monitor
WorkingDirectory=/opt/ntp-monitor-enterprise
Environment=PATH=/opt/ntp-monitor-venv/bin
ExecStart=/opt/ntp-monitor-venv/bin/python app.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3

# Logs
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ntp-monitor

# Sécurité
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/ntp-monitor-enterprise/logs /opt/ntp-monitor-enterprise/instance

[Install]
WantedBy=multi-user.target
EOF

# Activation et démarrage
sudo systemctl daemon-reload
sudo systemctl enable ntp-monitor
sudo systemctl start ntp-monitor
```

### Étape 9 : Configuration Logs
```bash
# Création répertoire logs
sudo mkdir -p /var/log/ntp-monitor
sudo chown ntp-monitor:ntp-monitor /var/log/ntp-monitor

# Configuration logrotate
sudo tee /etc/logrotate.d/ntp-monitor << 'EOF'
/var/log/ntp-monitor/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 ntp-monitor ntp-monitor
    postrotate
        systemctl reload ntp-monitor
    endscript
}
EOF
```

---

## 🔐 Configuration Production

### Variables d'Environnement Critiques
```bash
# Génération d'une clé secrète forte
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Configuration Redis sécurisée
sudo nano /etc/redis/redis.conf
# Décommenter et configurer :
# requirepass MOT_DE_PASSE_REDIS_FORT
# bind 127.0.0.1
```

### Optimisations MySQL
```bash
# Configuration MySQL optimisée
sudo tee -a /etc/mysql/mysql.conf.d/ntp-monitor.cnf << 'EOF'
[mysqld]
# Optimisations NTP Monitor
innodb_buffer_pool_size=512M
query_cache_size=64M
query_cache_limit=2M
max_connections=100
thread_cache_size=8
table_open_cache=1000

# Encodage UTF-8
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
EOF

sudo systemctl restart mysql
```

---

## 📊 Déploiement GitHub

### Structure Repository
```
ntp-monitor-enterprise/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── app.py
├── app.wsgi
├── init_database.py
├── backend/
├── frontend/
├── config/
├── scripts/
│   ├── quick_install.sh
│   ├── check_prerequisites.sh
│   └── backup.sh
├── deployment/
│   ├── apache/
│   ├── systemd/
│   └── nginx/
└── docs/
```

### Workflow GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy NTP Monitor Enterprise

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-flask
    
    - name: Run tests
      run: |
        pytest tests/ -v
    
    - name: Security scan
      run: |
        pip install bandit safety
        bandit -r backend/
        safety check -r requirements.txt
```

---

## 📊 Monitoring et Maintenance

### Surveillance Automatique
```bash
# Script de monitoring
sudo tee /usr/local/bin/ntp-monitor-check.sh << 'EOF'
#!/bin/bash
# Vérification santé NTP Monitor Enterprise

LOG_FILE="/var/log/ntp-monitor/health-check.log"
EMAIL="admin@votre-domaine.com"

check_service() {
    if ! systemctl is-active --quiet "$1"; then
        echo "$(date): Service $1 inactif" >> "$LOG_FILE"
        systemctl restart "$1"
        echo "Service $1 redémarré" | mail -s "Service $1 redémarré" "$EMAIL"
    fi
}

check_service "ntp-monitor"
check_service "apache2"
check_service "mysql"
check_service "redis-server"

# Vérification interface web
if ! curl -s http://localhost | grep -q "NTP Monitor"; then
    echo "$(date): Interface web inaccessible" >> "$LOG_FILE"
    systemctl restart apache2
fi
EOF

chmod +x /usr/local/bin/ntp-monitor-check.sh

# Cron job surveillance
echo "*/5 * * * * /usr/local/bin/ntp-monitor-check.sh" | sudo crontab -
```

### Sauvegarde Automatique
```bash
# Script de sauvegarde
sudo tee /usr/local/bin/ntp-monitor-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/ntp-monitor"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Sauvegarde base de données
mysqldump -u ntp_user -p ntp_monitor > "$BACKUP_DIR/ntp_monitor_$DATE.sql"

# Sauvegarde configuration
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    /opt/ntp-monitor-enterprise/.env \
    /etc/apache2/sites-available/ntp-monitor.conf \
    /etc/systemd/system/ntp-monitor.service

# Nettoyage anciennes sauvegardes (> 30 jours)
find "$BACKUP_DIR" -name "*.sql" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
EOF

chmod +x /usr/local/bin/ntp-monitor-backup.sh

# Sauvegarde quotidienne
echo "0 2 * * * /usr/local/bin/ntp-monitor-backup.sh" | sudo crontab -
```

---

## 🛡️ Sécurité

### SSL/HTTPS avec Let's Encrypt
```bash
# Installation certificat SSL
sudo certbot --apache -d votre-domaine.com -d www.votre-domaine.com

# Configuration auto-renouvellement
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Test renouvellement
sudo certbot renew --dry-run
```

### Durcissement Sécuritaire
```bash
# Désactiver versions PHP inutiles
sudo a2dismod php7.4 php8.0 php8.1 2>/dev/null || true

# Configuration SSH sécurisée
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Mise à jour automatique sécurité
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 🛠️ Dépannage

### Diagnostic Complet
```bash
# Script de diagnostic
sudo tee /usr/local/bin/ntp-monitor-diag.sh << 'EOF'
#!/bin/bash
echo "=== DIAGNOSTIC NTP MONITOR ENTERPRISE ==="
echo "Date: $(date)"
echo

echo "=== SERVICES ==="
systemctl status ntp-monitor --no-pager
systemctl status apache2 --no-pager
systemctl status mysql --no-pager
systemctl status redis-server --no-pager

echo -e "\n=== PROCESSUS ==="
ps aux | grep -E "(python|apache|mysql|redis)" | grep -v grep

echo -e "\n=== PORTS ==="
netstat -tlnp | grep -E "(5000|80|443|3306|6379)"

echo -e "\n=== LOGS RÉCENTS ==="
journalctl -u ntp-monitor --since "10 minutes ago" --no-pager

echo -e "\n=== ESPACE DISQUE ==="
df -h

echo -e "\n=== MÉMOIRE ==="
free -h

echo -e "\n=== TEST CONNEXION WEB ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost
curl -s -o /dev/null -w "%{http_code}" http://localhost/api/system/status
EOF

chmod +x /usr/local/bin/ntp-monitor-diag.sh
```

### Problèmes Courants

#### Service ne démarre pas
```bash
# Vérifier logs
sudo journalctl -u ntp-monitor -f

# Vérifier permissions
sudo chown -R ntp-monitor:ntp-monitor /opt/ntp-monitor-enterprise

# Vérifier environnement virtuel
sudo -u ntp-monitor /opt/ntp-monitor-venv/bin/python -c "import flask; print('Flask OK')"
```

#### Interface web inaccessible
```bash
# Vérifier configuration Apache
sudo apache2ctl configtest

# Vérifier logs Apache
sudo tail -f /var/log/apache2/ntp-monitor_error.log

# Redémarrer Apache
sudo systemctl restart apache2
```

#### Erreurs base de données
```bash
# Test connexion MySQL
mysql -u ntp_user -p ntp_monitor -e "SELECT VERSION();"

# Réinitialiser base de données
sudo systemctl stop ntp-monitor
cd /opt/ntp-monitor-enterprise
sudo -u ntp-monitor /opt/ntp-monitor-venv/bin/python init_database.py
sudo systemctl start ntp-monitor
```

---

## 🎯 Checklist Déploiement

### Pré-déploiement
- [ ] Serveur Ubuntu 24.04 prêt
- [ ] Accès SSH configuré
- [ ] Nom de domaine configuré (DNS)
- [ ] Certificats SSL prêts (optionnel)

### Installation
- [ ] Packages système installés
- [ ] MySQL configuré et sécurisé
- [ ] Application déployée
- [ ] Configuration .env complétée
- [ ] Base de données initialisée
- [ ] Apache configuré
- [ ] Service systemd configuré

### Post-déploiement
- [ ] Tous les services actifs
- [ ] Interface web accessible
- [ ] API fonctionnelle
- [ ] Monitoring configuré
- [ ] Sauvegardes configurées
- [ ] SSL activé (production)
- [ ] Mots de passe par défaut changés

### Tests
- [ ] Connexion admin réussie
- [ ] Monitoring NTP fonctionnel
- [ ] Alertes opérationnelles
- [ ] WebSocket temps réel
- [ ] Graphiques sans erreurs
- [ ] API endpoints testés

---

**🚀 Déploiement terminé ! Votre NTP Monitor Enterprise est opérationnel en production.**

Pour toute assistance : 
- 📧 Email : support@votre-domaine.com
- 🐛 Issues : https://github.com/votre-username/ntp-monitor-enterprise/issues
- 📚 Documentation : https://docs.votre-domaine.com 