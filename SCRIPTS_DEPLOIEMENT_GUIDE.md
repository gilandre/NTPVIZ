# Guide Complet - Scripts de Déploiement NTP Monitor Enterprise v2.1.0

## 🎯 **Vue d'ensemble**

Ce dossier contient un ensemble complet d'outils pour déployer, gérer et maintenir NTP Monitor Enterprise sur Ubuntu. Tous les scripts sont optimisés pour Ubuntu 24.04 avec préservation de ntpsec et utilisation de MySQL.

## 📋 **Scripts Disponibles**

### 🔍 **1. check_prerequisites.sh** - Vérification Prérequis
```bash
# Vérification complète avant déploiement
sudo ./check_prerequisites.sh
```

**Ce que fait ce script :**
- ✅ Vérifie les ressources système (CPU, RAM, disque)
- ✅ Teste la connectivité Internet et DNS
- ✅ Détecte les versions Python disponibles
- ✅ Vérifie l'état des services existants (MySQL, Apache, ntpsec)
- ✅ Contrôle les permissions et capacités système
- ✅ Identifie les conflits potentiels (ports occupés)
- ✅ Donne un rapport complet avec recommandations

**Sortie :**
- 🎉 **Système prêt** : Peut procéder au déploiement
- ⚠️ **Avertissements** : Déploiement possible avec surveillance
- ❌ **Erreurs** : Corrections nécessaires avant déploiement

---

### 🚀 **2. deploy_ubuntu_production_complete.sh** - Déploiement Unifié
```bash
# Déploiement automatique complet
chmod +x deploy_ubuntu_production_complete.sh
sudo ./deploy_ubuntu_production_complete.sh
```

**Script principal de déploiement - tout-en-un :**

#### **Fonctionnalités Intelligentes :**
- 🔍 **Détection automatique Python** (3.12 → 3.9)
- 🕐 **Préservation ntpsec existant** avec sauvegarde
- 🗄️ **Configuration MySQL sécurisée** avec credentials aléatoires
- 🌐 **Apache port 80 optimisé** avec WebSocket
- 📊 **Monitoring automatique** toutes les 15 minutes

#### **Phases d'exécution :**
1. **Vérification système** (prérequis, ressources, versions)
2. **Installation packages** (Python, MySQL, Apache, Redis, ntpsec)
3. **Configuration services** (sécurisation, optimisation)
4. **Déploiement application** (GitHub, dépendances, environnement)
5. **Configuration web** (WSGI, Virtual Host, SSL ready)
6. **Monitoring et validation** (tests, surveillance automatique)

---

### 🔧 **3. manage_ntp_monitor.sh** - Gestion Post-Déploiement
```bash
# Gestion complète de l'application déployée
chmod +x manage_ntp_monitor.sh
./manage_ntp_monitor.sh [COMMAND]
```

**Outil de maintenance et dépannage complet :**

#### **Commandes de Monitoring :**
```bash
./manage_ntp_monitor.sh status          # Statut tous services
./manage_ntp_monitor.sh logs [service]  # Logs spécifiques
./manage_ntp_monitor.sh test            # Tests connectivité
```

#### **Commandes de Gestion :**
```bash
sudo ./manage_ntp_monitor.sh start      # Démarrer services
sudo ./manage_ntp_monitor.sh stop       # Arrêter services
sudo ./manage_ntp_monitor.sh restart    # Redémarrer services
```

#### **Commandes de Maintenance :**
```bash
sudo ./manage_ntp_monitor.sh update           # Mise à jour GitHub
sudo ./manage_ntp_monitor.sh backup           # Sauvegarde complète
sudo ./manage_ntp_monitor.sh clean            # Nettoyage logs
sudo ./manage_ntp_monitor.sh reset-password   # Reset admin
```

#### **Commandes d'Information :**
```bash
./manage_ntp_monitor.sh info             # Infos système
./manage_ntp_monitor.sh help             # Aide complète
```

---

## 🔄 **Workflow de Déploiement Recommandé**

### **Étape 1 : Préparation**
```bash
# 1. Télécharger les scripts
git clone -b dev https://github.com/gilandre/NTPVIZ.git
cd NTPVIZ

# 2. Rendre les scripts exécutables
chmod +x *.sh

# 3. Vérifier les prérequis
sudo ./check_prerequisites.sh
```

### **Étape 2 : Déploiement**
```bash
# 4. Si prérequis OK, déployer
sudo ./deploy_ubuntu_production_complete.sh
```

### **Étape 3 : Validation**
```bash
# 5. Tester le déploiement
./manage_ntp_monitor.sh status
./manage_ntp_monitor.sh test

# 6. Accéder à l'application
# http://localhost ou http://IP-serveur
# Utilisateur: admin / Mot de passe: admin123
```

### **Étape 4 : Maintenance Continue**
```bash
# Surveillance quotidienne
./manage_ntp_monitor.sh status

# Mise à jour mensuelle
sudo ./manage_ntp_monitor.sh update

# Sauvegarde hebdomadaire
sudo ./manage_ntp_monitor.sh backup
```

---

## ⚙️ **Configuration et Personnalisation**

### **Variables Modifiables**

#### **Dans deploy_ubuntu_production_complete.sh :**
```bash
DOMAIN="192.168.10.45"           # Votre IP/domaine
GITHUB_BRANCH="dev"              # Branche GitHub
MYSQL_DB="ntp_monitor"           # Nom base de données
MYSQL_USER="ntp_user"            # Utilisateur MySQL
```

#### **Ports Utilisés :**
```bash
Port 80   : HTTP (Apache)
Port 443  : HTTPS (prêt pour SSL)
Port 3306 : MySQL
Port 5000 : Application Flask (interne)
Port 6379 : Redis
Port 123  : NTP (UDP)
Port 22   : SSH
```

### **Fichiers Importants Créés :**
```bash
# Configuration application
/home/ntp-monitor/ntp-monitor-enterprise/.env

# Credentials MySQL
/root/mysql_credentials.txt

# Configuration Apache
/etc/apache2/sites-available/ntp-monitor-enterprise.conf

# Service systemd
/etc/systemd/system/ntp-monitor-enterprise.service

# Sauvegarde ntpsec
/root/ntpsec_backup/YYYYMMDD_HHMMSS/

# Monitoring automatique
/home/ntp-monitor/monitor.sh
```

---

## 🛡️ **Fonctionnalités de Sécurité**

### **Sécurisation MySQL :**
- ✅ Suppression utilisateurs anonymes
- ✅ Suppression base de test
- ✅ Mot de passe aléatoire 16 caractères
- ✅ Utilisateur dédié avec privilèges minimaux

### **Sécurisation Apache :**
- ✅ Headers de sécurité (X-Frame-Options, X-XSS-Protection)
- ✅ Blocage accès fichiers sensibles (.env, .py, logs)
- ✅ Configuration WSGI sécurisée
- ✅ Prêt pour SSL/HTTPS

### **Sécurisation Système :**
- ✅ Utilisateur dédié non-privilégié
- ✅ Pare-feu UFW configuré
- ✅ Permissions fichiers restreintes
- ✅ Services isolés avec systemd

---

## 🔍 **Préservation ntpsec**

### **Détection Intelligente :**
- 🔍 Vérifie si ntpsec est installé et fonctionnel
- 📊 Compte les serveurs synchronisés
- 👥 Détecte les clients connectés
- ⚠️ Demande confirmation si clients actifs

### **Protection Configuration :**
- 💾 Sauvegarde automatique `/root/ntpsec_backup/`
- 🔄 Arrêt des services concurrents (chrony, timesyncd)
- ✅ Préservation complète de la synchronisation
- 🔧 Configuration application adaptée à ntpsec

---

## 🚨 **Dépannage Rapide**

### **Si l'application ne démarre pas :**
```bash
# 1. Vérifier les services
./manage_ntp_monitor.sh status

# 2. Voir les logs
./manage_ntp_monitor.sh logs app

# 3. Tester la connectivité
./manage_ntp_monitor.sh test

# 4. Redémarrer si nécessaire
sudo ./manage_ntp_monitor.sh restart
```

### **Si ntpsec pose problème :**
```bash
# Vérifier ntpsec
ntpq -c peers
sudo systemctl status ntpsec

# Vérifier les conflits
sudo systemctl status chronyd
sudo systemctl status systemd-timesyncd

# Restaurer sauvegarde si nécessaire
ls -la /root/ntpsec_backup/
```

### **Si MySQL ne fonctionne pas :**
```bash
# Vérifier MySQL
sudo systemctl status mysql

# Tester connexion
mysql -u ntp_user -p$(grep MYSQL_PASSWORD /root/mysql_credentials.txt | cut -d'=' -f2) ntp_monitor

# Voir les credentials
sudo cat /root/mysql_credentials.txt
```

---

## 📊 **Monitoring Automatique**

### **Script de Surveillance :**
Le script créé `/home/ntp-monitor/monitor.sh` s'exécute automatiquement toutes les 15 minutes via cron et :

- 🔍 Vérifie tous les services (MySQL, Redis, ntpsec, Apache, App)
- 🔄 Redémarre automatiquement les services arrêtés
- 🧹 Nettoie les logs anciens (30+ jours)
- 🌐 Teste l'accès web (HTTP 200)
- 📝 Logs toutes les actions dans `/home/ntp-monitor/logs/monitoring.log`

### **Surveillance Manuelle :**
```bash
# Statut général
./manage_ntp_monitor.sh status

# Tests complets
./manage_ntp_monitor.sh test

# Logs de monitoring
tail -f /home/ntp-monitor/logs/monitoring.log
```

---

## 🎉 **Avantages de cette Solution**

1. **🔄 Déploiement unifié** : Un seul script fait tout
2. **🧠 Intelligence adaptative** : Détection automatique des versions
3. **🛡️ Préservation existant** : Respecte ntpsec et configurations
4. **🔒 Sécurité renforcée** : Configuration sécurisée par défaut
5. **📊 Monitoring intégré** : Surveillance automatique 24/7
6. **🔧 Gestion simplifiée** : Outils de maintenance complets
7. **📋 Validation complète** : Tests automatiques post-déploiement
8. **📖 Documentation exhaustive** : Guides détaillés inclus

---

## 🤝 **Support et Maintenance**

Pour toute question ou problème :

1. **Consultez d'abord** : `./manage_ntp_monitor.sh help`
2. **Vérifiez les logs** : `./manage_ntp_monitor.sh logs`
3. **Testez la connectivité** : `./manage_ntp_monitor.sh test`
4. **Relancez le déploiement** : Les scripts sont idempotents

Les scripts sont conçus pour être **robustes** et **résilients**, avec une gestion d'erreurs complète et des messages explicites pour faciliter le dépannage.

---

**🎯 Objectif atteint : Déploiement NTP Monitor Enterprise v2.1.0 simplifié, sécurisé et maintenu automatiquement !** 