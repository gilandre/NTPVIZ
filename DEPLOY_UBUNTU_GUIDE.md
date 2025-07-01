# 🚀 Guide de déploiement Ubuntu Production - NTP Monitor Enterprise

## 📋 Déploiement automatique depuis GitHub

### 🎯 Prérequis
- **Serveur Ubuntu 20.04/22.04 LTS**
- **Accès root/sudo**
- **Domaine configuré** (optionnel pour SSL)
- **Repository GitHub** avec les corrections appliquées

---

## ⚡ Déploiement automatique (Recommandé)

### 1. Télécharger et configurer le script
```bash
# Connexion serveur
ssh user@votre-serveur-ip

# Télécharger le script de déploiement
wget https://raw.githubusercontent.com/VOTRE_USERNAME/ntp-monitor-enterprise/main/deploy_ubuntu_production.sh

# Ou copier le script depuis votre repository local
scp deploy_ubuntu_production.sh user@serveur-ip:/tmp/

# Éditer la configuration
nano deploy_ubuntu_production.sh
```

**Modifiez ces variables :**
```bash
GITHUB_REPO="https://github.com/gilandre/NTPVIZ.git"
DOMAIN="192.168.10.45"  # ou votre IP/domaine
```

### 2. Exécuter le déploiement
```bash
# Rendre exécutable
chmod +x deploy_ubuntu_production.sh

# Lancer le déploiement (en root)
sudo ./deploy_ubuntu_production.sh
```

### 3. Résultat final
✅ **Application installée** sur http://votre-domaine.com  
✅ **Services configurés** (Apache, MySQL, Redis, NTP)  
✅ **SSL activé** (si domaine configuré)  
✅ **Monitoring automatique** actif  
✅ **Toutes les corrections** appliquées

---

## 🔧 Déploiement manuel (Si problème avec script)

### 1. Installation système
```bash
# Mise à jour
sudo apt update && sudo apt upgrade -y

# Dépendances essentielles
sudo apt install -y python3.11 python3.11-venv python3.11-dev \
    mysql-server apache2 libapache2-mod-wsgi-py3 \
    redis-server git curl ntp

# Configuration MySQL
sudo mysql_secure_installation
sudo mysql -u root -p
```

```sql
CREATE DATABASE ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ntp_user'@'localhost' IDENTIFIED BY 'MOT_DE_PASSE_FORT';
GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 2. Utilisateur et application
```bash
# Créer utilisateur
sudo useradd -m -s /bin/bash ntp-monitor
sudo usermod -aG www-data ntp-monitor

# Changer vers utilisateur app
sudo -u ntp-monitor -i

# Clone depuis GitHub
git clone https://github.com/gilandre/NTPVIZ.git
cd NTPVIZ

# Environnement Python
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Répertoires
mkdir -p logs instance backups
```

### 3. Configuration
```bash
# Fichier .env
cp .env.example .env
nano .env
```

**Configuration .env :**
```env
FLASK_ENV=production
SECRET_KEY=clé-secrète-très-longue
DEBUG=false
DATABASE_URL=mysql+pymysql://ntp_user:MOT_DE_PASSE@localhost/ntp_monitor
DEFAULT_NTP_SERVERS=pool.ntp.org,time.google.com,time.cloudflare.com
LOCAL_NTP_SERVERS=192.168.1.100,10.0.0.50
ALERT_OFFSET_THRESHOLD=100
ALERT_DELAY_THRESHOLD=500
```

### 4. Base de données
```bash
# Initialiser
source venv/bin/activate
python init_database.py
```

### 5. Apache Virtual Host
```bash
# Configuration Apache
sudo nano /etc/apache2/sites-available/ntp-monitor.conf
```

```apache
<VirtualHost *:80>
    ServerName votre-domaine.com
    DocumentRoot /home/ntp-monitor/ntp-monitor-enterprise
    
    WSGIDaemonProcess ntp-monitor python-home=/home/ntp-monitor/ntp-monitor-enterprise/venv python-path=/home/ntp-monitor/ntp-monitor-enterprise
    WSGIProcessGroup ntp-monitor
    WSGIScriptAlias / /home/ntp-monitor/ntp-monitor-enterprise/app.wsgi
    
    <Directory /home/ntp-monitor/ntp-monitor-enterprise>
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
    
    Alias /static /home/ntp-monitor/ntp-monitor-enterprise/frontend/static
    <Directory /home/ntp-monitor/ntp-monitor-enterprise/frontend/static>
        Require all granted
    </Directory>
</VirtualHost>
```

### 6. Fichier WSGI
```bash
# Créer app.wsgi
nano /home/ntp-monitor/ntp-monitor-enterprise/app.wsgi
```

```python
#!/usr/bin/env python3
import sys, os
from pathlib import Path

app_path = Path('/home/ntp-monitor/ntp-monitor-enterprise')
sys.path.insert(0, str(app_path))
os.chdir(str(app_path))

from dotenv import load_dotenv
load_dotenv(str(app_path / '.env'))

from app import app as application
```

### 7. Activation
```bash
# Activer site Apache
sudo a2dissite 000-default
sudo a2ensite ntp-monitor
sudo systemctl reload apache2

# Service systemd
sudo nano /etc/systemd/system/ntp-monitor.service
```

```ini
[Unit]
Description=NTP Monitor Enterprise
After=network.target mysql.service

[Service]
Type=simple
User=ntp-monitor
WorkingDirectory=/home/ntp-monitor/ntp-monitor-enterprise
ExecStart=/home/ntp-monitor/ntp-monitor-enterprise/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Démarrer services
sudo systemctl daemon-reload
sudo systemctl enable ntp-monitor
sudo systemctl start ntp-monitor
```

---

## 🔒 Sécurisation

### SSL avec Let's Encrypt
```bash
# Installation Certbot
sudo apt install -y certbot python3-certbot-apache

# Certificat SSL
sudo certbot --apache -d votre-domaine.com

# Vérifier renouvellement
sudo certbot renew --dry-run
```

### Pare-feu
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Permissions
```bash
sudo chown -R ntp-monitor:www-data /home/ntp-monitor/ntp-monitor-enterprise
sudo chmod -R 755 /home/ntp-monitor/ntp-monitor-enterprise
sudo chmod 600 /home/ntp-monitor/ntp-monitor-enterprise/.env
```

---

## 🔄 Mise à jour depuis GitHub

### Script de mise à jour
```bash
# Créer script de mise à jour
nano /home/ntp-monitor/update.sh
```

```bash
#!/bin/bash
cd /home/ntp-monitor/ntp-monitor-enterprise

# Backup
tar -czf ../backup-$(date +%Y%m%d).tar.gz --exclude=venv .

# Mise à jour
git pull origin main

# Dépendances
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Redémarrage
sudo systemctl restart ntp-monitor
sudo systemctl reload apache2

echo "✅ Mise à jour terminée"
```

```bash
# Rendre exécutable
chmod +x /home/ntp-monitor/update.sh

# Automatisation (optionnel)
crontab -e
# Ajouter: 0 3 * * * /home/ntp-monitor/update.sh >> /home/ntp-monitor/logs/update.log 2>&1
```

---

## 📊 Monitoring et maintenance

### Vérification statut
```bash
# Services
sudo systemctl status ntp-monitor
sudo systemctl status apache2
sudo systemctl status mysql

# Logs application
tail -f /home/ntp-monitor/ntp-monitor-enterprise/logs/app.log

# Logs Apache
sudo tail -f /var/log/apache2/ntp-monitor_error.log

# Logs système
sudo journalctl -u ntp-monitor -f
```

### Tests fonctionnels
```bash
# Accès local
curl -I http://localhost

# Test API
curl http://localhost/api/ntp/status

# Test corrections Chart.js
curl -s http://localhost/static/js/dashboard.js | grep "type: 'category'"
```

---

## 🧪 Validation déploiement

### Checklist final
- [ ] ✅ **Application accessible** : http://votre-domaine.com
- [ ] ✅ **Connexion admin** : admin / admin123
- [ ] ✅ **Graphiques sans erreur** Chart.js
- [ ] ✅ **Caractères français** corrects
- [ ] ✅ **Services actifs** : ntp-monitor, apache2, mysql
- [ ] ✅ **SSL configuré** (si domaine)
- [ ] ✅ **Monitoring automatique** actif

### URLs importantes
- **Application** : https://votre-domaine.com
- **API Status** : https://votre-domaine.com/api/ntp/status
- **Login** : admin / admin123 (⚠️ à changer)

---

## 🔧 Résolution problèmes

### Service ne démarre pas
```bash
sudo journalctl -u ntp-monitor -n 50
cd /home/ntp-monitor/ntp-monitor-enterprise
source venv/bin/activate
python app.py  # Test manuel
```

### Erreur base de données
```bash
python -c "
from backend.app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
"
```

### Erreur permissions
```bash
sudo chown -R ntp-monitor:www-data /home/ntp-monitor/ntp-monitor-enterprise
sudo chmod -R 755 /home/ntp-monitor/ntp-monitor-enterprise
```

---

## 🎉 Résultat final

Votre **NTP Monitor Enterprise v2.0.0** est maintenant déployé avec :

✅ **Toutes les corrections appliquées**  
✅ **Configuration production sécurisée**  
✅ **SSL et monitoring automatique**  
✅ **Synchronisation GitHub**  
✅ **Performance optimisée**  

**Accès : https://votre-domaine.com - admin/admin123**

---

*Guide de déploiement Ubuntu - NTP Monitor Enterprise v2.0.0* 