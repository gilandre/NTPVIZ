# 📋 Résumé des Scripts de Déploiement - NTP Monitor Enterprise

## 🎯 Vue d'ensemble

Ce document résume tous les scripts de déploiement créés pour NTP Monitor Enterprise, incluant les corrections de schéma de base de données et l'harmonisation des modèles.

## 📁 Structure des scripts

### Scripts principaux de déploiement

#### 1. `deployment/scripts/deploy_ubuntu_complete.sh`
**Fonction** : Déploiement complet automatique sur Ubuntu 24.04
**Fonctionnalités** :
- ✅ Installation automatique des packages système
- ✅ Configuration MySQL automatique
- ✅ Téléchargement depuis GitHub (branche MacDev)
- ✅ Configuration de l'environnement Python
- ✅ Correction automatique du schéma de base de données
- ✅ Harmonisation des modèles
- ✅ Initialisation de la base de données
- ✅ Configuration du service systemd
- ✅ Configuration du firewall
- ✅ Vérification finale du déploiement

**Utilisation** :
```bash
wget https://raw.githubusercontent.com/gilandre/NTPVIZ/MacDev/deployment/scripts/deploy_ubuntu_complete.sh
chmod +x deploy_ubuntu_complete.sh
./deploy_ubuntu_complete.sh
```

#### 2. `deployment/scripts/update_deployment.sh`
**Fonction** : Mise à jour automatique du déploiement existant
**Fonctionnalités** :
- ✅ Sauvegarde automatique avant mise à jour
- ✅ Mise à jour depuis GitHub
- ✅ Mise à jour des dépendances Python
- ✅ Correction du schéma et harmonisation
- ✅ Redémarrage du service
- ✅ Rollback en cas de problème

**Utilisation** :
```bash
wget https://raw.githubusercontent.com/gilandre/NTPVIZ/MacDev/deployment/scripts/update_deployment.sh
chmod +x update_deployment.sh
./update_deployment.sh
```

### Scripts de correction de base de données

#### 3. `fix_database_schema.py`
**Fonction** : Correction automatique du schéma de base de données
**Problèmes résolus** :
- ✅ Ajout des colonnes manquantes dans `users` :
  - `last_login` (DATETIME NULL)
  - `login_count` (INT DEFAULT 0)
  - `preferences` (TEXT NULL)
  - `deleted_at` (DATETIME NULL)
  - `deleted_by` (INT NULL)
- ✅ Ajout des colonnes manquantes dans `ntp_servers` :
  - `server_type` (VARCHAR(20) NOT NULL DEFAULT 'global')
  - `last_delay` (FLOAT NULL)
  - `deleted_at` (DATETIME NULL)
  - `deleted_by` (INT NULL)
  - `max_offset` (FLOAT DEFAULT 1.0)
  - `critical_offset` (FLOAT DEFAULT 5.0)

**Utilisation** :
```bash
python fix_database_schema.py
```

#### 4. `harmonize_models.py`
**Fonction** : Harmonisation des modèles et suppression des redondances
**Actions** :
- ✅ Suppression du fichier redondant `ntp_server_logical_delete.py`
- ✅ Mise à jour du fichier `__init__.py` des modèles
- ✅ Vérification de la cohérence des modèles
- ✅ Test des modèles avec la base de données

**Utilisation** :
```bash
python harmonize_models.py
```

### Scripts de vérification

#### 5. `verify_deployment_scripts.py`
**Fonction** : Vérification complète de tous les scripts de déploiement
**Vérifications** :
- ✅ Existence de tous les fichiers requis
- ✅ Syntaxe valide des scripts Bash et Python
- ✅ Configuration de l'environnement
- ✅ Cohérence des modèles de base de données
- ✅ Complétude du guide de déploiement

**Utilisation** :
```bash
python verify_deployment_scripts.py
```

## 🔧 Scripts de support existants

### Scripts de dépannage
- `deployment/scripts/quick-debug.sh` : Diagnostic rapide
- `deployment/scripts/debug-500-advanced.sh` : Diagnostic avancé des erreurs 500
- `deployment/scripts/fix-apache-500-error.sh` : Correction des erreurs Apache
- `deployment/scripts/fix-flask-login-werkzeug.sh` : Correction des problèmes Flask-Login
- `deployment/scripts/fix-python312-setuptools.sh` : Correction Python 3.12

### Scripts de déploiement existants
- `deployment/scripts/deploy.sh` : Script de déploiement original
- `deployment/scripts/install.sh` : Script d'installation
- `deployment/scripts/quick-deploy.sh` : Déploiement rapide

### Scripts de vérification
- `deployment/scripts/verify_ubuntu_24.04.sh` : Vérification Ubuntu 24.04
- `deployment/scripts/test-python-detection.sh` : Test de détection Python
- `deployment/scripts/web-logs-viewer.sh` : Visualiseur de logs web

## 📊 Statistiques des corrections

### Problèmes résolus
1. **Erreur `Unknown column 'users.last_login'`** ✅
2. **Erreur `Unknown column 'ntp_servers.server_type'`** ✅
3. **Incohérences entre modèles** ✅
4. **Fichiers redondants** ✅
5. **Configuration manquante** ✅

### Colonnes ajoutées
- **Table `users`** : 5 colonnes ajoutées
- **Table `ntp_servers`** : 6 colonnes ajoutées

### Fichiers supprimés
- `backend/models/ntp_server_logical_delete.py` (redondant)

## 🚀 Procédure de déploiement recommandée

### Pour un nouveau serveur Ubuntu 24.04

```bash
# 1. Télécharger et exécuter le script de déploiement complet
wget https://raw.githubusercontent.com/gilandre/NTPVIZ/MacDev/deployment/scripts/deploy_ubuntu_complete.sh
chmod +x deploy_ubuntu_complete.sh
./deploy_ubuntu_complete.sh

# 2. Vérifier le déploiement
python verify_deployment_scripts.py
```

### Pour mettre à jour un déploiement existant

```bash
# 1. Télécharger et exécuter le script de mise à jour
wget https://raw.githubusercontent.com/gilandre/NTPVIZ/MacDev/deployment/scripts/update_deployment.sh
chmod +x update_deployment.sh
./update_deployment.sh

# 2. En cas de problème, effectuer un rollback
./update_deployment.sh rollback
```

## 🛠️ Commandes de gestion

### Service systemd
```bash
sudo systemctl status ntp-monitor    # Voir le statut
sudo systemctl restart ntp-monitor   # Redémarrer
sudo systemctl stop ntp-monitor      # Arrêter
sudo journalctl -u ntp-monitor -f   # Voir les logs
```

### Scripts de déploiement
```bash
./deploy_ubuntu_complete.sh logs     # Voir les logs
./deploy_ubuntu_complete.sh restart  # Redémarrer
./deploy_ubuntu_complete.sh status   # Statut
./deploy_ubuntu_complete.sh test     # Test de l'application

./update_deployment.sh rollback      # Rollback
```

## 📈 Monitoring et maintenance

### Vérification quotidienne
```bash
# Vérifier le statut du service
sudo systemctl status ntp-monitor

# Vérifier l'accessibilité
curl -s http://localhost:5001/ | head -5

# Vérifier les logs récents
sudo journalctl -u ntp-monitor -n 20
```

### Nettoyage des sauvegardes
```bash
# Supprimer les sauvegardes anciennes (plus de 7 jours)
find /opt/ntp-monitor-backup-* -type d -mtime +7 -exec rm -rf {} \;
```

## 🎯 Accès à l'application

### Informations de connexion
- **URL** : `http://votre-serveur-ip:5001`
- **Utilisateur** : `admin`
- **Mot de passe** : `admin123`

### Utilisateurs par défaut
- `admin` : Administrateur complet
- `operator` : Opérateur avec permissions limitées
- `viewer` : Lecteur uniquement

## ✅ Validation finale

Tous les scripts ont été testés et validés avec le script `verify_deployment_scripts.py` qui confirme :

- ✅ **Tous les fichiers requis** sont présents
- ✅ **Tous les scripts** ont une syntaxe valide
- ✅ **Configuration d'environnement** complète
- ✅ **Modèles de base de données** cohérents
- ✅ **Guide de déploiement** complet

## 🎉 Conclusion

Le système de déploiement est maintenant **complet et robuste** avec :

- 🔄 **Déploiement automatique** depuis GitHub
- 🔧 **Correction automatique** des problèmes de schéma
- 🛡️ **Sauvegarde et rollback** automatiques
- 📊 **Monitoring et maintenance** intégrés
- 📚 **Documentation complète** fournie

L'application NTP Monitor Enterprise est prête pour le déploiement en production sur Ubuntu 24.04 ! 