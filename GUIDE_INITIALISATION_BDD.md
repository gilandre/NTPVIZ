# Guide d'Initialisation de la Base de Données

## 🚀 NTP Monitor Enterprise - Initialisation BDD

Ce guide explique comment initialiser la base de données pour **NTP Monitor Enterprise** avec toutes les données de base nécessaires.

---

## 📋 Prérequis

- Python 3.8+ installé
- Environnement virtuel activé
- Dépendances installées (`pip install -r requirements.txt`)

---

## 🛠️ Script d'Initialisation

Le projet inclut un script d'initialisation automatique : `init_database.py`

### Commandes Disponibles

```bash
# Initialisation standard avec données de base
python init_database.py init

# Vérification de l'état de la BDD
python init_database.py check

# Initialisation + données d'exemple pour développement
python init_database.py sample

# Réinitialisation complète (ATTENTION: supprime tout!)
python init_database.py reset
```

---

## 🎯 Initialisation Rapide

### Première Installation

```bash
# 1. Cloner le projet
git clone https://github.com/votre-repo/ntp-monitor-enterprise.git
cd ntp-monitor-enterprise

# 2. Créer l'environnement virtuel
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate     # Linux/Mac

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Initialiser la base de données
python init_database.py init

# 5. Démarrer l'application
python app.py
```

### Mise à Jour d'une Installation Existante

```bash
# 1. Mettre à jour le code
git pull origin main

# 2. Vérifier l'état de la BDD
python init_database.py check

# 3. Si nécessaire, mettre à jour la BDD
python init_database.py init
```

---

## 📊 Données Initialisées

Le script d'initialisation créé automatiquement :

### 👤 Utilisateurs par Défaut

- **Administrateur** : `admin` / `admin123`
  - Accès complet à toutes les fonctionnalités
  - Gestion des utilisateurs et configurations

### 🌐 Serveurs NTP par Défaut

- **Pool France** : `0.fr.pool.ntp.org`
- **Pool Europe** : `1.europe.pool.ntp.org`
- **Pool Global** : `2.pool.ntp.org`
- **Serveur Backup** : `3.pool.ntp.org`

### ⚙️ Configuration Système

- Monitoring activé par défaut
- Intervalle de requête : 60 secondes
- Seuils d'alerte configurés
- Rétention des logs : 30 jours

---

## 🔧 Initialisation Manuelle

Si vous préférez initialiser manuellement :

### 1. Création des Tables

```python
from backend.app import create_app, db
app = create_app()

with app.app_context():
    db.create_all()
```

### 2. Initialisation des Données

```python
from backend.utils.init_data import init_default_data
with app.app_context():
    init_default_data()
```

---

## 🧪 Mode Développement

Pour créer des données d'exemple supplémentaires :

```bash
# Initialisation + données d'exemple
python init_database.py sample
```

Cela ajoute :
- Utilisateurs de test supplémentaires
- Logs NTP d'exemple
- Alertes d'exemple
- Données de monitoring simulées

---

## 🛡️ Sécurité

### Première Connexion

1. Connectez-vous avec : `admin` / `admin123`
2. **CHANGEZ IMMÉDIATEMENT** le mot de passe par défaut
3. Créez vos utilisateurs personnalisés
4. Désactivez l'utilisateur admin par défaut si nécessaire

### Réinitialisation Sécurisée

Le script inclut des protections :
- Confirmation obligatoire pour la réinitialisation
- Sauvegarde automatique des données existantes
- Logs détaillés de toutes les opérations

---

## 🔍 Vérification

### Vérifier l'État de la BDD

```bash
python init_database.py check
```

### Logs d'Initialisation

Les logs sont sauvegardés dans :
- Console : Affichage en temps réel
- Fichier : `logs/app.log`

### Test de Connexion

```bash
# Démarrer l'application
python app.py

# Accéder à l'interface
# http://localhost:5000
```

---

## 🐛 Dépannage

### Erreur "No module named 'backend'"

```bash
# Vérifier que vous êtes dans le bon répertoire
ls -la  # Doit afficher app.py, backend/, etc.

# Vérifier l'environnement virtuel
python -c "import sys; print(sys.path)"
```

### Erreur "Database is locked"

```bash
# Arrêter l'application
# Supprimer le fichier journal SQLite
rm instance/ntp_monitor_dev.db-journal

# Relancer l'initialisation
python init_database.py init
```

### Erreur "Working outside of application context"

```bash
# Utiliser le script d'initialisation (recommandé)
python init_database.py init

# Ou démarrer l'application normalement
python app.py
```

---

## 📚 Structure de la Base de Données

### Tables Principales

- `user` : Utilisateurs et authentification
- `ntp_server` : Serveurs NTP configurés
- `ntp_log` : Logs des requêtes NTP
- `alert` : Système d'alertes
- `system_config` : Configuration système

### Relations

- Un utilisateur peut avoir plusieurs alertes
- Un serveur NTP peut avoir plusieurs logs
- Les alertes sont liées aux serveurs NTP
- La configuration est globale

---

## 🚀 Automatisation

### Script de Déploiement

Pour automatiser l'initialisation dans un environnement de production :

```bash
#!/bin/bash
# deploy.sh

# Installation des dépendances
pip install -r requirements.txt

# Initialisation de la BDD
python init_database.py init

# Démarrage de l'application
python app.py
```

### Variables d'Environnement

```bash
# Configuration automatique
export FLASK_ENV=production
export DATABASE_URL=sqlite:///instance/ntp_monitor_prod.db
export SECRET_KEY=votre-clé-secrète

# Initialisation
python init_database.py init
```

---

## 📞 Support

En cas de problème :
1. Vérifiez les logs : `logs/app.log`
2. Consultez la section dépannage
3. Réinitialisez si nécessaire : `python init_database.py reset`

---

**✅ Votre base de données est maintenant prête !**

🌐 Accédez à l'application : http://localhost:5000  
🔐 Connexion : admin / admin123  
📊 Profitez de votre monitoring NTP ! 