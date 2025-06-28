# NTP Monitor Enterprise v1.0

Application web professionnelle de monitoring NTP temps réel avec gestion complète des serveurs configurables.

## 🎯 Objectifs

- **Monitoring simultané** de 5 serveurs NTP (3 mondiaux + 2 locaux configurables)
- **Interface d'administration** pour configuration dynamique des serveurs
- **Système d'alertes** intelligent avec notifications temps réel
- **Monitoring clients NTP** connectés au serveur local
- **Manuel utilisateur** intégré à l'interface

## 🏗️ Architecture

```
ntp-monitor-enterprise/
├── backend/                 # API Flask + Services NTP
│   ├── app/                # Application Flask
│   ├── models/             # Modèles base de données
│   ├── services/           # Services NTP et monitoring
│   ├── api/                # Endpoints REST
│   └── utils/              # Utilitaires
├── frontend/               # Interface web
│   ├── static/            # CSS, JS, images
│   ├── templates/         # Templates HTML
│   └── components/        # Composants réutilisables
├── deployment/            # Configuration déploiement
│   ├── apache/           # Configuration Apache
│   ├── systemd/          # Services système
│   └── scripts/          # Scripts installation
├── docs/                 # Documentation utilisateur
├── tests/                # Tests automatisés
└── config/               # Fichiers configuration
```

## 🚀 Stack Technologique

- **Backend:** Flask + SQLAlchemy + Redis + Celery
- **Frontend:** HTML5 + Bootstrap + Chart.js + WebSocket
- **Database:** SQLite (production) / PostgreSQL (enterprise)
- **Server:** Apache + mod_wsgi
- **OS:** Ubuntu 24.04 LTS
- **NTP:** ntpsec integration

## 📦 Installation Rapide

```bash
# Clone et installation
git clone <repo> ntp-monitor-enterprise
cd ntp-monitor-enterprise
chmod +x deployment/scripts/install.sh
sudo ./deployment/scripts/install.sh
```

## 🌐 Accès Application

- **URL:** https://your-server/ntp-monitor
- **Login par défaut:** admin / admin123
- **Port:** 80/443 (Apache)

## 📚 Documentation

Documentation utilisateur intégrée accessible via l'interface web.

## 🔧 Support

- **OS:** Ubuntu 24.04 LTS
- **Web Server:** Apache 2.4+
- **Python:** 3.11+
- **NTP Service:** ntpsec

---
**NTP Monitor Enterprise** - Solution professionnelle de monitoring NTP 