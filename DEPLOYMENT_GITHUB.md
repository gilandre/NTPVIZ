# 🚀 Guide de Déploiement GitHub - NTP Monitor Enterprise v2.1.0

**Guide complet pour débutants - Premier déploiement sur Ubuntu 24.04**

Ce guide vous accompagne pas à pas pour déployer NTP Monitor Enterprise depuis GitHub sur un serveur Ubuntu 24.04, même si vous n'avez jamais fait de déploiement auparavant.

---

## 📋 Avant de Commencer

### 🎯 Ce que vous aurez à la fin
- Une interface web de monitoring NTP accessible via votre navigateur
- Surveillance automatique de 8 serveurs NTP
- Alertes en temps réel
- Graphiques interactifs
- Système sécurisé avec utilisateurs et rôles

### 📋 Prérequis
- **Serveur Ubuntu 24.04** avec accès SSH
- **Accès root/sudo** sur le serveur
- **10GB d'espace disque** libre minimum
- **2GB de RAM** minimum (4GB recommandé)
- **Connexion Internet** stable

### 🕐 Temps d'installation
- **Installation automatique** : 10-15 minutes
- **Installation manuelle** : 30-45 minutes

---

## 🚀 Méthode 1 : Installation Automatique (Recommandée pour Débutants)

### Étape 1 : Connexion au Serveur
```bash
# Remplacez "votre-serveur" par l'IP ou le nom de votre serveur
ssh root@votre-serveur

# Ou si vous avez un utilisateur sudo :
ssh votre-utilisateur@votre-serveur
```

### Étape 2 : Installation Automatique
```bash
# Copier-coller cette commande en une seule fois
curl -fsSL https://raw.githubusercontent.com/votre-username/ntp-monitor-enterprise/main/scripts/install_auto.sh | sudo bash
```

**⏳ L'installation va prendre 10-15 minutes.**

### Étape 3 : Vérification
```bash
# Vérifier que tous les services sont actifs
sudo systemctl status ntp-monitor apache2 mysql redis-server

# Tester l'interface web
curl -s http://localhost | grep -q "NTP Monitor" && echo "✅ Installation réussie !" || echo "❌ Problème détecté"
```

### Étape 4 : Accès
**Interface web** : `http://votre-serveur`  
**Identifiants par défaut** :
- **Utilisateur** : `admin`
- **Mot de passe** : `admin123`

⚠️ **Important** : Changez le mot de passe après la première connexion !

---

## 🔧 Méthode 2 : Installation Manuelle (Étape par Étape)

### Étape 1 : Préparation du Serveur

#### 1.1 Mise à jour du système
```bash
# Mise à jour des packages
sudo apt update && sudo apt upgrade -y

# Redémarrer si nécessaire
sudo reboot
```

#### 1.2 Installation des prérequis
```bash
# Installation des outils essentiels
sudo apt install -y \
    curl wget git vim nano htop tree \
    build-essential pkg-config \
    python3 python3-pip python3-venv python3-dev \
    mysql-server mysql-client libmysqlclient-dev \
    apache2 libapache2-mod-wsgi-py3 apache2-utils \
    redis-server \
    ntpsec ntpdate ntpstat \
    ufw fail2ban \
    certbot python3-certbot-apache

# Vérifier que tout est installé
echo "✅ Installation terminée"
```

### Étape 2 : Configuration Sécurisée

#### 2.1 Pare-feu
```bash
# Configuration firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw allow 123/udp    # NTP
sudo ufw --force enable

# Vérifier
sudo ufw status
```

#### 2.2 Fail2ban
```bash
# Activer fail2ban pour la sécurité
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Étape 3 : Configuration MySQL

#### 3.1 Sécurisation
```bash
# Sécuriser MySQL
sudo mysql_secure_installation

# Répondre aux questions :
# - Remove anonymous users? Y
# - Disallow root login remotely? Y
# - Remove test database? Y
# - Reload privilege tables? Y
```

#### 3.2 Création base de données
```bash
# Créer la base de données
sudo mysql -e "
CREATE DATABASE ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ntp_user'@'localhost' IDENTIFIED BY 'VotreMotDePasseSecurise123!';
GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_user'@'localhost';
FLUSH PRIVILEGES;"

# Vérifier
sudo mysql -e "SHOW DATABASES;" | grep ntp_monitor
```

### Étape 4 : Installation de l'Application

#### 4.1 Création utilisateur dédié
```bash
# Créer un utilisateur système pour l'application
sudo useradd -m -s /bin/bash ntp-monitor
sudo mkdir -p /opt/ntp-monitor-enterprise
sudo chown ntp-monitor:ntp-monitor /opt/ntp-monitor-enterprise
```

#### 4.2 Cloner l'application
```bash
# Cloner depuis GitHub
sudo -u ntp-monitor git clone https://github.com/votre-username/ntp-monitor-enterprise.git /opt/ntp-monitor-enterprise

# Vérifier le téléchargement
ls -la /opt/ntp-monitor-enterprise/
```

#### 4.3 Environnement virtuel Python
```bash
# Créer l'environnement virtuel
sudo -u ntp-monitor python3 -m venv /opt/ntp-monitor-venv

# Activer et installer les dépendances
sudo -u ntp-monitor /opt/ntp-monitor-venv/bin/pip install --upgrade pip setuptools wheel

# Installer les dépendances de l'application
cd /opt/ntp-monitor-enterprise
sudo -u ntp-monitor /opt/ntp-monitor-venv/bin/pip install -r requirements.txt

# Vérifier l'installation
sudo -u ntp-monitor /opt/ntp-monitor-venv/bin/python -c "import flask; print('✅ Flask OK')"
```

### Étape 5 : Configuration de l'Application

#### 5.1 Fichier de configuration
```bash
# Copier le fichier de configuration exemple
sudo -u ntp-monitor cp /opt/ntp-monitor-enterprise/.env.example /opt/ntp-monitor-enterprise/.env

# Éditer la configuration
sudo -u ntp-monitor nano /opt/ntp-monitor-enterprise/.env
```

#### 5.2 Configuration .env (À adapter)
```env
# === CONFIGURATION PRODUCTION ===
FLASK_ENV=production
DEBUG=false
SECRET_KEY=CHANGEZ_CETTE_CLE_TRES_LONGUE_ET_UNIQUE_123456789
HOST=0.0.0.0
PORT=5000

# === BASE DE DONNÉES ===
DATABASE_URL=mysql+pymysql://ntp_user:VotreMotDePasseSecurise123!@localhost/ntp_monitor

# === SERVEURS NTP ===
DEFAULT_NTP_SERVERS=pool.ntp.org,time.google.com,time.cloudflare.com
LOCAL_NTP_SERVERS=192.168.1.1,10.0.0.1

# === ALERTES ===
ALERT_OFFSET_THRESHOLD=100
ALERT_DELAY_THRESHOLD=500

# === REDIS ===
REDIS_URL=redis://localhost:6379/0

# === LOGS ===
LOG_LEVEL=INFO
LOG_TO_FILE=true
```

**💡 Conseil** : Générez une clé secrète forte :
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Étape 6 : Initialisation Base de Données

```bash
# Initialiser la base de données avec les données par défaut
cd /opt/ntp-monitor-enterprise
sudo -u ntp-monitor /opt/ntp-monitor-venv/bin/python init_database.py

# Vérifier que les tables sont créées
mysql -u ntp_user -p ntp_monitor -e "SHOW TABLES;"
```

### Étape 7 : Configuration Apache

#### 7.1 Création du fichier de configuration
```bash
# Créer la configuration Apache
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
        threads=5
    
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
```

#### 7.2 Création du fichier WSGI
```bash
# Créer le fichier WSGI
sudo -u ntp-monitor tee /opt/ntp-monitor-enterprise/app.wsgi << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Ajouter le chemin de l'application
sys.path.insert(0, '/opt/ntp-monitor-enterprise')

# Activer l'environnement virtuel
activate_this = '/opt/ntp-monitor-venv/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})

# Importer l'application
from app import app as application

if __name__ == "__main__":
    application.run()
EOF
```

#### 7.3 Activation du site
```bash
# Activer le site et les modules
sudo a2ensite ntp-monitor
sudo a2enmod wsgi
sudo a2dissite 000-default
sudo systemctl reload apache2

# Vérifier la configuration
sudo apache2ctl configtest
```

### Étape 8 : Service Systemd

#### 8.1 Création du service
```bash
# Créer le service systemd
sudo tee /etc/systemd/system/ntp-monitor.service << 'EOF'
[Unit]
Description=NTP Monitor Enterprise
After=network.target mysql.service redis.service

[Service]
Type=simple
User=ntp-monitor
Group=ntp-monitor
WorkingDirectory=/opt/ntp-monitor-enterprise
Environment=PATH=/opt/ntp-monitor-venv/bin
ExecStart=/opt/ntp-monitor-venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### 8.2 Activation et démarrage
```bash
# Activer et démarrer le service
sudo systemctl daemon-reload
sudo systemctl enable ntp-monitor
sudo systemctl start ntp-monitor

# Vérifier le statut
sudo systemctl status ntp-monitor
```

---

## 🎯 Vérification Finale

### Tests Automatiques
```bash
# Script de vérification complète
cat << 'EOF' > /tmp/verify_installation.sh
#!/bin/bash
echo "=== VÉRIFICATION NTP MONITOR ENTERPRISE ==="
echo

# Services
echo "Services:"
for service in ntp-monitor apache2 mysql redis-server ntpsec; do
    if systemctl is-active --quiet $service; then
        echo "  ✅ $service actif"
    else
        echo "  ❌ $service inactif"
    fi
done

# Ports
echo -e "\nPorts:"
netstat -tlnp | grep -E "(80|443|5000|3306|6379|123)" | while read line; do
    echo "  ✅ $line"
done

# Interface web
echo -e "\nInterface web:"
if curl -s http://localhost | grep -q "NTP Monitor"; then
    echo "  ✅ Interface accessible"
else
    echo "  ❌ Interface non accessible"
fi

# API
echo -e "\nAPI:"
if curl -s http://localhost/api/system/status | grep -q "status"; then
    echo "  ✅ API fonctionnelle"
else
    echo "  ❌ API non fonctionnelle"
fi

# Base de données
echo -e "\nBase de données:"
if mysql -u ntp_user -p ntp_monitor -e "SELECT 1" 2>/dev/null; then
    echo "  ✅ Base de données accessible"
else
    echo "  ❌ Base de données non accessible"
fi

echo -e "\n=== RÉSUMÉ ==="
echo "Interface web: http://$(hostname -I | awk '{print $1}')"
echo "Identifiants: admin / admin123"
echo "Changez le mot de passe après la première connexion !"
EOF

chmod +x /tmp/verify_installation.sh
/tmp/verify_installation.sh
```

### Accès Final
1. **Interface web** : `http://votre-serveur`
2. **Identifiants** : `admin` / `admin123`
3. **Changez le mot de passe** immédiatement après connexion

---

## 🛠️ Dépannage pour Débutants

### Problème : Interface non accessible

#### Vérification Apache
```bash
# Vérifier Apache
sudo systemctl status apache2

# Vérifier les logs d'erreur
sudo tail -f /var/log/apache2/ntp-monitor_error.log
```

#### Vérification Firewall
```bash
# Vérifier le pare-feu
sudo ufw status

# Autoriser le port 80 si nécessaire
sudo ufw allow 80/tcp
```

### Problème : Service ne démarre pas

#### Vérification du service
```bash
# Vérifier le statut
sudo systemctl status ntp-monitor

# Voir les logs
sudo journalctl -u ntp-monitor -f
```

#### Vérification des permissions
```bash
# Réparer les permissions
sudo chown -R ntp-monitor:ntp-monitor /opt/ntp-monitor-enterprise
sudo chmod +x /opt/ntp-monitor-enterprise/app.py
```

### Problème : Base de données

#### Test de connexion
```bash
# Tester la connexion MySQL
mysql -u ntp_user -p ntp_monitor -e "SELECT VERSION();"
```

#### Réinitialisation
```bash
# Réinitialiser la base de données
sudo systemctl stop ntp-monitor
cd /opt/ntp-monitor-enterprise
sudo -u ntp-monitor /opt/ntp-monitor-venv/bin/python init_database.py
sudo systemctl start ntp-monitor
```

---

## 📞 Support et Aide

### En cas de problème
1. **Vérifiez les logs** : `sudo journalctl -u ntp-monitor -f`
2. **Relancez la vérification** : `/tmp/verify_installation.sh`
3. **Consultez la documentation** : [Guide complet](GUIDE_DEPLOIEMENT_PRODUCTION.md)

### Support
- **Issues GitHub** : [Créer un ticket](https://github.com/votre-username/ntp-monitor-enterprise/issues)
- **Documentation** : Guides dans le dossier `docs/`
- **Logs** : `/var/log/apache2/ntp-monitor_*.log`

---

## 🎉 Félicitations !

Vous avez successfully déployé **NTP Monitor Enterprise** !

### Prochaines étapes
1. **Connectez-vous** à l'interface web
2. **Changez le mot de passe** administrateur
3. **Configurez vos serveurs NTP** locaux
4. **Testez les alertes** en ajustant les seuils
5. **Configurez SSL** pour sécuriser les connexions

### Maintenance
- **Sauvegardes** : Configurez des sauvegardes automatiques
- **Mises à jour** : Vérifiez régulièrement les mises à jour
- **Monitoring** : Surveillez les logs et performances

**🚀 Votre système de monitoring NTP est maintenant opérationnel !** 