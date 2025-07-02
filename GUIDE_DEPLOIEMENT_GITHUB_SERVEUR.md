# Guide de Déploiement GitHub → Serveur Ubuntu 24.04

## 🎯 Objectif

Ce guide vous permet de **déployer automatiquement** votre application NTP Monitor Enterprise depuis **GitHub** vers votre **serveur Ubuntu 24.04** avec toutes les corrections intégrées.

---

## 📋 Prérequis

### **Côté GitHub**
- Repository GitHub avec votre code NTP Monitor
- Branche `main` ou `master` avec le code à jour
- Accès en lecture au repository (public ou token pour privé)

### **Côté Serveur Ubuntu 24.04**
- Serveur Ubuntu 24.04 LTS
- Accès root (sudo)
- Connexion Internet
- 2 GB RAM minimum, 10 GB espace disque

---

## 🚀 Déploiement Rapide (Méthode Simple)

### **Étape 1 : Préparez le Script**
```bash
# Connexion au serveur
ssh root@votre-serveur.com

# Téléchargement du script
wget https://raw.githubusercontent.com/votre-repo/ntp-monitor/main/deploy_github_ubuntu.sh
chmod +x deploy_github_ubuntu.sh
```

### **Étape 2 : Configurez l'URL GitHub**
```bash
# Modifiez l'URL de votre repository
nano deploy_github_ubuntu.sh

# Changez cette ligne (ligne 13):
GITHUB_REPO="https://github.com/VOTRE-USERNAME/ntp-monitor.git"
```

### **Étape 3 : Exécutez le Déploiement**
```bash
# Déploiement automatique
sudo bash deploy_github_ubuntu.sh
```

**C'est tout !** Le script fait automatiquement :
- ✅ Installation des outils système
- ✅ Clonage depuis GitHub
- ✅ Application des corrections ('partitioned', fallback MySQL/SQLite)
- ✅ Installation packages compatibles
- ✅ Configuration service systemd
- ✅ Configuration Nginx reverse proxy
- ✅ Tests de validation

---

## ⚙️ Déploiement Avancé (Méthode Personnalisée)

### **Étape 1 : Configuration Personnalisée**
```bash
# Téléchargement configuration
wget https://raw.githubusercontent.com/votre-repo/ntp-monitor/main/deploy_config.env

# Personnalisation
nano deploy_config.env
```

**Variables importantes à modifier :**
```bash
# GitHub
GITHUB_REPO_URL="https://github.com/VOTRE-USERNAME/ntp-monitor.git"
GITHUB_BRANCH="main"  # ou votre branche

# Sécurité (IMPORTANT!)
SECRET_KEY="votre-cle-secrete-unique"
MYSQL_PASSWORD="mot-de-passe-mysql-fort"

# Réseau
NGINX_SERVER_NAME="votre-domaine.com"
```

### **Étape 2 : Chargement Configuration**
```bash
# Chargement des variables
source deploy_config.env

# Déploiement avec configuration
sudo -E bash deploy_github_ubuntu.sh
```

---

## 🔧 Corrections Automatiques Intégrées

Le script applique **automatiquement** toutes les corrections identifiées :

### **1. Erreur 'partitioned' Cookies**
```python
# Patch automatique dans backend/api/auth.py
def safe_cookie(response, key, value="", **kwargs):
    """Wrapper évitant erreur partitioned"""
    safe_kwargs = {k: v for k, v in kwargs.items() if k != "partitioned"}
    try:
        response.set_cookie(key, value, **safe_kwargs)
    except TypeError:
        response.set_cookie(key, value, path="/", httponly=True)
```

### **2. Versions Packages Corrigées**
```bash
# Installation automatique versions compatibles
Flask==2.3.3          # Évite bug partitioned
Werkzeug==2.3.7        # Compatible Flask 2.3.3
redis==4.6.0           # Compatible Celery
celery==5.3.4          # Version stable
Flask-SocketIO==5.3.6  # Version testée
python-socketio==5.8.0 # Stable
```

### **3. Fallback MySQL/SQLite**
```python
# Configuration automatique avec test MySQL
try:
    # Test connexion MySQL
    pymysql.connect(host='localhost', port=3306, user='root', 
                   password='', connect_timeout=2).close()
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost:3306/ntp_monitor'
    print("✅ MySQL utilisé")
except:
    # Fallback SQLite automatique
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    print("⚠️ SQLite utilisé")
```

---

## 📊 Processus de Déploiement Détaillé

### **Phase 1 : Préparation Système**
```bash
1. Installation outils système...
   ✅ git, python3, python3-pip, python3-venv
   ✅ nginx, mysql-server, redis-server
   ✅ curl, systemctl

2. Configuration utilisateur...
   ✅ Création utilisateur 'ntp-monitor'
   ✅ Configuration permissions
```

### **Phase 2 : Récupération Code**
```bash
3. Sauvegarde ancienne version...
   ✅ Arrêt service existant
   ✅ Sauvegarde avec timestamp

4. Récupération code GitHub...
   ✅ Clonage repository
   ✅ Checkout branche spécifiée
   ✅ Configuration propriétaire
```

### **Phase 3 : Application Corrections**
```bash
5. Application corrections automatiques...
   ✅ Configuration fallback MySQL/SQLite
   ✅ Patch cookies 'partitioned'
   ✅ Configuration production sécurisée

6. Installation packages corrigés...
   ✅ Désinstallation packages problématiques
   ✅ Installation versions compatibles
   ✅ Environnement virtuel isolé
```

### **Phase 4 : Configuration Services**
```bash
7. Configuration services...
   ✅ Démarrage MySQL/Redis
   ✅ Service systemd NTP Monitor
   ✅ Service Celery worker

8. Configuration Nginx...
   ✅ Reverse proxy port 5000
   ✅ Support WebSocket
   ✅ Fichiers statiques optimisés
```

### **Phase 5 : Finalisation**
```bash
9. Initialisation base de données...
   ✅ Création tables
   ✅ Données par défaut
   ✅ Comptes utilisateurs

10. Démarrage services...
    ✅ Service NTP Monitor
    ✅ Tests de validation
    ✅ Vérification accessibilité
```

---

## ✅ Tests de Validation Automatiques

Le script effectue des **tests automatiques** :

```bash
11. Tests de validation...
   ✅ Service actif         # systemctl is-active ntp-monitor
   ✅ Port 5000 ouvert      # ss -tlnp | grep :5000
   ✅ Application accessible # curl http://localhost:5000/
```

---

## 🌐 Accès à l'Application

### **URLs d'Accès**
- **Local** : http://localhost:5000
- **Réseau** : http://IP-SERVEUR:5000  
- **Nginx** : http://IP-SERVEUR (port 80)

### **Comptes par Défaut**
```
👤 Administrateur : admin / admin123
👤 Opérateur      : operator / operator123  
👤 Visualiseur    : viewer / viewer123
```

> **🚨 Important** : Changez les mots de passe par défaut !

---

## 🔧 Commandes de Maintenance

### **Gestion Service**
```bash
# Statut service
sudo systemctl status ntp-monitor

# Redémarrage
sudo systemctl restart ntp-monitor

# Logs en temps réel
sudo journalctl -u ntp-monitor -f

# Arrêt/Démarrage
sudo systemctl stop ntp-monitor
sudo systemctl start ntp-monitor
```

### **Mise à Jour depuis GitHub**
```bash
# Re-déploiement (met à jour depuis GitHub)
sudo bash deploy_github_ubuntu.sh

# Ou avec sauvegarde manuelle
sudo systemctl stop ntp-monitor
cd /opt/ntp-monitor
git pull origin main
sudo systemctl start ntp-monitor
```

### **Diagnostic**
```bash
# Vérification port
sudo ss -tlnp | grep :5000

# Test connexion
curl -I http://localhost:5000/

# Logs Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Vérification base de données
sudo -u ntp-monitor ls -la /opt/ntp-monitor/instance/
```

---

## 🛡️ Sécurité Production

### **Recommandations Essentielles**

#### **1. Certificats SSL/HTTPS**
```bash
# Installation Certbot (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx

# Génération certificat
sudo certbot --nginx -d votre-domaine.com

# Auto-renouvellement
sudo crontab -e
# Ajouter: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### **2. Firewall**
```bash
# Configuration UFW
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Restriction MySQL (si utilisé)
sudo ufw deny 3306
```

#### **3. Mots de Passe**
```bash
# Base de données MySQL
sudo mysql_secure_installation

# Application (via interface web)
# Connectez-vous et changez les mots de passe par défaut
```

#### **4. Monitoring**
```bash
# Installation monitoring (optionnel)
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

---

## 🔄 Mise à Jour Automatique

### **Script de Mise à Jour Périodique**
```bash
# Création script mise à jour
sudo tee /opt/ntp-monitor-update.sh << 'EOF'
#!/bin/bash
cd /opt/ntp-monitor
git pull origin main
sudo systemctl restart ntp-monitor
echo "$(date): Mise à jour automatique effectuée" >> /var/log/ntp-monitor-update.log
EOF

sudo chmod +x /opt/ntp-monitor-update.sh

# Programmation cron (mise à jour quotidienne à 3h du matin)
sudo crontab -e
# Ajouter: 0 3 * * * /opt/ntp-monitor-update.sh
```

---

## 🆘 Résolution de Problèmes

### **Problème : Service ne démarre pas**
```bash
# Diagnostic
sudo systemctl status ntp-monitor
sudo journalctl -u ntp-monitor --no-pager

# Solutions communes
sudo systemctl daemon-reload
sudo systemctl restart ntp-monitor
```

### **Problème : Port 5000 non accessible**
```bash
# Vérification processus
sudo netstat -tlnp | grep :5000
sudo lsof -i :5000

# Redémarrage
sudo pkill -f "python.*app.py"
sudo systemctl start ntp-monitor
```

### **Problème : Base de données**
```bash
# Réinitialisation
sudo -u ntp-monitor bash -c "
source /opt/ntp-monitor/.venv/bin/activate
cd /opt/ntp-monitor
python3 backend/utils/init_data.py
"
```

### **Problème : Packages**
```bash
# Réinstallation environnement
sudo rm -rf /opt/ntp-monitor/.venv
sudo -u ntp-monitor python3 -m venv /opt/ntp-monitor/.venv
sudo bash deploy_github_ubuntu.sh
```

---

## 📞 Support

### **Logs Importants**
- **Application** : `journalctl -u ntp-monitor -f`
- **Nginx** : `/var/log/nginx/ntp-monitor_*.log`
- **Système** : `/var/log/syslog`
- **Déploiement** : `/var/log/ntp-monitor-deploy.log`

### **Configuration Critique**
- **Service** : `/etc/systemd/system/ntp-monitor.service`
- **Nginx** : `/etc/nginx/sites-available/ntp-monitor`
- **App** : `/opt/ntp-monitor/config/config.py`

---

## 🎉 Conclusion

Avec ce guide et les scripts fournis, vous pouvez :

- ✅ **Déployer rapidement** depuis GitHub vers Ubuntu 24.04
- ✅ **Appliquer automatiquement** toutes les corrections
- ✅ **Configurer un environnement de production** sécurisé
- ✅ **Maintenir facilement** l'application

**NTP Monitor Enterprise** est maintenant prêt pour la production avec une **architecture robuste** et des **corrections intégrées** !

---

*Guide créé pour NTP Monitor Enterprise v2.1.0*  
*Compatible Ubuntu 24.04 LTS - Janvier 2025* 