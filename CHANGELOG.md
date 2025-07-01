# Changelog - NTP Monitor Enterprise

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Versioning Sémantique](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-12-30

### 🚀 Ajouts majeurs
- **Dashboard interactif complet** avec graphiques Chart.js
- **Système d'alertes intelligent** avec notifications temps réel
- **Interface d'administration** pour configuration des serveurs NTP
- **Support multi-utilisateurs** (Admin/Operator/Viewer)
- **Monitoring des clients NTP** connectés au serveur local
- **WebSocket temps réel** pour les notifications instantanées
- **API REST complète** pour l'intégration externe

### ✅ Corrections critiques
- **Chart.js: Erreur "date adapter"** - Migration vers axe catégorie
- **Encodage UTF-8** - Support complet Windows/Linux pour caractères français
- **Gestion des erreurs API** - Détection session expirée et rechargement automatique
- **Validation des données** - Vérifications robustes pour les graphiques

### 🎨 Améliorations interface
- **Serveurs locaux mis en évidence** - Badge "Local" distinctif
- **Format d'heure simplifié** - Affichage HH:MM au lieu de timestamp complet
- **Badge d'alertes cliquable** - Compteur coloré avec indicateur visuel
- **Zoom graphique interactif** - Fonctionnalité de zoom sur les courbes
- **Design responsive** - Optimisation mobile et desktop
- **Icônes FontAwesome** - Intégration complète des polices

### 🔧 Améliorations techniques
- **Architecture modulaire** - Séparation claire backend/frontend
- **Gestion d'erreurs robuste** - Handlers d'erreur globaux
- **Configuration flexible** - Support .env pour tous les paramètres
- **Logging structuré** - Système de logs complet avec rotation
- **Base de données optimisée** - Support SQLite/MySQL/PostgreSQL

### 🔒 Sécurité
- **Authentification sécurisée** - Hash des mots de passe avec bcrypt
- **Protection CSRF** - Validation des formulaires
- **Sessions sécurisées** - Configuration Flask-Login avancée
- **Validation des entrées** - Sanitisation des données utilisateur

### 📚 Documentation
- **README complet** - Installation et configuration détaillées
- **Guide de déploiement** - Procédures GitHub et production
- **API documentation** - Endpoints et exemples d'utilisation
- **Guide de résolution** - Solutions aux problèmes courants

## [1.2.0] - 2024-12-29

### Ajouts
- Support MySQL/MariaDB en plus de SQLite
- Configuration des serveurs NTP via interface web
- Monitoring des clients NTP locaux
- Système d'alertes de base

### Corrections
- Stabilité des connexions NTP
- Gestion des timeouts
- Interface responsive améliorée

## [1.1.0] - 2024-12-28

### Ajouts
- Interface web d'administration
- Graphiques de base avec Chart.js
- Système d'authentification simple
- Configuration via fichiers .env

### Corrections
- Performance des requêtes NTP
- Affichage des données temps réel

## [1.0.0] - 2024-12-27

### Ajouts initiaux
- **Monitoring NTP de base** - 5 serveurs simultanés
- **Interface web simple** - Dashboard basique
- **Base de données SQLite** - Stockage des logs
- **Service NTP** - Intégration ntplib
- **Configuration statique** - Serveurs prédéfinis

---

## Types de changements

- `Ajouts` pour les nouvelles fonctionnalités
- `Corrections` pour les corrections de bugs
- `Améliorations` pour les changements dans les fonctionnalités existantes
- `Suppressions` pour les fonctionnalités supprimées
- `Sécurité` en cas de vulnérabilités

## Notes de version

### Version 2.0.0 - Révision majeure

Cette version marque une refonte complète de l'application avec :

#### Corrections critiques résolues
1. **Erreur Chart.js** (`This method is not implemented`) - Problème majeur qui empêchait l'affichage des graphiques
2. **Encodage UTF-8** - Support complet des caractères français sur Windows
3. **Gestion des erreurs API** - Sessions expirées et rechargement automatique
4. **Validation des données** - Prévention des erreurs de graphiques vides

#### Nouvelles fonctionnalités majeures
1. **Dashboard interactif** - Graphiques zoomables et temps réel
2. **Système d'alertes** - Notifications WebSocket instantanées
3. **Administration web** - Configuration complète des serveurs
4. **Multi-utilisateurs** - Rôles et permissions
5. **Monitoring clients** - Détection des clients NTP connectés

#### Architecture technique
1. **Structure modulaire** - Backend/Frontend séparés
2. **API REST complète** - Endpoints documentés
3. **WebSocket temps réel** - Notifications instantanées
4. **Configuration flexible** - Variables d'environnement
5. **Support multi-BDD** - SQLite, MySQL, PostgreSQL

Cette version est recommandée pour tous les utilisateurs et corrige tous les problèmes connus des versions précédentes. 