# NTP Monitor Enterprise v2.0.0

🚀 **Application web professionnelle de monitoring NTP temps réel avec interface d'administration complète**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com)

## 📋 Table des matières

- [Aperçu](#aperçu)
- [Fonctionnalités](#fonctionnalités)
- [Prérequis](#prérequis)
- [Installation rapide](#installation-rapide)
- [Configuration](#configuration)
- [Déploiement](#déploiement)
- [Architecture](#architecture)
- [API Documentation](#api-documentation)
- [Résolution des problèmes](#résolution-des-problèmes)
- [Contribuer](#contribuer)

## 🎯 Aperçu

NTP Monitor Enterprise est une solution complète de monitoring des serveurs NTP avec :
- **Monitoring temps réel** de 5 serveurs NTP (3 mondiaux + 2 locaux configurables)
- **Interface d'administration** dynamique pour la gestion des serveurs
- **Système d'alertes** intelligent avec notifications WebSocket
- **Monitoring clients NTP** connectés au serveur local
- **Dashboard interactif** avec graphiques Chart.js et zoom
- **Support multi-utilisateurs** avec authentification sécurisée

## ✨ Fonctionnalités

### 🔧 Administration
- ✅ Configuration dynamique des serveurs NTP
- ✅ Gestion des seuils d'alertes personnalisables
- ✅ Interface d'administration responsive
- ✅ Gestion multi-utilisateurs (Admin/Operator/Viewer)

### 📊 Monitoring
- ✅ Surveillance temps réel de 5 serveurs NTP
- ✅ Graphiques interactifs avec zoom (Chart.js)
- ✅ Alertes colorées et notifications WebSocket
- ✅ Monitoring des clients NTP locaux
- ✅ Mise en évidence des serveurs locaux

### 🔔 Alertes & Notifications
- ✅ Système d'alertes intelligent
- ✅ Notifications temps réel via WebSocket
- ✅ Badge d'alertes cliquable avec compteur
- ✅ Gestion des seuils personnalisables

### 🎨 Interface utilisateur
- ✅ Design moderne et responsive
- ✅ Support complet UTF-8 (caractères français)
- ✅ Format d'heure simplifié (HH:MM)
- ✅ Graphiques interactifs avec gestion d'erreurs
- ✅ Icônes FontAwesome intégrées

## 🔧 Prérequis

### Système d'exploitation
- **Windows 10/11** ou **Linux Ubuntu 20.04+**
- **Python 3.8+** (testé avec Python 3.11)

### Dépendances système
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv ntp ntpdate

# Windows (chocolatey)
choco install python3 ntp
```

### Services requis
- **NTP Service** (ntpd ou chrony)
- **Redis** (optionnel, pour cache et WebSocket)
- **MySQL/SQLite** (base de données)

## 🚀 Installation rapide

### 1. Cloner le repository
```bash
git clone https://github.com/votre-username/ntp-monitor-enterprise.git
cd ntp-monitor-enterprise
```

### 2. Créer l'environnement virtuel
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration initiale
```bash
# Configurer l'encodage UTF-8 (Windows)
chcp 65001

# Créer les répertoires nécessaires
mkdir -p logs instance

# Initialiser la base de données
python init_database.py
```

### 5. Lancer l'application
```bash
# Mode développement
python app.py

# Mode production (avec gunicorn)
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
```

### 6. Accéder à l'interface
- **URL locale:** http://localhost:5000
- **Compte admin:** `admin` / `admin123`
- **Compte opérateur:** `operator` / `operator123`
- **Compte visualiseur:** `viewer` / `viewer123`

## ⚙️ Configuration

### Variables d'environnement
Créer un fichier `.env` :
```env
# Configuration de base
FLASK_ENV=production
SECRET_KEY=votre-clé-secrète-très-longue
DEBUG=false

# Base de données
DATABASE_URL=sqlite:///instance/ntp_monitor.db
# Pour MySQL: mysql+pymysql://user:password@localhost/ntp_monitor

# Configuration NTP
DEFAULT_NTP_SERVERS=pool.ntp.org,time.google.com,time.cloudflare.com
LOCAL_NTP_SERVERS=192.168.1.100,10.0.0.50

# Alertes
ALERT_OFFSET_THRESHOLD=100
ALERT_DELAY_THRESHOLD=500
ALERT_EMAIL=admin@exemple.com

# WebSocket
SOCKETIO_ASYNC_MODE=threading
```

### Configuration des serveurs NTP
Les serveurs peuvent être configurés via l'interface web ou directement dans la base de données :

```python
# Serveurs par défaut
GLOBAL_SERVERS = [
    'pool.ntp.org',
    'time.google.com', 
    'time.cloudflare.com'
]

LOCAL_SERVERS = [
    '192.168.1.100',  # Configurable via interface
    '10.0.0.50'       # Configurable via interface
]
```

## 🏗️ Architecture

```
ntp-monitor-enterprise/
├── app.py                      # Point d'entrée principal ✅
├── requirements.txt            # Dépendances Python ✅
├── .env.example               # Configuration exemple
├── .gitignore                 # Fichiers à ignorer ✅
│
├── backend/                   # Backend Flask
│   ├── __init__.py
│   ├── app/                   # Application Flask
│   │   ├── __init__.py        # Factory app ✅
│   │   ├── auth.py           # Authentification ✅
│   │   └── routes.py         # Routes principales ✅
│   │
│   ├── api/                   # API REST
│   │   ├── __init__.py
│   │   ├── main.py           # Routes principales ✅
│   │   ├── ntp.py            # API NTP ✅
│   │   ├── admin.py          # API administration ✅
│   │   ├── alerts.py         # API alertes ✅
│   │   └── websocket.py      # WebSocket handlers ✅
│   │
│   ├── models/               # Modèles base de données
│   │   ├── __init__.py
│   │   ├── user.py           # Modèle utilisateur ✅
│   │   ├── ntp_server.py     # Modèle serveur NTP ✅
│   │   ├── ntp_log.py        # Logs NTP ✅
│   │   └── alert.py          # Modèle alertes ✅
│   │
│   ├── services/             # Services métier
│   │   ├── __init__.py
│   │   ├── ntp_service.py    # Service NTP principal ✅
│   │   ├── alert_service.py  # Service alertes ✅
│   │   └── client_monitor_service.py  # Monitoring clients ✅
│   │
│   └── utils/                # Utilitaires
│       ├── __init__.py
│       └── init_data.py      # Données initiales ✅
│
├── frontend/                 # Frontend web
│   ├── static/               # Assets statiques
│   │   ├── css/              # Styles CSS
│   │   │   ├── app.css       # Styles principaux ✅
│   │   │   └── vendor/       # CSS tiers (Bootstrap, FontAwesome) ✅
│   │   │
│   │   ├── js/               # JavaScript
│   │   │   ├── dashboard.js  # Dashboard principal ✅ [CORRIGÉ]
│   │   │   ├── app.js        # App principale ✅
│   │   │   ├── modules/      # Modules JS ✅
│   │   │   └── vendor/       # JS tiers ✅
│   │   │
│   │   └── fonts/            # Polices FontAwesome ✅
│   │
│   └── templates/            # Templates HTML
│       ├── base.html         # Template de base ✅
│       ├── dashboard.html    # Dashboard ✅
│       ├── auth/             # Templates auth ✅
│       └── modals/           # Modales ✅
│
├── config/                   # Configuration
│   └── config.py            # Configuration Flask ✅
│
├── deployment/              # Scripts de déploiement
│   ├── apache/              # Configuration Apache
│   └── scripts/             # Scripts d'installation
│
└── docs/                    # Documentation
    ├── DEPLOYMENT.md        # Guide de déploiement
    ├── API.md              # Documentation API
    └── TROUBLESHOOTING.md  # Résolution problèmes
```

## 🔧 Corrections appliquées

### ✅ Correction Chart.js (Erreur critique résolue)
- **Problème:** `Error: This method is not implemented: Check that a complete date adapter is provided`
- **Solution:** Changement de l'axe temps vers axe catégorie dans `dashboard.js`
- **Impact:** Graphiques fonctionnels avec formatage d'heure personnalisé

### ✅ Correction encodage UTF-8 (Windows)
- **Problème:** Caractères français corrompus dans les logs
- **Solution:** Configuration UTF-8 dans `app.py` + `chcp 65001`
- **Impact:** Affichage correct des caractères français

### ✅ Améliorations interface utilisateur
- **Ajouté:** Mise en évidence des serveurs locaux
- **Ajouté:** Format d'heure simplifié (HH:MM)
- **Ajouté:** Badge d'alertes cliquable avec compteur coloré
- **Ajouté:** Zoom interactif sur les graphiques
- **Ajouté:** Gestion d'erreurs robuste avec rechargement automatique

## 🚀 Déploiement production

### Apache + mod_wsgi
```bash
# Installer Apache et mod_wsgi
sudo apt install apache2 libapache2-mod-wsgi-py3

# Copier la configuration
sudo cp deployment/apache/ntp-monitor.conf /etc/apache2/sites-available/
sudo a2ensite ntp-monitor
sudo systemctl reload apache2
```

### Systemd Service
```bash
# Copier le service
sudo cp deployment/systemd/ntp-monitor.service /etc/systemd/system/
sudo systemctl enable ntp-monitor
sudo systemctl start ntp-monitor
```

### Docker (optionnel)
```bash
# Build image
docker build -t ntp-monitor-enterprise .

# Run container
docker run -d -p 5000:5000 --name ntp-monitor ntp-monitor-enterprise
```

## 📚 API Documentation

### Endpoints principaux
- `GET /api/ntp/status` - Statut des serveurs NTP
- `GET /api/ntp/analytics/offset-trends` - Données graphiques
- `POST /api/admin/servers` - Configuration serveurs
- `GET /api/alerts/active` - Alertes actives
- `WebSocket /socket.io` - Notifications temps réel

### Exemple d'utilisation
```javascript
// Récupérer le statut NTP
fetch('/api/ntp/status')
  .then(response => response.json())
  .then(data => console.log(data));
```

## 🐛 Résolution des problèmes

### Erreur Chart.js
**Symptôme:** `Error: This method is not implemented`
**Solution:** ✅ Déjà corrigé dans `dashboard.js` ligne 604

### Caractères français corrompus
**Symptôme:** Affichage incorrect des accents
**Solution:** ✅ Configuration UTF-8 dans `app.py` et `chcp 65001`

### Session expirée sur API
**Symptôme:** Retour HTML au lieu de JSON
**Solution:** ✅ Détection automatique et rechargement de page

### Serveurs NTP non accessibles
**Symptôme:** Timeout sur requêtes NTP
**Solution:** Vérifier la configuration réseau et pare-feu

## 🤝 Contribuer

1. Fork le repository
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 License

Distribué sous license MIT. Voir `LICENSE` pour plus d'informations.

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/votre-username/ntp-monitor-enterprise/issues)
- **Documentation:** [Wiki](https://github.com/votre-username/ntp-monitor-enterprise/wiki)
- **Email:** support@exemple.com

---

**NTP Monitor Enterprise v2.0.0** - Solution professionnelle de monitoring NTP
Développé avec ❤️ par [Votre nom] 