# 🚀 NTP Monitor Enterprise - Branche MacDev

## 📋 Vue d'ensemble

Cette branche contient la version stabilisée et optimisée de NTP Monitor Enterprise, prête pour la production sur Ubuntu 24.04.

## ✅ Fonctionnalités principales

### 🔧 Modal d'Administration
- **Interface complète** : Gestion des utilisateurs, serveurs, statistiques
- **Navigation fluide** : Vue d'ensemble, utilisateurs, serveurs, audit, alertes
- **Données temps réel** : Mise à jour automatique des statistiques
- **Gestion des alertes** : Historique et configuration des seuils

### 📊 Monitoring NTP
- **Serveurs multiples** : Support des serveurs locaux et globaux
- **Métriques temps réel** : Offset, latence, stratum, disponibilité
- **Alertes intelligentes** : Seuils configurables par type de serveur
- **Interface responsive** : Compatible desktop et mobile

### 🔐 Sécurité et Authentification
- **Système de rôles** : Admin, Operator, Viewer
- **Gestion des sessions** : Sécurisée avec Flask-Login
- **Audit trail** : Logs complets des actions utilisateurs

## 🛠️ Installation

### Prérequis
- Ubuntu 24.04 (recommandé) ou macOS
- Python 3.9+
- MySQL 8.0+
- Git

### Installation rapide
```bash
# Cloner le projet
git clone https://github.com/votre-repo/NTPVIZ.git
cd NTPVIZ

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp env.example .env
# Éditer .env avec vos paramètres

# Initialiser la base de données
python initialiser_database.py

# Démarrer l'application
python app.py
```

### Déploiement production Ubuntu 24.04
```bash
# Script de déploiement automatique
wget -O - https://raw.githubusercontent.com/votre-repo/NTPVIZ/MacDev/deployment/scripts/deploy.sh | sudo bash
```

## 🔧 Configuration

### Variables d'environnement (.env)
```bash
FLASK_ENV=production
DATABASE_URL=mysql://user:password@localhost/ntp_monitor
SECRET_KEY=votre-clé-secrète
HOST=0.0.0.0
PORT=5001
DEBUG=False
```

### Base de données
L'application utilise MySQL avec les tables suivantes :
- `users` : Utilisateurs et rôles
- `ntp_servers` : Serveurs NTP configurés
- `ntp_logs` : Logs de monitoring
- `alerts` : Alertes générées
- `system_config` : Configuration système

## 📁 Structure du projet

```
NTPVIZ/
├── app.py                 # Point d'entrée principal
├── requirements.txt       # Dépendances Python
├── backend/              # Backend Flask
│   ├── api/             # Endpoints API
│   ├── models/          # Modèles de données
│   ├── services/        # Services métier
│   └── utils/           # Utilitaires
├── frontend/            # Interface utilisateur
│   ├── static/          # CSS, JS, images
│   └── templates/       # Templates HTML
├── config/              # Configuration
├── deployment/          # Scripts de déploiement
└── scripts/             # Scripts utilitaires
```

## 🚀 Démarrage

### Développement
```bash
python app.py
```
L'application sera accessible sur `http://localhost:5001`

### Production
```bash
# Utiliser systemd
sudo systemctl start ntp-monitor
sudo systemctl enable ntp-monitor
```

## 👥 Utilisateurs par défaut

- **Administrateur** : `admin` / `admin123`
- **Opérateur** : `operator` / `operator123`
- **Lecteur** : `viewer` / `viewer123`

⚠️ **Important** : Changez les mots de passe après la première connexion !

## 🔍 Dépannage

### Problèmes courants

1. **Erreur de connexion à la base de données**
   ```bash
   # Vérifier MySQL
   sudo systemctl status mysql
   
   # Vérifier les credentials dans .env
   mysql -u ntp_user -p
   ```

2. **Modal d'administration ne se charge pas**
   ```bash
   # Vérifier les logs
   tail -f logs/app.log
   
   # Vérifier les endpoints API
   curl http://localhost:5001/api/admin/stats
   ```

3. **Monitoring NTP ne fonctionne pas**
   ```bash
   # Vérifier la configuration des serveurs
   python -c "from backend.services.ntp_service import ntp_service; print(ntp_service.get_servers())"
   ```

### Logs
Les logs sont disponibles dans :
- `logs/app.log` : Logs de l'application
- `logs/ntp_monitor.log` : Logs du monitoring NTP

## 📈 Monitoring et Métriques

### Métriques disponibles
- **Offset** : Déviation temporelle (ms)
- **Latence** : Temps de réponse réseau (ms)
- **Stratum** : Niveau de synchronisation
- **Disponibilité** : Pourcentage de temps en ligne

### Alertes configurables
- Seuils d'avertissement et critiques
- Par type de serveur (local/global)
- Notifications en temps réel

## 🔄 Mise à jour

```bash
# Mettre à jour depuis la branche MacDev
git pull origin MacDev

# Redémarrer l'application
sudo systemctl restart ntp-monitor
```

## 📞 Support

Pour toute question ou problème :
1. Consultez `TROUBLESHOOTING.md`
2. Vérifiez les logs dans `logs/`
3. Testez les endpoints API
4. Ouvrez une issue sur GitHub

## 📄 Licence

Ce projet est sous licence MIT. Voir `LICENSE` pour plus de détails.

---

**Version** : MacDev  
**Dernière mise à jour** : Août 2025  
**Compatibilité** : Ubuntu 24.04, macOS, Python 3.9+ 