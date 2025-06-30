# 🚀 Guide de Déploiement - NTP Monitor Enterprise

## 📋 Guide Complet de Déploiement sur Serveur Distant

---

## ⚡ Déploiement Rapide (1-Click)

### 🔗 Commande Complète

```bash
# Clone et déploiement automatique
wget -O - https://raw.githubusercontent.com/[YOUR_REPO]/dev/deployment/scripts/deploy.sh | sudo bash
```

---

## 🛠️ Déploiement Manuel Étape par Étape

### 📋 Prérequis Serveur

- **OS** : Ubuntu 24.04 LTS (recommandé) ou Ubuntu 22.04/20.04
- **RAM** : Minimum 2GB, recommandé 4GB+
- **Stockage** : Minimum 10GB, recommandé 20GB+
- **Réseau** : Accès Internet + ports 80/443 ouverts
- **Utilisateur** : Accès sudo

### 🚀 Étape 1 : Préparation du Serveur

```bash
# Connexion au serveur
ssh user@your-server-ip

# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation des outils de base
sudo apt install -y git curl wget htop vim
```

### 📦 Étape 2 : Clone du Repository

```bash
# Clone du projet
git clone https://github.com/[YOUR_REPO]/ntp-monitor-enterprise.git
cd ntp-monitor-enterprise

# Basculer sur la branche dev (dernière version)
git checkout dev
```

### ⚙️ Étape 3 : Installation Automatique

```bash
# Rendre le script exécutable
chmod +x deployment/scripts/install.sh

# Lancement de l'installation complète
sudo ./deployment/scripts/install.sh
```

### 🎯 Étape 4 : Configuration Post-Installation

#### A. Configuration du domaine (optionnel)

```bash
# Éditer la configuration Apache
sudo nano /etc/apache2/sites-available/ntp-monitor.conf

# Remplacer localhost par votre domaine
ServerName your-domain.com
ServerAlias www.your-domain.com
```

#### B. Configuration SSL/HTTPS (recommandé)

```bash
# Installation de Certbot
sudo apt install -y certbot python3-certbot-apache

# Obtention du certificat SSL
sudo certbot --apache -d your-domain.com -d www.your-domain.com

# Test du renouvellement automatique
sudo certbot renew --dry-run
```

#### C. Configuration de la sécurité

```bash
# Configuration du firewall
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# Configuration des permissions
sudo chown -R ntpmonitor:www-data /var/www/ntp-monitor-enterprise
sudo chmod -R 755 /var/www/ntp-monitor-enterprise
```

---

## 🔧 Configuration Avancée

### 📊 Base de Données

```bash
# Initialisation manuelle de la BDD (si nécessaire)
cd /var/www/ntp-monitor-enterprise
sudo -u ntpmonitor ./venv/bin/python init_database.py init

# Vérification de la BDD
sudo -u ntpmonitor ./venv/bin/python init_database.py check
```

### 🎛️ Configuration des Services

```bash
# Status des services
sudo systemctl status apache2 redis-server ntpsec

# Redémarrage des services
sudo systemctl restart apache2
sudo systemctl restart redis-server
sudo systemctl restart ntpsec

# Logs en temps réel
sudo tail -f /var/log/apache2/ntp-monitor_error.log
sudo tail -f /var/www/ntp-monitor-enterprise/logs/app.log
```

### 🔍 Variables d'Environnement Production

```bash
# Création du fichier de configuration production
sudo nano /var/www/ntp-monitor-enterprise/.env

# Contenu du fichier .env
FLASK_ENV=production
DATABASE_URL=sqlite:///instance/ntp_monitor_prod.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-super-secret-key-here
ADMIN_EMAIL=admin@your-domain.com
SMTP_SERVER=smtp.your-domain.com
SMTP_PORT=587
SMTP_USERNAME=noreply@your-domain.com
SMTP_PASSWORD=your-smtp-password
```

---

## 🎯 Tests et Validation

### ✅ Checklist de Déploiement

```bash
# 1. Test HTTP
curl -I http://your-domain.com
# Résultat attendu: HTTP/1.1 200 OK

# 2. Test HTTPS (si configuré)
curl -I https://your-domain.com
# Résultat attendu: HTTP/1.1 200 OK

# 3. Test des services backend
sudo systemctl is-active apache2 redis-server ntpsec
# Résultat attendu: active active active

# 4. Test de la base de données
cd /var/www/ntp-monitor-enterprise
sudo -u ntpmonitor ./venv/bin/python -c "from app import create_app; from backend.app import db; app = create_app('production'); print('✅ BDD OK' if app else '❌ BDD ERROR')"

# 5. Test des requêtes NTP
sudo -u ntpmonitor ./venv/bin/python -c "import ntplib; c = ntplib.NTPClient(); print('✅ NTP OK' if c.request('pool.ntp.org') else '❌ NTP ERROR')"
```

### 🚨 Monitoring et Alertes

```bash
# Vérification des logs d'erreur
sudo grep -i error /var/log/apache2/ntp-monitor_error.log | tail -10

# Vérification de l'utilisation des ressources
htop
df -h
free -h

# Test de performance
curl -w "@curl-format.txt" -o /dev/null -s http://your-domain.com
```

---

## 🔄 Maintenance et Mises à Jour

### 📈 Mise à Jour de l'Application

```bash
# Sauvegarde avant mise à jour
sudo cp -r /var/www/ntp-monitor-enterprise /var/backups/ntp-monitor-$(date +%Y%m%d)

# Mise à jour du code
cd /var/www/ntp-monitor-enterprise
sudo git pull origin dev

# Mise à jour des dépendances
sudo -u ntpmonitor ./venv/bin/pip install -r requirements.txt --upgrade

# Redémarrage des services
sudo systemctl restart apache2
```

### 💾 Sauvegarde Automatique

```bash
# Script de sauvegarde
sudo nano /usr/local/bin/backup-ntp-monitor.sh

#!/bin/bash
BACKUP_DIR="/var/backups/ntp-monitor"
APP_DIR="/var/www/ntp-monitor-enterprise"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/ntp-monitor-$DATE.tar.gz $APP_DIR/instance/ $APP_DIR/logs/
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

# Rendre exécutable
sudo chmod +x /usr/local/bin/backup-ntp-monitor.sh

# Crontab pour sauvegarde quotidienne
sudo crontab -e
# Ajouter: 0 2 * * * /usr/local/bin/backup-ntp-monitor.sh
```

---

## 🛡️ Sécurité Production

### 🔐 Hardening Serveur

```bash
# Désactivation de l'utilisateur admin par défaut
# Connexion à l'interface web → Admin → Utilisateurs → Changer mot de passe

# Configuration fail2ban
sudo apt install -y fail2ban
sudo nano /etc/fail2ban/jail.local

[apache-ntp-monitor]
enabled = true
port = http,https
filter = apache-ntp-monitor
logpath = /var/log/apache2/ntp-monitor_access.log
maxretry = 5
bantime = 3600
```

### 📊 Monitoring Production

```bash
# Installation de monitoring (optionnel)
sudo apt install -y prometheus-node-exporter

# Configuration des alertes par email
sudo apt install -y mailutils postfix
```

---

## 📞 Support et Dépannage

### 🆘 Problèmes Courants

#### Erreur 500 - Internal Server Error
```bash
# Vérifier les logs Apache
sudo tail -f /var/log/apache2/ntp-monitor_error.log

# Vérifier les permissions
sudo chown -R ntpmonitor:www-data /var/www/ntp-monitor-enterprise
```

#### Application inaccessible
```bash
# Vérifier Apache
sudo systemctl status apache2
sudo apache2ctl configtest

# Vérifier les ports
sudo netstat -tlnp | grep :80
```

#### Erreurs Base de Données
```bash
# Réinitialiser la BDD (ATTENTION: perte de données)
cd /var/www/ntp-monitor-enterprise
sudo -u ntpmonitor ./venv/bin/python init_database.py reset
```

### 📧 Contacts

- **Documentation** : Voir README.md et guides dans le projet
- **Issues** : GitHub Issues du repository
- **Support** : [support@your-domain.com]

---

## ✅ Checklist Finale

- [ ] Serveur mis à jour et sécurisé
- [ ] Application installée et fonctionnelle  
- [ ] Base de données initialisée
- [ ] Services démarrés (Apache, Redis, NTP)
- [ ] SSL/HTTPS configuré (recommandé)
- [ ] Firewall configuré
- [ ] Monitoring en place
- [ ] Sauvegardes automatiques configurées
- [ ] Tests de fonctionnement réalisés
- [ ] Mot de passe admin changé
- [ ] Documentation d'exploitation créée

---

**🎉 Félicitations ! Votre NTP Monitor Enterprise est déployé avec succès !** 