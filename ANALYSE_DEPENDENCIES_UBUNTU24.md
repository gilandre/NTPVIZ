# 📋 Analyse Complète des Dépendances - NTP Monitor Enterprise

## 🎯 Vue d'ensemble

Cette analyse holistique identifie **toutes les dépendances** nécessaires au bon fonctionnement de **NTP Monitor Enterprise v2.0.0** sur **Ubuntu Server 24.04 LTS**.

---

## 📊 Résumé des Dépendances Identifiées

### 🔧 **Système d'exploitation**
- **Ubuntu Server 24.04 LTS** (recommandé)
- **Compatibilité** : Ubuntu 22.04+ 
- **Architecture** : x86_64/amd64 (recommandé), ARM64 (supporté)

### 💾 **Ressources minimales**
- **RAM** : 1 GB minimum, 2 GB recommandé
- **Stockage** : 5 GB minimum, 10 GB recommandé
- **Processeur** : 1 vCPU minimum, 2 vCPU recommandé

---

## 🔍 Analyse Détaillée par Catégorie

### 1. **Packages Système Essentiels**

#### **Outils de base**
```bash
curl wget git htop vim tree net-tools unzip
software-properties-common apt-transport-https ca-certificates
gnupg lsb-release build-essential pkg-config ufw
```

#### **Pourquoi ces packages ?**
- `curl/wget` : Téléchargement de ressources externes
- `git` : Clone du repository depuis GitHub
- `build-essential` : Compilation des extensions Python natives
- `pkg-config` : Configuration des bibliothèques système
- `ufw` : Pare-feu pour sécurisation

### 2. **Environnement Python**

#### **Python et outils**
```bash
python3 python3-pip python3-venv python3-dev
python3-setuptools python3-wheel python3-distutils
```

#### **Version requise**
- **Python 3.11+** (idéalement Python 3.12)
- Support complet des fonctionnalités modernes
- Compatibilité avec toutes les dépendances

#### **Dépendances Python critiques** (via requirements.txt)
```python
# Framework Flask
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-SocketIO==5.3.6
Flask-Login==0.6.3
Flask-WTF==1.2.1

# Base de données
SQLAlchemy==2.0.21
PyMySQL==1.1.0

# Services
redis==5.0.1
ntplib==0.4.0
psutil==5.9.5
requests==2.31.0

# Sécurité
Werkzeug==2.3.7
bcrypt==4.0.1
cryptography

# WebSocket
python-socketio==5.8.0

# Serveur web
gunicorn==21.2.0

# Configuration
python-dotenv==1.0.0

# Utilitaires
pytz python-dateutil pandas numpy
```

### 3. **Base de Données MySQL**

#### **Packages MySQL**
```bash
mysql-server mysql-client libmysqlclient-dev mysql-common
```

#### **Configuration requise**
- **Base de données** : `ntp_monitor`
- **Utilisateur** : `ntp_user`
- **Charset** : `utf8mb4`
- **Permissions** : ALL PRIVILEGES sur la base

#### **Driver Python**
- **PyMySQL** : Driver Python pur (fallback)
- **mysqlclient** : Driver natif C (optimal, nécessite libmysqlclient-dev)

### 4. **Serveur Web Apache**

#### **Packages Apache**
```bash
apache2 libapache2-mod-wsgi-py3 apache2-utils
```

#### **Modules requis**
- `mod_wsgi` : Interface Python/Apache
- `mod_rewrite` : Réécriture d'URL
- `mod_ssl` : Support HTTPS
- `mod_headers` : Gestion des headers HTTP

#### **Configuration**
- **VirtualHost** sur port 80/443
- **DocumentRoot** vers l'application
- **WSGIDaemonProcess** pour isolation

### 5. **Services Réseau**

#### **Redis**
```bash
redis-server
```
- **Usage** : Cache, sessions, WebSocket
- **Configuration** : localhost:6379
- **Mode** : Threading compatible

#### **NTP**
```bash
ntp ntpdate ntpstat
```
- **Usage** : Synchronisation temporelle + monitoring
- **Configuration** : Pool NTP + serveurs locaux
- **Ports** : 123/udp

### 6. **Sécurité et SSL**

#### **Packages SSL/TLS**
```bash
certbot python3-certbot-apache openssl
```
- **Let's Encrypt** : Certificats SSL automatiques
- **OpenSSL** : Chiffrement et génération de clés

#### **Pare-feu UFW**
```bash
ufw
```
- **Ports ouverts** : 22 (SSH), 80 (HTTP), 443 (HTTPS), 123 (NTP)
- **Politique** : DENY par défaut, ALLOW spécifique

### 7. **Outils de Monitoring**

#### **Packages monitoring**
```bash
psmisc lsof tcpdump iftop
```
- **psmisc** : Processus et signaux
- **lsof** : Fichiers ouverts et connexions
- **tcpdump** : Analyse réseau
- **iftop** : Monitoring bande passante

---

## 🚀 Script de Vérification Automatique

### **dependencies_checker_ubuntu24.sh**

Le script `dependencies_checker_ubuntu24.sh` effectue :

#### **Phase 1 : Vérifications**
1. ✅ **Système** : Version Ubuntu, ressources
2. ✅ **Packages** : Tous les packages requis
3. ✅ **Python** : Version, pip, venv, modules
4. ✅ **Services** : MySQL, Apache, Redis, NTP
5. ✅ **Base de données** : MySQL, drivers, connexion
6. ✅ **Apache** : Installation, modules, ports
7. ✅ **Réseau** : Internet, DNS, NTP, firewall

#### **Phase 2 : Installation automatique**
1. 🔧 **Packages système** : apt install complet
2. 🔧 **MySQL** : Configuration + base + utilisateur
3. 🔧 **Apache** : Activation modules + configuration
4. 🔧 **Services** : Démarrage + activation
5. 🔧 **Python** : Installation dépendances critiques
6. 🔧 **Firewall** : Configuration UFW

#### **Phase 3 : Tests finaux**
1. 🧪 **MySQL** : Connexion + version
2. 🧪 **Apache** : Status + accessibility
3. 🧪 **Redis** : Ping test
4. 🧪 **NTP** : Synchronisation
5. 🧪 **Python** : Import des modules critiques
6. 🧪 **Réseau** : Connectivité Internet

---

## 📋 Utilisation du Script

### **Prérequis**
```bash
# 1. Système Ubuntu 24.04 LTS
# 2. Accès root (sudo)
# 3. Connexion Internet
```

### **Installation**
```bash
# 1. Copier le script sur le serveur Ubuntu
scp dependencies_checker_ubuntu24.sh user@server:/tmp/

# 2. Se connecter au serveur
ssh user@server

# 3. Rendre le script exécutable
chmod +x /tmp/dependencies_checker_ubuntu24.sh

# 4. Exécuter en tant que root
sudo /tmp/dependencies_checker_ubuntu24.sh
```

### **Modes d'exécution**

#### **Mode Vérification seule** (système déjà configuré)
```bash
sudo ./dependencies_checker_ubuntu24.sh
# Le script détecte automatiquement si tout est OK
# et effectue seulement les vérifications
```

#### **Mode Installation complète** (système vierge)
```bash
sudo ./dependencies_checker_ubuntu24.sh
# Le script détecte les éléments manquants
# et procède à l'installation automatique
```

### **Sortie du script**

#### **En cas de succès** ✅
```
🎉 INSTALLATION COMPLÈTE RÉUSSIE !
Votre système Ubuntu 24.04 est maintenant prêt pour NTP Monitor Enterprise

🔧 Configuration système:
  ✓ Ubuntu 24.04 installé et à jour
  ✓ Python 3.12 configuré
  ✓ MySQL 8.0 opérationnel
  ✓ Apache 2.4 avec mod_wsgi
  ✓ Redis 7.0 actif
  ✓ NTP synchronisé
  ✓ Pare-feu UFW configuré

📊 Base de données MySQL:
  • Base de données: ntp_monitor
  • Utilisateur: ntp_user
  • Mot de passe: voir /root/mysql_credentials.txt

🚀 Prochaines étapes:
  1. Cloner le code NTP Monitor Enterprise
  2. Configurer l'application (.env)
  3. Déployer avec deploy_ubuntu_production.sh
  4. Configurer SSL/TLS (certbot)
  5. Accéder à l'interface web
```

#### **En cas d'erreur** ❌
```
❌ INSTALLATION INCOMPLÈTE
Des erreurs ont été détectées et doivent être corrigées

🔧 Actions recommandées:
  1. Corriger les erreurs signalées ci-dessus
  2. Relancer ce script: sudo dependencies_checker_ubuntu24.sh
  3. Vérifier la configuration réseau
  4. Consulter les logs détaillés
```

---

## 🔗 Intégration avec le Déploiement

### **Workflow complet**

```bash
# Étape 1 : Vérification des dépendances
sudo ./dependencies_checker_ubuntu24.sh

# Étape 2 : Clone de l'application
git clone https://github.com/votre-repo/NTPVIZ.git
cd NTPVIZ

# Étape 3 : Déploiement avec le script existant
# (modifier DOMAIN dans le script avant exécution)
sudo ./deploy_ubuntu_production.sh
```

### **Fichiers de configuration générés**

#### **MySQL credentials** (/root/mysql_credentials.txt)
```bash
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=ntp_monitor
MYSQL_USER=ntp_user
MYSQL_PASSWORD=<généré_automatiquement>
```

#### **Services activés**
```bash
systemctl status mysql apache2 redis-server ntp ufw
```

---

## 🛠️ Dépannage

### **Problèmes courants**

#### **1. Erreur de permissions**
```bash
# Solution : Exécuter en tant que root
sudo ./dependencies_checker_ubuntu24.sh
```

#### **2. Espace disque insuffisant**
```bash
# Vérifier l'espace
df -h

# Nettoyer si nécessaire
sudo apt clean
sudo apt autoremove
```

#### **3. Problème réseau**
```bash
# Tester la connectivité
ping -c 4 8.8.8.8
nslookup google.com

# Vérifier les DNS
cat /etc/resolv.conf
```

#### **4. MySQL ne démarre pas**
```bash
# Vérifier les logs
sudo journalctl -u mysql

# Vérifier l'espace disque
df -h /var/lib/mysql
```

#### **5. Apache ne démarre pas**
```bash
# Vérifier la configuration
sudo apache2ctl configtest

# Vérifier les logs
sudo tail -f /var/log/apache2/error.log
```

### **Logs et diagnostics**

#### **Logs système**
```bash
# Logs généraux
sudo journalctl -xe

# Logs par service
sudo journalctl -u mysql
sudo journalctl -u apache2
sudo journalctl -u redis-server
```

#### **Tests manuels**
```bash
# Test MySQL
mysql -u root -e "SELECT VERSION();"

# Test Apache
curl -I http://localhost

# Test Redis
redis-cli ping

# Test Python
python3 -c "import flask, sqlalchemy, pymysql, redis"
```

---

## 📈 Monitoring Post-Installation

### **Commandes de vérification**

#### **Status des services**
```bash
sudo systemctl status mysql apache2 redis-server ntp
```

#### **Ports en écoute**
```bash
sudo netstat -tlnp | grep -E ':80|:443|:3306|:6379|:123'
```

#### **Processus**
```bash
ps aux | grep -E 'mysql|apache|redis|ntp'
```

#### **Logs en temps réel**
```bash
sudo tail -f /var/log/apache2/access.log
sudo tail -f /var/log/mysql/error.log
```

---

## 🎯 Conclusion

Le script `dependencies_checker_ubuntu24.sh` garantit une **installation complète et robuste** de toutes les dépendances nécessaires à **NTP Monitor Enterprise**. 

### **Points forts**
✅ **Vérification exhaustive** de tous les composants  
✅ **Installation automatique** des éléments manquants  
✅ **Configuration optimisée** pour production  
✅ **Tests de validation** complets  
✅ **Rapport détaillé** avec prochaines étapes  
✅ **Gestion d'erreurs** robuste  

### **Résultat attendu**
Un système **Ubuntu 24.04 LTS** parfaitement configuré et prêt à accueillir **NTP Monitor Enterprise** avec toutes ses fonctionnalités.

---

**🚀 Votre système sera prêt pour un déploiement production de NTP Monitor Enterprise !** 