# Guide de Déploiement Production - NTP Monitor Enterprise v2.1.0

## 🎯 **Objectif**

Ce guide présente le script de déploiement unifié `deploy_ubuntu_production_complete.sh` qui automatise entièrement l'installation de NTP Monitor Enterprise sur Ubuntu avec :
- ✅ **Vérification intelligente des prérequis**
- ✅ **Préservation de ntpsec existant**
- ✅ **Configuration MySQL robuste**
- ✅ **Déploiement sur port 80 avec Apache**
- ✅ **Détection automatique des versions**
- ✅ **Monitoring automatique**

## 🚀 **Déploiement Rapide**

### **Commande Unique**
```bash
# Télécharger et exécuter
chmod +x deploy_ubuntu_production_complete.sh
sudo ./deploy_ubuntu_production_complete.sh
```

### **Ou depuis GitHub**
```bash
# Cloner le repo et déployer
git clone -b dev https://github.com/gilandre/NTPVIZ.git
cd NTPVIZ
chmod +x deploy_ubuntu_production_complete.sh
sudo ./deploy_ubuntu_production_complete.sh
```

## 📋 **Prérequis Automatiquement Vérifiés**

Le script vérifie automatiquement :

| Composant | Requis | Vérification |
|-----------|--------|--------------|
| **Système** | Ubuntu (recommandé) | Distribution détectée |
| **Espace disque** | ≥ 2GB libre | `df -BG /` |
| **Mémoire** | ≥ 512MB | `free -m` |
| **Internet** | Connexion active | `ping 8.8.8.8` |
| **Python** | 3.9+ | Auto-détection 3.12→3.9 |
| **Droits** | root/sudo | `$EUID` |

## 🔧 **Ce que fait le script**

### **Phase 1: Vérification Système**
```bash
✅ Vérification espace disque (2GB+)
✅ Vérification mémoire (512MB+)
✅ Test connexion Internet
✅ Détection version Python optimale
✅ Vérification état ntpsec existant
```

### **Phase 2: Installation Packages**
```bash
✅ Mise à jour système (apt update/upgrade)
✅ Installation Python selon version détectée
✅ Installation MySQL + Apache + Redis
✅ Installation ntpsec (si nécessaire)
✅ Installation outils système complets
```

### **Phase 3: Configuration Services**
```bash
✅ Configuration ntpsec (préservation existant)
✅ Configuration MySQL sécurisée
✅ Configuration Redis
✅ Configuration Apache + modules
✅ Configuration pare-feu UFW
```

### **Phase 4: Déploiement Application**
```bash
✅ Création utilisateur dédié
✅ Clone depuis GitHub (branche dev)
✅ Environnement virtuel Python
✅ Installation dépendances corrigées
✅ Configuration variables d'environnement
```

### **Phase 5: Configuration Web**
```bash
✅ Création fichier WSGI adaptatif
✅ Configuration Apache Virtual Host port 80
✅ Support WebSocket pour SocketIO
✅ Création service systemd
✅ Activation et démarrage services
```

### **Phase 6: Monitoring et Validation**
```bash
✅ Script de monitoring automatique
✅ Cron job toutes les 15 minutes
✅ Validation tous les services
✅ Test accès web
✅ Affichage informations finales
```

## 🔍 **Fonctionnalités Intelligentes**

### **Détection Automatique Python**
```bash
# Ordre de préférence automatique
1. python3.12 (Ubuntu 24.04)
2. python3.11 (Ubuntu 22.04)
3. python3.10 (Ubuntu 20.04)
4. python3.9 (fallback)
5. python3 (défaut système)
```

### **Préservation ntpsec**
```bash
# Si ntpsec fonctionne déjà
✅ Détection configuration existante
✅ Sauvegarde automatique dans /root/ntpsec_backup/
✅ Préservation clients connectés
✅ Arrêt services concurrents (chrony, systemd-timesyncd)
✅ Maintien synchronisation existante
```

### **Configuration MySQL Sécurisée**
```bash
# Sécurisation automatique
✅ Suppression utilisateurs anonymes
✅ Suppression base 'test'
✅ Création base ntp_monitor + utilisateur
✅ Mot de passe aléatoire 16 caractères
✅ Sauvegarde credentials dans /root/mysql_credentials.txt
```

### **Apache Port 80 Optimisé**
```bash
# Configuration complète
✅ Virtual Host port 80
✅ mod_wsgi avec environnement virtuel
✅ Support WebSocket (SocketIO)
✅ Proxy pass pour temps réel
✅ Fichiers statiques optimisés
✅ Sécurité et headers
```

## 📊 **Monitoring Automatique**

Le script installe un système de monitoring qui :

```bash
# Toutes les 15 minutes via cron
✅ Vérifie tous les services (MySQL, Redis, ntpsec, Apache, App)
✅ Redémarre automatiquement les services arrêtés
✅ Nettoie les logs anciens (30+ jours)
✅ Teste l'accès web (curl localhost)
✅ Logs dans /home/ntp-monitor/logs/monitoring.log
```

## 🌐 **Accès Application**

### **URLs d'accès**
```bash
# Local
http://localhost

# IP serveur
http://192.168.10.45  # (modifiable dans le script)

# Connexion par défaut
Utilisateur: admin
Mot de passe: admin123
```

### **Ports ouverts**
```bash
Port 22  : SSH
Port 80  : HTTP (Apache)
Port 443 : HTTPS (prêt pour SSL)
Port 123 : NTP (UDP)
```

## 🔧 **Gestion Post-Déploiement**

### **Commandes de gestion**
```bash
# Service principal
sudo systemctl status ntp-monitor-enterprise
sudo systemctl restart ntp-monitor-enterprise
sudo systemctl stop ntp-monitor-enterprise

# Logs en temps réel
sudo journalctl -u ntp-monitor-enterprise -f
sudo tail -f /var/log/apache2/ntp-monitor-enterprise_error.log

# Vérification ntpsec
ntpq -c peers
ntpq -c associations
sudo systemctl status ntpsec

# Base de données
mysql -u ntp_user -p$(grep MYSQL_PASSWORD /root/mysql_credentials.txt | cut -d'=' -f2) ntp_monitor
```

### **Fichiers importants**
```bash
# Application
/home/ntp-monitor/ntp-monitor-enterprise/

# Configuration
/home/ntp-monitor/ntp-monitor-enterprise/.env

# Credentials MySQL
/root/mysql_credentials.txt

# Configuration Apache
/etc/apache2/sites-available/ntp-monitor-enterprise.conf

# Service systemd
/etc/systemd/system/ntp-monitor-enterprise.service

# Monitoring
/home/ntp-monitor/monitor.sh
```

## 🐛 **Dépannage**

### **Si l'application ne démarre pas**
```bash
# 1. Vérifier les logs
sudo journalctl -u ntp-monitor-enterprise -f

# 2. Vérifier les services
sudo systemctl status mysql
sudo systemctl status redis-server
sudo systemctl status apache2
sudo systemctl status ntpsec

# 3. Test manuel
cd /home/ntp-monitor/ntp-monitor-enterprise
sudo -u ntp-monitor venv/bin/python app.py

# 4. Vérifier configuration
sudo -u ntp-monitor cat .env
```

### **Si ntpsec ne fonctionne pas**
```bash
# Vérifier le service
sudo systemctl status ntpsec
sudo systemctl restart ntpsec

# Vérifier la synchronisation
ntpq -c peers
ntpq -c associations

# Vérifier les conflits
sudo systemctl status chronyd
sudo systemctl status systemd-timesyncd

# Restaurer sauvegarde si nécessaire
ls -la /root/ntpsec_backup/
```

### **Si MySQL a des problèmes**
```bash
# Vérifier MySQL
sudo systemctl status mysql
sudo mysql -u root

# Vérifier utilisateur application
mysql -u ntp_user -p$(grep MYSQL_PASSWORD /root/mysql_credentials.txt | cut -d'=' -f2)

# Réinitialiser mot de passe si nécessaire
sudo mysql -u root
ALTER USER 'ntp_user'@'localhost' IDENTIFIED BY 'nouveau_mot_de_passe';
```

## ⚡ **Optimisations**

### **Pour serveur de production**
```bash
# Modifier les variables dans le script
DOMAIN="votre-domaine.com"  # Au lieu de l'IP
MYSQL_DB="ntp_monitor_prod"
```

### **Pour SSL/HTTPS**
```bash
# Après déploiement
sudo certbot --apache -d votre-domaine.com
```

### **Pour plus de sécurité**
```bash
# Changer mot de passe admin par défaut
# Via l'interface web: Profil → Changer mot de passe
```

## 📈 **Fonctionnalités NTP Monitor**

### **Monitoring temps réel**
```bash
✅ 8 serveurs NTP simultanés
✅ Graphiques interactifs (Chart.js)
✅ Alertes WebSocket temps réel
✅ Historique et tendances
✅ Métriques détaillées (offset, delay, jitter)
```

### **Multi-utilisateurs**
```bash
✅ Rôles: Admin, Operator, Viewer
✅ Permissions granulaires
✅ Sessions sécurisées
✅ Logs d'activité
```

### **API REST**
```bash
✅ Endpoints complets
✅ Authentification JWT
✅ Export données JSON
✅ Intégration externe
```

## 🎉 **Avantages du Script Unifié**

1. **🔍 Détection intelligente** : Adapte automatiquement selon l'environnement
2. **⚡ Préservation** : Maintient les configurations existantes (ntpsec)
3. **🛡️ Sécurité** : Configuration sécurisée par défaut
4. **📊 Monitoring** : Surveillance automatique 24/7
5. **🔧 Maintenance** : Nettoyage et redémarrage automatiques
6. **📋 Validation** : Tests complets post-déploiement
7. **📖 Documentation** : Informations complètes affichées

## 🤝 **Support**

Si vous rencontrez des problèmes :

1. **Vérifiez les logs** : `sudo journalctl -u ntp-monitor-enterprise -f`
2. **Consultez le monitoring** : `tail -f /home/ntp-monitor/logs/monitoring.log`
3. **Relancez le script** : Il est idempotent et peut être relancé
4. **Vérifiez les prérequis** : Le script affiche les erreurs explicites

---

## 📝 **Changelog**

### Version 2.1.0 (Janvier 2025)
- ✅ Script de déploiement unifié
- ✅ Détection automatique Python/ntpsec
- ✅ Préservation configurations existantes
- ✅ Configuration port 80 optimisée
- ✅ Monitoring automatique intégré
- ✅ Gestion erreurs robuste
- ✅ Support Ubuntu 24.04 natif 