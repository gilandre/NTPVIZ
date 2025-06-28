# NTP Monitor Enterprise v1.0 - Guide de Déploiement

## 🎯 Vue d'ensemble

**NTP Monitor Enterprise** est une application web professionnelle de monitoring NTP temps réel développée spécifiquement pour Ubuntu 24.04 avec Apache 2.4.

### Fonctionnalités principales
- ✅ **Monitoring simultané** de 5 serveurs NTP (3 mondiaux + 2 locaux configurables)
- ✅ **Interface d'administration** pour configuration dynamique des serveurs
- ✅ **Système d'alertes** intelligent avec notifications temps réel
- ✅ **Monitoring des clients NTP** connectés au serveur local
- ✅ **Dashboard temps réel** avec WebSocket
- ✅ **Authentification sécurisée** multi-rôles
- ✅ **API REST complète** pour intégrations externes

---

## 📋 Prérequis

### Système requis
- **OS :** Ubuntu 24.04 LTS
- **RAM :** 2 GB minimum, 4 GB recommandé
- **Stockage :** 10 GB d'espace libre
- **Réseau :** Accès Internet pour synchronisation NTP

### Services requis
- Apache 2.4
- Python 3.11
- Redis Server
- NTPsec (service NTP)

---

## 🚀 Installation Automatique

### 1. Télécharger et préparer
```bash
# Cloner ou copier les fichiers de l'application
sudo cp -r ntp-monitor-enterprise /tmp/

# Rendre le script exécutable
chmod +x /tmp/ntp-monitor-enterprise/deployment/scripts/install.sh
```

### 2. Lancer l'installation
```bash
# Exécuter l'installation complète (en tant que root)
sudo /tmp/ntp-monitor-enterprise/deployment/scripts/install.sh
```

### 3. Vérification
```bash
# Vérifier les services
sudo systemctl status apache2 redis-server ntpsec

# Test de connectivité
curl http://localhost
# ou 
curl http://$(hostname -I | awk '{print $1}')
```

---

## 🔐 Première Connexion

### Accès à l'application
- **URL :** `http://votre-serveur` ou `http://localhost`
- **Utilisateur :** `admin`
- **Mot de passe :** `admin123`

### ⚠️ SÉCURITÉ IMPORTANTE
**Changez immédiatement le mot de passe administrateur après la première connexion !**

---

## ⚙️ Configuration Post-Installation

### 1. Configuration des serveurs NTP locaux
1. Connectez-vous en tant qu'administrateur
2. Allez dans **Administration** → **Gestion des serveurs**
3. Modifiez les serveurs "Serveur Local 1" et "Serveur Local 2"
4. Remplacez les adresses par vos serveurs NTP locaux réels

### 2. Configuration des seuils d'alerte
1. Allez dans **Configuration** → **Paramètres NTP**
2. Ajustez les seuils selon vos besoins :
   - **Seuil d'avertissement :** 1.0 seconde (par défaut)
   - **Seuil critique :** 5.0 secondes (par défaut)

### 3. Création d'utilisateurs supplémentaires
1. Allez dans **Administration** → **Gestion des utilisateurs**
2. Créez des comptes selon les rôles :
   - **Admin :** Accès complet
   - **Operator :** Configuration et monitoring
   - **Viewer :** Consultation uniquement

---

## 📊 Utilisation de l'Interface

### Dashboard Principal
- **Vue d'ensemble :** Statistiques globales des serveurs
- **Horloges temps réel :** Affichage des 5 serveurs NTP
- **Graphiques :** Évolution des écarts de synchronisation
- **Alertes :** Notifications en temps réel
- **Monitoring clients :** Statistiques des connexions

### Fonctionnalités Avancées
- **Actualisation automatique :** Mise à jour toutes les 30 secondes
- **Notifications WebSocket :** Alertes instantanées
- **Historique :** Logs et statistiques sur 24h/7j/30j
- **Export :** Données au format JSON via API

---

## 🔧 Administration et Maintenance

### Commandes utiles
```bash
# Redémarrer l'application
sudo systemctl restart apache2

# Voir les logs en temps réel
sudo tail -f /var/log/apache2/ntp-monitor_error.log
sudo tail -f /var/www/ntp-monitor-enterprise/logs/app.log

# Status des services
sudo systemctl status apache2 redis-server ntpsec

# Backup de la base de données
sudo cp /var/www/ntp-monitor-enterprise/ntp_monitor_prod.db /backup/
```

### Fichiers importants
- **Configuration Apache :** `/etc/apache2/sites-available/ntp-monitor.conf`
- **Application :** `/var/www/ntp-monitor-enterprise/`
- **Base de données :** `/var/www/ntp-monitor-enterprise/ntp_monitor_prod.db`
- **Logs :** `/var/www/ntp-monitor-enterprise/logs/`

### Mise à jour de l'application
```bash
# Sauvegarder la base de données
sudo cp /var/www/ntp-monitor-enterprise/ntp_monitor_prod.db /backup/

# Arrêter Apache
sudo systemctl stop apache2

# Remplacer les fichiers (conservez la DB et les logs)
# ... mise à jour des fichiers ...

# Redémarrer Apache
sudo systemctl start apache2
```

---

## 📡 API REST

### Endpoints principaux
- **Santé :** `GET /health`
- **Serveurs :** `GET /api/servers`
- **Dashboard :** `GET /api/dashboard/summary`
- **Temps réel :** `GET /api/dashboard/realtime`
- **Statistiques :** `GET /api/servers/{id}/stats`

### Authentification API
```bash
# Exemple avec curl
curl -u "admin:admin123" http://localhost/api/servers
```

---

## 🔔 Alertes et Notifications

### Types d'alertes
- **Écart de synchronisation :** Quand l'offset dépasse les seuils
- **Serveur hors ligne :** Quand un serveur ne répond plus
- **Connectivité :** Problèmes réseau

### Configuration des notifications
1. Allez dans **Administration** → **Configuration système**
2. Activez les notifications email ou webhook
3. Configurez les paramètres SMTP ou URL webhook

---

## 🛠️ Dépannage

### Problèmes courants

#### Application inaccessible
```bash
# Vérifier Apache
sudo systemctl status apache2
sudo apache2ctl configtest

# Vérifier les logs
sudo tail -f /var/log/apache2/error.log
```

#### Erreurs de base de données
```bash
# Vérifier les permissions
sudo chown -R ntpmonitor:www-data /var/www/ntp-monitor-enterprise/
sudo chmod 775 /var/www/ntp-monitor-enterprise/logs/
```

#### Problèmes WebSocket
```bash
# Vérifier la configuration proxy
sudo a2enmod proxy proxy_http proxy_wstunnel
sudo systemctl restart apache2
```

---

## 🚨 Sécurité

### Recommandations de sécurité
1. **Changez les mots de passe par défaut**
2. **Configurez HTTPS avec SSL**
3. **Utilisez un firewall (UFW)**
4. **Mettez à jour régulièrement le système**
5. **Surveillez les logs d'accès**

### Configuration HTTPS (optionnel)
```bash
# Générer un certificat SSL
sudo certbot --apache -d votre-domaine.com

# Ou utiliser un certificat auto-signé pour test
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/ntp-monitor.key \
  -out /etc/ssl/certs/ntp-monitor.crt
```

---

## 📞 Support

### Logs de diagnostic
```bash
# Créer un package de diagnostic
sudo tar -czf ntp-monitor-diagnostic.tar.gz \
  /var/log/apache2/ntp-monitor*.log \
  /var/www/ntp-monitor-enterprise/logs/ \
  /etc/apache2/sites-available/ntp-monitor.conf
```

### Informations système
- **Version :** NTP Monitor Enterprise v1.0
- **Compatibilité :** Ubuntu 24.04 + Apache 2.4
- **Technologies :** Python 3.11, Flask, SQLite, Redis
- **Licence :** Propriétaire

---

## 🎉 Félicitations !

Votre application **NTP Monitor Enterprise** est maintenant opérationnelle !

- 🔗 **Interface web :** http://votre-serveur
- 👤 **Admin :** admin / admin123 
- 📊 **Dashboard :** Monitoring temps réel
- ⚡ **Performances :** Optimisé pour production

**N'oubliez pas de changer le mot de passe administrateur !** 