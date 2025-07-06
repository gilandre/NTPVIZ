# 🚀 Installation Rapide - NTP Monitor Enterprise

**Guide simple pour débutants - Premier déploiement sur Ubuntu 24.04**

---

## ⚡ Installation Automatique (Recommandée)

### 1. Connectez-vous à votre serveur
```bash
ssh root@votre-serveur-ip
```

### 2. Installez NTP Monitor Enterprise
```bash
curl -fsSL https://raw.githubusercontent.com/gilandre/ntp-monitor-enterprise/main/scripts/install_auto.sh | sudo bash
```

### 3. Accédez à l'interface
- **URL** : `http://votre-serveur-ip`
- **Utilisateur** : `admin`
- **Mot de passe** : `admin123`

⚠️ **Changez le mot de passe après la première connexion !**

---

## ✅ Vérification de l'Installation

```bash
# Télécharger et exécuter le script de vérification
curl -fsSL https://raw.githubusercontent.com/gilandre/ntp-monitor-enterprise/main/scripts/verify_installation.sh | bash
```

---

## 🎯 Ce que vous obtenez

- ✅ **Interface web moderne** accessible via votre navigateur
- ✅ **Monitoring de 8 serveurs NTP** (3 mondiaux + 5 locaux configurables)
- ✅ **Alertes en temps réel** avec seuils configurables
- ✅ **Graphiques interactifs** avec historique et zoom
- ✅ **Multi-utilisateurs** avec rôles (admin/opérateur/visualiseur)
- ✅ **API REST** pour intégrations externes
- ✅ **WebSocket** pour mises à jour temps réel
- ✅ **Base de données MySQL** avec fallback SQLite
- ✅ **Cache Redis** pour performances optimales
- ✅ **Serveur NTP** (ntpsec) intégré

---

## 🔧 Prérequis Serveur

| Composant | Minimum | Recommandé |
|-----------|---------|------------|
| **OS** | Ubuntu 24.04 LTS | Ubuntu 24.04 LTS |
| **RAM** | 2GB | 4GB |
| **Disque** | 10GB libre | 20GB libre |
| **CPU** | 1 core | 2 cores |
| **Réseau** | 100 Mbps | 1 Gbps |

### Ports utilisés
- **22** : SSH
- **80** : Interface web (HTTP)
- **443** : Interface web (HTTPS)
- **123** : Serveur NTP
- **3306** : MySQL (local)
- **5000** : Application (développement)
- **6379** : Redis (local)

---

## 📋 Installation Manuelle (Étape par étape)

Si vous préférez comprendre chaque étape :

### 1. Préparation
```bash
# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installation packages essentiels
sudo apt install -y curl wget git python3 python3-pip python3-venv \
    mysql-server apache2 libapache2-mod-wsgi-py3 redis-server \
    ntpsec build-essential ufw fail2ban
```

### 2. Sécurité
```bash
# Configuration pare-feu
sudo ufw allow 22/tcp 80/tcp 443/tcp 123/udp
sudo ufw --force enable

# Activation fail2ban
sudo systemctl enable fail2ban && sudo systemctl start fail2ban
```

### 3. Base de données
```bash
# Sécurisation MySQL
sudo mysql_secure_installation

# Création base de données
sudo mysql -e "
CREATE DATABASE ntp_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ntp_user'@'localhost' IDENTIFIED BY 'VotreMotDePasseSecurise';
GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_user'@'localhost';
FLUSH PRIVILEGES;"
```

### 4. Application
```bash
# Création utilisateur
sudo useradd -m -s /bin/bash ntp-monitor

# Téléchargement
sudo -u ntp-monitor git clone https://github.com/gilandre/ntp-monitor-enterprise.git /opt/ntp-monitor-enterprise

# Environnement Python
sudo -u ntp-monitor python3 -m venv /opt/ntp-monitor-venv
sudo -u ntp-monitor /opt/ntp-monitor-venv/bin/pip install -r /opt/ntp-monitor-enterprise/requirements.txt
```

### 5. Configuration
```bash
# Configuration application
sudo -u ntp-monitor cp /opt/ntp-monitor-enterprise/.env.example /opt/ntp-monitor-enterprise/.env
sudo -u ntp-monitor nano /opt/ntp-monitor-enterprise/.env

# Initialisation base de données
cd /opt/ntp-monitor-enterprise
sudo -u ntp-monitor /opt/ntp-monitor-venv/bin/python init_database.py
```

---

## 🛠️ Commandes Utiles

### Gestion des services
```bash
# Statut de tous les services
sudo systemctl status ntp-monitor apache2 mysql redis-server

# Redémarrer l'application
sudo systemctl restart ntp-monitor

# Redémarrer Apache
sudo systemctl restart apache2
```

### Logs et diagnostic
```bash
# Logs de l'application
sudo journalctl -u ntp-monitor -f

# Logs Apache
sudo tail -f /var/log/apache2/ntp-monitor_error.log

# Test interface web
curl http://localhost
```

### Configuration
```bash
# Éditer la configuration
sudo nano /opt/ntp-monitor-enterprise/.env

# Recharger après modification
sudo systemctl restart ntp-monitor
```

---

## 🚨 Dépannage Rapide

### Interface web non accessible
```bash
# Vérifier Apache
sudo systemctl status apache2
sudo systemctl restart apache2

# Vérifier pare-feu
sudo ufw status
sudo ufw allow 80/tcp
```

### Service ne démarre pas
```bash
# Vérifier les logs
sudo journalctl -u ntp-monitor --no-pager

# Vérifier les permissions
sudo chown -R ntp-monitor:ntp-monitor /opt/ntp-monitor-enterprise

# Redémarrer le service
sudo systemctl daemon-reload
sudo systemctl restart ntp-monitor
```

### Base de données non accessible
```bash
# Test connexion
mysql -u ntp_user -p ntp_monitor -e "SELECT 1"

# Réinitialiser base de données
sudo systemctl stop ntp-monitor
cd /opt/ntp-monitor-enterprise
sudo -u ntp-monitor /opt/ntp-monitor-venv/bin/python init_database.py
sudo systemctl start ntp-monitor
```

---

## 🔐 Sécurisation

### 1. Changer les mots de passe
- **Interface web** : Connectez-vous et changez le mot de passe admin
- **Base de données** : Utilisez un mot de passe fort dans `.env`

### 2. Configurer SSL/HTTPS
```bash
# Installation certbot
sudo apt install certbot python3-certbot-apache

# Obtenir certificat SSL
sudo certbot --apache -d votre-domaine.com

# Renouvellement automatique
sudo systemctl enable certbot.timer
```

### 3. Durcir la sécurité
```bash
# Désactiver mot de passe SSH (optionnel)
sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Mise à jour automatique
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

---

## 📊 Configuration Avancée

### Serveurs NTP personnalisés
1. Connectez-vous à l'interface web
2. Allez dans **Administration** → **Configuration**
3. Modifiez la section **Serveurs NTP Locaux**
4. Ajoutez vos serveurs (ex: `192.168.1.1,10.0.0.1`)

### Seuils d'alertes
1. **Administration** → **Alertes**
2. Configurez les seuils :
   - **Offset** : 100ms (par défaut)
   - **Délai** : 500ms (par défaut)

### Notifications email
1. Éditez le fichier `.env`
2. Configurez les paramètres SMTP :
   ```env
   ALERT_EMAIL_ENABLED=true
   ALERT_EMAIL_SMTP=smtp.gmail.com
   ALERT_EMAIL_USERNAME=votre-email@gmail.com
   ALERT_EMAIL_PASSWORD=votre-mot-de-passe-app
   ```

---

## 📞 Support

### Documentation complète
- **[Guide de Déploiement](DEPLOYMENT_GITHUB.md)** - Instructions détaillées
- **[Guide Production](GUIDE_DEPLOIEMENT_PRODUCTION.md)** - Configuration avancée
- **[README](README.md)** - Présentation complète

### En cas de problème
1. **Vérifiez les logs** : `sudo journalctl -u ntp-monitor -f`
2. **Exécutez la vérification** : Script `verify_installation.sh`
3. **Consultez la FAQ** : Section dépannage dans les guides
4. **Créez un ticket** : [GitHub Issues](https://github.com/gilandre/ntp-monitor-enterprise/issues)

### Informations système
```bash
# Collecter les informations pour le support
sudo systemctl status ntp-monitor apache2 mysql
sudo journalctl -u ntp-monitor --since "1 hour ago" --no-pager
curl -s http://localhost/api/system/status
```

---

## 🎉 Félicitations !

Votre **NTP Monitor Enterprise** est maintenant installé et opérationnel !

### Prochaines étapes recommandées :
1. ✅ **Connexion** à l'interface web
2. ✅ **Changement** du mot de passe administrateur
3. ✅ **Configuration** des serveurs NTP locaux
4. ✅ **Test** des alertes et notifications
5. ✅ **Configuration** SSL pour la production
6. ✅ **Sauvegarde** de la configuration

**🚀 Votre infrastructure de monitoring NTP est prête !**

---

*NTP Monitor Enterprise v2.1.0 - Installation rapide pour débutants*  
*Dernière mise à jour : Janvier 2025* 