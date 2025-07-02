# Guide Déploiement GitHub → Serveur Ubuntu 24.04

## 🚀 Déploiement Automatique NTP Monitor Enterprise

### **Utilisation Simple (3 étapes)**

#### **1. Préparez le script sur votre serveur**
```bash
# Connexion serveur
ssh root@votre-serveur.com

# Téléchargement script
wget https://raw.githubusercontent.com/votre-repo/deploy_github_ubuntu.sh
chmod +x deploy_github_ubuntu.sh
```

#### **2. Configurez l'URL GitHub**
```bash
# Modifiez l'URL de votre repository (ligne 13)
nano deploy_github_ubuntu.sh

# Changez:
GITHUB_REPO="https://github.com/VOTRE-USERNAME/ntp-monitor.git"
```

#### **3. Exécutez le déploiement**
```bash
sudo bash deploy_github_ubuntu.sh
```

**✅ Terminé !** L'application sera accessible sur http://IP-SERVEUR:5000

---

## 📋 Ce que fait le Script Automatiquement

### **🔧 Corrections Intégrées**
- ✅ **Erreur 'partitioned'** → Flask 2.3.3 + wrapper sécurisé  
- ✅ **Packages compatibles** → Versions testées (Redis 4.6.0, Celery 5.3.4, etc.)
- ✅ **Fallback MySQL/SQLite** → Bascule automatique selon disponibilité
- ✅ **Configuration production** → Sécurisée et optimisée

### **🏗️ Infrastructure Déployée**
- ✅ **Environnement virtuel** → Isolation packages
- ✅ **Service systemd** → Démarrage automatique
- ✅ **Nginx reverse proxy** → Port 80 → 5000
- ✅ **Base de données** → MySQL ou SQLite selon disponibilité
- ✅ **Utilisateur dédié** → Sécurité renforcée

---

## 🌐 Accès Application

- **URL Principale** : http://IP-SERVEUR
- **URL Directe** : http://IP-SERVEUR:5000  
- **Comptes** : admin/admin123, operator/operator123

---

## 🔧 Commandes Utiles

```bash
# Statut service
sudo systemctl status ntp-monitor

# Logs en temps réel
sudo journalctl -u ntp-monitor -f

# Redémarrage
sudo systemctl restart ntp-monitor

# Mise à jour depuis GitHub
sudo bash deploy_github_ubuntu.sh
```

---

## 📊 Structure Déployée

```
/opt/ntp-monitor/                 # Application
├── .venv/                        # Environnement virtuel
├── backend/                      # Code Python
├── frontend/                     # Interface web
├── config/                       # Configuration (avec corrections)
├── instance/                     # Base de données SQLite
└── logs/                         # Logs application

/etc/systemd/system/
├── ntp-monitor.service           # Service principal
└── ntp-monitor-worker.service    # Worker Celery

/etc/nginx/sites-available/
└── ntp-monitor                   # Configuration Nginx
```

---

## 🛡️ Sécurité Production

### **Actions Recommandées**
```bash
# 1. SSL/HTTPS
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d votre-domaine.com

# 2. Firewall
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 3. Changement mots de passe
# Via interface web : http://IP-SERVEUR
```

---

## 🔄 Mise à Jour Automatique

### **Script mise à jour périodique**
```bash
# Création script
sudo tee /opt/update-ntp.sh << 'EOF'
#!/bin/bash
cd /opt/ntp-monitor
git pull origin main
sudo systemctl restart ntp-monitor
EOF

sudo chmod +x /opt/update-ntp.sh

# Programmation quotidienne (3h du matin)
sudo crontab -e
# Ajouter: 0 3 * * * /opt/update-ntp.sh
```

---

## 🆘 Dépannage Rapide

### **Service inactif**
```bash
sudo systemctl daemon-reload
sudo systemctl restart ntp-monitor
sudo journalctl -u ntp-monitor --no-pager
```

### **Port non accessible**
```bash
sudo ss -tlnp | grep :5000
sudo systemctl restart nginx
```

### **Base de données corrompue**
```bash
sudo rm -f /opt/ntp-monitor/instance/ntp_monitor.db
sudo systemctl restart ntp-monitor
```

---

## ✅ Vérification Déploiement Réussi

### **Tests automatiques effectués**
- ✅ Service ntp-monitor actif
- ✅ Port 5000 accessible  
- ✅ Application web répond
- ✅ Base de données initialisée
- ✅ Nginx configuré

### **Tests manuels recommandés**
```bash
# Test service
systemctl is-active ntp-monitor

# Test application
curl -I http://localhost:5000/

# Test Nginx
curl -I http://localhost/

# Test base de données
sudo -u ntp-monitor ls /opt/ntp-monitor/instance/
```

---

## 📞 Configuration Avancée

### **Variables personnalisables** (optionnel)
```bash
# Dans deploy_github_ubuntu.sh
GITHUB_REPO="https://github.com/votre-repo/ntp-monitor.git"
GITHUB_BRANCH="main"
APP_DIR="/opt/ntp-monitor"
SERVICE_NAME="ntp-monitor"
USER_APP="ntp-monitor"
```

### **Configuration MySQL personnalisée**
```bash
# Si MySQL configuré avec mot de passe
sudo mysql -u root -p
CREATE DATABASE ntp_monitor;
CREATE USER 'ntp_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_user'@'localhost';

# Modifier config/config.py après déploiement
sudo nano /opt/ntp-monitor/config/config.py
```

---

## 🎉 Résultat Final

Après exécution du script, vous obtenez :

- 🏢 **Application NTP Monitor Enterprise** opérationnelle
- 🔧 **Toutes les corrections appliquées** (partitioned, packages, fallback)
- 🌐 **Interface web accessible** via Nginx
- 🛡️ **Environnement sécurisé** avec utilisateur dédié
- 🔄 **Service systemd** pour démarrage automatique
- 📊 **Monitoring 8 serveurs NTP** par défaut

**🎯 Prêt pour la production en 5 minutes !**

---

*Guide pour NTP Monitor Enterprise v2.1.0*  
*Ubuntu 24.04 LTS - Janvier 2025* 