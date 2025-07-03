# NTP Monitor Enterprise - Installation Rapide Ubuntu 24.04

## 🚀 Installation en Une Commande

### Méthode 1 : Installation Ultra-Rapide (Recommandée)

```bash
curl -fsSL https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/install_ntp_monitor.sh | sudo bash
```

### Méthode 2 : Installation avec Script Interactif

```bash
curl -fsSL https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/quick_install_ubuntu24.sh | sudo bash
```

### Méthode 3 : Téléchargement puis Exécution

```bash
# Télécharger le script d'installation
wget https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/quick_install_ubuntu24.sh

# Rendre exécutable
chmod +x quick_install_ubuntu24.sh

# Exécuter
sudo ./quick_install_ubuntu24.sh
```

### Méthode 4 : Script de Dépendances Seulement

```bash
# Télécharger le vérificateur de dépendances
wget https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/dependencies_checker_ubuntu24_final.sh

# Rendre exécutable
chmod +x dependencies_checker_ubuntu24_final.sh

# Exécuter
sudo ./dependencies_checker_ubuntu24_final.sh
```

## 📋 Prérequis

- **Système** : Ubuntu 24.04 LTS (compatible 22.04+)
- **Privilèges** : Accès root (sudo)
- **Connexion** : Internet active
- **Ressources** : 1GB RAM minimum, 5GB disque libre

## ⚡ Ce que font les scripts

### 1. Vérification Système
- ✅ Version Ubuntu compatible
- ✅ Ressources suffisantes (RAM/Disque)
- ✅ Privilèges root

### 2. Installation Packages (39 packages)
- ✅ Outils système (curl, wget, git, htop, vim, etc.)
- ✅ Python 3.11+ avec pip, venv, dev headers
- ✅ MySQL Server + Client + Headers
- ✅ Apache 2 + mod_wsgi + modules SSL
- ✅ Redis Server pour cache/sessions
- ✅ NTP + outils de synchronisation
- ✅ Certbot pour SSL/TLS
- ✅ UFW Firewall

### 3. Configuration Services
- ✅ MySQL : Base `ntp_monitor` + utilisateur `ntp_user`
- ✅ Apache : Modules wsgi, rewrite, ssl, headers
- ✅ Redis : Cache et sessions
- ✅ NTP : Synchronisation temporelle
- ✅ UFW : Ports 22, 80, 443, 123

### 4. Installation Python (25+ packages)
- ✅ Flask 2.3.3 + Extensions
- ✅ SQLAlchemy 2.0.21
- ✅ PyMySQL 1.1.0
- ✅ Redis client 5.0.1
- ✅ WebSocket support
- ✅ Cryptographie + sécurité

### 5. Tests Finaux
- ✅ MySQL opérationnel
- ✅ Apache actif avec modules
- ✅ Redis fonctionnel
- ✅ Python avec toutes les dépendances
- ✅ Connectivité réseau

## 📊 Après Installation

### Credentials MySQL
```bash
# Voir le mot de passe généré
sudo cat /root/mysql_credentials.txt
```

### Vérifier les Services
```bash
# Status des services principaux
sudo systemctl status mysql apache2 redis-server ntp

# Logs en temps réel
sudo journalctl -f -u mysql
sudo tail -f /var/log/apache2/error.log
```

### Test de Connectivité
```bash
# Test web local
curl -I http://localhost

# Test MySQL
mysql -u ntp_user -p -e "SHOW DATABASES;"
```

## 🔥 Déploiement Complet

Après l'installation des dépendances :

```bash
# 1. Cloner le projet complet
git clone https://github.com/gilandre/NTPVIZ.git
cd NTPVIZ

# 2. Lancer le déploiement
sudo ./deploy_ubuntu_production.sh

# 3. Configurer SSL (optionnel)
sudo certbot --apache -d votre-domaine.com
```

## 🛠️ Dépannage

### Problème de Caractères UTF-8
Les scripts incluent un auto-nettoyage des caractères problématiques.

### Échec d'Installation
```bash
# Vérifier les logs
sudo journalctl -xe

# Vérifier l'espace disque
df -h

# Vérifier la mémoire
free -h

# Relancer l'installation
sudo ./dependencies_checker_ubuntu24_final.sh
```

### Services Inactifs
```bash
# Redémarrer les services
sudo systemctl restart mysql apache2 redis-server

# Vérifier les erreurs
sudo systemctl status --failed
```

## 📞 Support

- **Logs Application** : `/var/log/apache2/ntp-monitor_error.log`
- **Logs MySQL** : `/var/log/mysql/error.log`
- **Credentials** : `/root/mysql_credentials.txt`
- **Configuration** : Fichier `.env` dans le répertoire de l'application

## 🎯 Ports Configurés

- **SSH** : 22 (ouvert)
- **HTTP** : 80 (ouvert)
- **HTTPS** : 443 (ouvert)
- **NTP** : 123/udp (ouvert)

## ✅ Validation Finale

Votre serveur est prêt quand vous voyez :

```
🎉 INSTALLATION COMPLETE ET REUSSIE !
Systeme Ubuntu 24.04 pret pour NTP Monitor Enterprise
```

**Version des scripts** : 2.0.1-final  
**Dernière mise à jour** : 2025-01-07 