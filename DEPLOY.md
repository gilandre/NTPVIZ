# 🚀 Guide de Déploiement - NTP Monitor Enterprise

Guide simple pour déployer et mettre à jour NTP Monitor Enterprise sur le serveur 79.137.36.66.

## 📋 Prérequis

- Serveur Ubuntu/Debian avec accès SSH
- Accès root ou sudo
- Connexion Internet
- MySQL installé

## 🔧 Installation Initiale

### 1. Installation sur le serveur

```bash
# Connectez-vous au serveur
ssh root@79.137.36.66

# Clonez le dépôt
git clone -b dev https://github.com/YOUR_USERNAME/NTP_PROJECT.git /opt/ntp-monitor
cd /opt/ntp-monitor

# Exécutez l'installation
chmod +x deployment/scripts/install.sh
./deployment/scripts/install.sh
```

### 2. Configuration personnalisée (optionnel)

```bash
# Éditez la configuration si nécessaire
nano /opt/ntp-monitor/.env
```

## 🔄 Mise à Jour en Une Commande

Une fois l'installation initiale effectuée, utilisez ce script pour mettre à jour l'application :

```bash
# Depuis votre machine locale
chmod +x deploy.sh
./deploy.sh
```

**C'est tout !** Le script va automatiquement :
- Se connecter au serveur 79.137.36.66
- Arrêter l'application
- Sauvegarder la configuration
- Télécharger les dernières mises à jour GitHub
- Mettre à jour les dépendances
- Redémarrer l'application
- Vérifier que tout fonctionne

## 🎯 Configuration Par Défaut

| Paramètre | Valeur |
|-----------|--------|
| **Serveur** | 79.137.36.66 |
| **Port** | 5000 |
| **Répertoire** | /opt/ntp-monitor |
| **Service** | ntp-monitor |
| **Base de données** | MySQL (ntp_monitor) |

## 👤 Identifiants Par Défaut

| Utilisateur | Mot de passe | Rôle |
|-------------|--------------|------|
| admin | admin123 | Administrateur |
| operator | operator123 | Opérateur |
| viewer | viewer123 | Visualiseur |

⚠️ **Changez ces mots de passe après la première connexion !**

## 📝 Commandes Utiles

```bash
# Statut du service
ssh root@79.137.36.66 'systemctl status ntp-monitor'

# Logs en temps réel
ssh root@79.137.36.66 'journalctl -u ntp-monitor -f'

# Redémarrage manuel
ssh root@79.137.36.66 'systemctl restart ntp-monitor'

# Vérification de l'application
curl http://79.137.36.66:5000/api/system/status
```

## 🔧 Personnalisation du Déploiement

Pour déployer sur un autre serveur ou avec des paramètres différents :

```bash
# Serveur différent
./deploy.sh user@autre-serveur.com

# Répertoire différent
./deploy.sh user@serveur.com /chemin/vers/app

# Service différent
./deploy.sh user@serveur.com /opt/app mon-service
```

## 🛠️ Dépannage

### Application non accessible
```bash
# Vérifiez le service
ssh root@79.137.36.66 'systemctl status ntp-monitor'

# Vérifiez les logs
ssh root@79.137.36.66 'journalctl -u ntp-monitor --since "5 minutes ago"'

# Vérifiez le port
ssh root@79.137.36.66 'netstat -tlnp | grep 5000'
```

### Base de données
```bash
# Connexion MySQL
ssh root@79.137.36.66 'mysql -u ntp_monitor -p ntp_monitor'

# Vérification des tables
ssh root@79.137.36.66 'mysql -u ntp_monitor -p -e "SHOW TABLES;" ntp_monitor'
```

### Réinitialisation complète
```bash
ssh root@79.137.36.66 'systemctl stop ntp-monitor'
ssh root@79.137.36.66 'rm -rf /opt/ntp-monitor'
# Puis relancez l'installation
```

## 📊 Monitoring

- **Application** : http://79.137.36.66:5000
- **API Health** : http://79.137.36.66:5000/api/system/status
- **Logs** : `journalctl -u ntp-monitor -f`

## 🔐 Sécurité

- L'application utilise HTTPS en production
- Les mots de passe sont hashés (bcrypt)
- Les sessions sont sécurisées
- Le pare-feu autorise uniquement les ports nécessaires

---

**🎉 C'est tout ! Votre application NTP Monitor Enterprise est maintenant déployée et prête à l'emploi.** 