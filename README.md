# 🚀 NTP Monitor Enterprise v2.1.0

Une solution professionnelle de monitoring NTP temps réel pour Ubuntu 24.04 avec interface web moderne et alertes intelligentes.

## ✨ **Nouvelles Fonctionnalités 2025**

- ✅ **Corrections critiques** : Chart.js, UTF-8, scripts d'installation
- ✅ **Déploiement simplifié** : Installation one-click depuis GitHub
- ✅ **Monitoring étendu** : 8 serveurs NTP simultanés
- ✅ **Fallback intelligent** : MySQL avec basculement SQLite automatique
- ✅ **Scripts robustes** : Auto-nettoyage UTF-8 et gestion d'erreurs
- ✅ **Documentation complète** : Guide de déploiement mis à jour

## 🎯 **Fonctionnalités Principales**

### **Monitoring NTP Avancé**
- 🕒 **8 serveurs NTP** surveillés simultanément (3 mondiaux + 5 locaux configurables)
- 📊 **Métriques précises** : offset, delay, jitter, stratum
- 🔄 **Mise à jour temps réel** : Actualisation automatique toutes les 30 secondes
- 📈 **Graphiques interactifs** : Historique 24h/7j/30j avec zoom

### **Interface Web Moderne**
- 🎨 **Design responsive** : Bootstrap 5 + thème sombre/clair
- 🔔 **Alertes temps réel** : Notifications WebSocket instantanées
- 👥 **Multi-utilisateurs** : Rôles admin/opérateur/visualiseur
- 🌐 **API REST** : Intégration avec systèmes externes

### **Sécurité et Performance**
- 🔐 **Authentification** : Sessions sécurisées avec Redis
- 🛡️ **Protection CSRF** : Sécurité renforcée
- ⚡ **Cache intelligent** : Optimisation performances
- 📝 **Logs détaillés** : Traçabilité complète

## 🚀 **Installation Rapide**

### **Méthode 1 : Installation One-Click (Recommandée)**
```bash
# Installation complète en une commande
curl -fsSL https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/quick_install_ubuntu24.sh | sudo bash
```

### **Méthode 2 : Installation Étape par Étape**
```bash
# 1. Installer les prérequis système
curl -fsSL https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/dependencies_checker_ubuntu24_final.sh | sudo bash

# 2. Déployer l'application
curl -fsSL https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deploy_ubuntu_production.sh | sudo bash
```

### **Méthode 3 : Installation Manuelle**
```bash
# Cloner le projet (branche dev recommandée)
git clone -b dev https://github.com/gilandre/NTPVIZ.git
cd NTPVIZ

# Installer prérequis et déployer
sudo ./dependencies_checker_ubuntu24_final.sh
sudo ./deploy_ubuntu_production.sh
```

## 📋 **Prérequis Système**

- **OS** : Ubuntu 24.04 LTS (compatible 22.04/20.04)
- **RAM** : 2GB minimum, 4GB recommandé
- **Disque** : 10GB libre minimum
- **Accès** : Privilèges sudo/root
- **Réseau** : Connexion Internet pour synchronisation

## 🌐 **Accès Application**

Après installation réussie :

```bash
# Interface web
http://votre-serveur              # Via Apache (production)
http://votre-serveur:5000         # Direct Flask (développement)

# Comptes par défaut (à changer après première connexion)
Administrateur : admin / admin123
Opérateur      : operator / operator123
Visualiseur    : viewer / viewer123
```

## 🔧 **Corrections Critiques Appliquées**

### **1. Chart.js - Graphiques Fonctionnels**
```javascript
// PROBLÈME RÉSOLU : Error: This method is not implemented
// Changement de l'axe temps vers axe catégorie
x: {
    type: 'category',
    labels: timeLabels  // Format HH:MM personnalisé
}
```

### **2. UTF-8 - Caractères Français**
```python
// PROBLÈME RÉSOLU : Caractères français corrompus
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
```

### **3. Scripts Installation - Auto-nettoyage**
```bash
# PROBLÈME RÉSOLU : "$'\240...': command not found"
# Auto-nettoyage caractères UTF-8 problématiques
if [[ "$1" != "--cleaned" ]]; then
    sed -i 's/\xC2\xA0/ /g' "$0" 2>/dev/null || true
    exec "$0" --cleaned "$@"
fi
```

## 📊 **Architecture Technique**

### **Backend Python**
- **Framework** : Flask 2.3.3 + SQLAlchemy 2.0.21
- **Base de données** : MySQL (production) / SQLite (fallback)
- **Cache** : Redis pour sessions et cache
- **WebSocket** : Flask-SocketIO pour temps réel

### **Frontend Moderne**
- **UI** : Bootstrap 5 + Font Awesome
- **Graphiques** : Chart.js avec zoom interactif
- **Temps réel** : WebSocket pour notifications
- **Responsive** : Support mobile et tablette

### **Infrastructure**
- **Serveur web** : Apache 2.4 + mod_wsgi
- **Services** : systemd pour démarrage automatique
- **Monitoring** : NTP clients + métriques système
- **Sécurité** : UFW firewall + SSL optionnel

## 🗂️ **Structure du Projet**

```
NTPVIZ/
├── app.py                        # Application Flask principale
├── backend/                      # Code Python backend
│   ├── api/                      # Endpoints REST
│   │   ├── main.py              # Routes principales
│   │   ├── ntp.py               # API NTP
│   │   ├── auth.py              # Authentification
│   │   ├── admin.py             # Administration
│   │   ├── alerts.py            # Système d'alertes
│   │   └── websocket.py         # WebSocket temps réel
│   ├── models/                   # Modèles base de données
│   │   ├── ntp_server.py        # Serveurs NTP
│   │   ├── ntp_log.py           # Logs monitoring
│   │   ├── user.py              # Utilisateurs
│   │   └── alert.py             # Alertes
│   ├── services/                 # Services métier
│   │   ├── ntp_service.py       # Monitoring NTP
│   │   ├── alert_service.py     # Gestion alertes
│   │   └── aggregation_service.py # Agrégation données
│   └── utils/                    # Utilitaires
│       ├── init_data.py         # Initialisation BDD
│       └── mysql_fallback.py    # Fallback MySQL/SQLite
├── frontend/                     # Interface web
│   ├── static/
│   │   ├── css/                 # Styles CSS
│   │   ├── js/                  # JavaScript
│   │   │   ├── dashboard.js     # Dashboard (corrigé)
│   │   │   └── modules/         # Modules JS
│   │   └── fonts/               # Font Awesome
│   └── templates/               # Templates HTML
│       ├── base.html           # Template de base
│       ├── dashboard.html      # Dashboard principal
│       ├── auth/               # Authentification
│       └── modals/             # Modales
├── config/                      # Configuration
│   └── config.py               # Configuration Flask
├── deployment/                  # Scripts de déploiement
│   ├── scripts/                # Scripts d'installation
│   ├── apache/                 # Configuration Apache
│   └── systemd/                # Services systemd
├── requirements.txt            # Dépendances Python
└── docs/                       # Documentation
    ├── GUIDE_DEPLOIEMENT_COMPLET_2025.md  # Guide complet
    ├── INSTALLATION_RAPIDE.md             # Installation rapide
    └── API.md                              # Documentation API
```

## 🔧 **Gestion et Maintenance**

### **Commandes Utiles**
```bash
# Statut des services
sudo systemctl status ntp-monitor-enterprise apache2 mysql redis-server

# Logs en temps réel
sudo journalctl -u ntp-monitor-enterprise -f
sudo tail -f /var/log/apache2/ntp-monitor-enterprise_error.log

# Redémarrage des services
sudo systemctl restart ntp-monitor-enterprise
sudo systemctl restart apache2

# Mise à jour depuis GitHub
cd /home/ntp-monitor/ntp-monitor-enterprise
sudo -u ntp-monitor git pull origin dev
sudo systemctl restart ntp-monitor-enterprise
```

### **Sauvegarde et Restauration**
```bash
# Sauvegarde complète
sudo tar -czf /backup/ntp-monitor-$(date +%Y%m%d).tar.gz \
  /home/ntp-monitor/ntp-monitor-enterprise \
  /etc/apache2/sites-available/ntp-monitor-enterprise.conf

# Sauvegarde base de données seulement
sudo cp /home/ntp-monitor/ntp-monitor-enterprise/instance/ntp_monitor_prod.db /backup/
```

## 🛡️ **Sécurité**

### **Bonnes Pratiques**
- ✅ **Changez les mots de passe** par défaut après installation
- ✅ **Configurez SSL/HTTPS** avec certbot pour la production
- ✅ **Surveillez les logs** d'accès régulièrement
- ✅ **Mettez à jour** le système Ubuntu mensuellement
- ✅ **Sauvegardez** la base de données hebdomadairement

### **Configuration SSL (Optionnel)**
```bash
# Installation Certbot
sudo apt install certbot python3-certbot-apache

# Obtention certificat SSL
sudo certbot --apache -d votre-domaine.com

# Test renouvellement automatique
sudo certbot renew --dry-run
```

## 📈 **Monitoring Avancé**

### **Métriques Surveillées**
- **Serveurs NTP** : 8 serveurs simultanés (3 mondiaux + 5 locaux)
- **Synchronisation** : Offset, delay, jitter, stratum par serveur
- **Alertes** : Seuils configurables (100ms offset, 500ms delay)
- **Clients** : Connexions actives au serveur NTP local
- **Système** : CPU, RAM, disque, réseau

### **Tableau de Bord**
- **Temps réel** : Mise à jour automatique toutes les 30 secondes
- **Graphiques** : Historique avec zoom interactif
- **Alertes** : Notifications WebSocket instantanées
- **Statistiques** : Moyennes, min/max, tendances

## 🆘 **Dépannage**

### **Problèmes Courants**

#### **Service ne démarre pas**
```bash
# Diagnostic
sudo systemctl status ntp-monitor-enterprise --no-pager
sudo journalctl -u ntp-monitor-enterprise --no-pager

# Solution
sudo systemctl daemon-reload
sudo systemctl restart ntp-monitor-enterprise
```

#### **Interface web inaccessible**
```bash
# Vérifier Apache
sudo systemctl status apache2
sudo apache2ctl configtest

# Redémarrer Apache
sudo systemctl restart apache2
```

#### **Erreurs base de données**
```bash
# Réinitialiser base de données
sudo systemctl stop ntp-monitor-enterprise
sudo rm -f /home/ntp-monitor/ntp-monitor-enterprise/instance/ntp_monitor_prod.db
sudo systemctl start ntp-monitor-enterprise
```

## 📚 **Documentation**

- **[Guide de Déploiement Complet](docs/GUIDE_DEPLOIEMENT_COMPLET_2025.md)** - Installation et configuration détaillées
- **[Installation Rapide](INSTALLATION_RAPIDE.md)** - Commandes one-click
- **[Documentation API](docs/API.md)** - Endpoints REST et WebSocket
- **[Résolution de Problèmes](docs/TROUBLESHOOTING.md)** - Dépannage avancé

## 🤝 **Contribution**

Les contributions sont les bienvenues ! Pour contribuer :

1. **Fork** le projet
2. **Créez** une branche feature (`git checkout -b feature/AmazingFeature`)
3. **Committez** vos changements (`git commit -m 'Add AmazingFeature'`)
4. **Push** vers la branche (`git push origin feature/AmazingFeature`)
5. **Ouvrez** une Pull Request

## 📞 **Support**

- **GitHub Issues** : [https://github.com/gilandre/NTPVIZ/issues](https://github.com/gilandre/NTPVIZ/issues)
- **Documentation** : Guides dans le dossier `docs/`
- **Logs** : `/home/ntp-monitor/ntp-monitor-enterprise/logs/`

## 📄 **Licence**

Ce projet est sous licence propriétaire. Voir le fichier `LICENSE` pour plus de détails.

## 🏆 **Remerciements**

- **NTP.org** pour le protocole NTP
- **Flask** pour le framework web
- **Chart.js** pour les graphiques
- **Bootstrap** pour l'interface utilisateur
- **Communauté OpenSource** pour les outils et bibliothèques

---

## 🎉 **Statut du Projet**

- ✅ **Stable** : Version 2.1.0 en production
- ✅ **Testé** : Ubuntu 24.04/22.04/20.04
- ✅ **Documenté** : Guides complets disponibles
- ✅ **Maintenu** : Mises à jour régulières
- ✅ **Support** : Issues GitHub actives

**🚀 Prêt pour la production !**

---

*NTP Monitor Enterprise v2.1.0 - Solution professionnelle de monitoring NTP*  
*Dernière mise à jour : Janvier 2025* 