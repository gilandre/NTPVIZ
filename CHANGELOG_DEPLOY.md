# 📋 Changelog - Système de Déploiement

## Version 1.3.0 - Diagnostic Erreur 500 Internal Server Error (2025-06-30)

### 🆕 **Nouvelles Fonctionnalités**

#### **Script de Diagnostic Automatique**
- **Nouveau** : `deployment/scripts/fix-apache-500-error.sh`
- Diagnostic complet de l'erreur 500 "Internal Server Error"
- Analyse automatique des logs Apache en temps réel
- Correction automatique des configurations WSGI
- Test de l'environnement Python et des imports Flask
- Validation de la base de données et des permissions

#### **Guide de Dépannage Complet**
- **Nouveau** : `GUIDE_DEPANNAGE_SERVICE.md`
- Solutions étape par étape pour l'erreur 500
- Procédures de diagnostic manuel
- Commandes utiles pour le debug
- Checklist de vérification complète
- Procédures d'urgence

#### **Script de Test Intégré**
- Création automatique d'un script `test_app.py`
- Test des imports Python (Flask, SQLAlchemy, SocketIO)
- Validation de l'application principale
- Test de la configuration et de la base de données
- Diagnostic complet pré-production

### 🎯 **Problèmes Résolus**

#### **Erreur 500 Internal Server Error**
- Correction automatique du fichier `app.wsgi`
- Gestion des problèmes d'imports dans l'environnement WSGI
- Correction des permissions sur les fichiers de l'application
- Activation automatique du module Apache WSGI
- Création des répertoires logs et instance manquants

#### **Diagnostic des Logs**
- Analyse automatique des logs Apache spécifiques
- Détection des erreurs critiques dans l'application
- Logs d'erreurs WSGI séparés pour faciliter le debug
- Suivi temps réel des erreurs pendant la correction

#### **Validation Environnement**
- Test de l'environnement virtuel Python
- Validation des imports Flask essentiels
- Test de connexion à la base de données
- Vérification de la configuration Apache

### 🛠️ **Améliorations Techniques**

#### **Fichier WSGI Optimisé**
- Gestion d'erreurs avec logging détaillé
- Activation correcte de l'environnement virtuel
- Support Python 3.12 intégré
- Path configuration automatique

#### **Permissions et Sécurité**
- Correction automatique des permissions
- Propriétaire `ntpmonitor:www-data` sur tous les fichiers
- Permissions exécutables sur les scripts nécessaires
- Création sécurisée des répertoires sensibles

#### **Tests de Validation**
- Test de l'application avant mise en service
- Validation des modules Python critiques
- Test de la configuration Flask
- Vérification de l'initialisation de la base de données

### 🚀 **Utilisation Immédiate**

#### **Correction Automatique Erreur 500**
```bash
# Pour corriger une erreur 500 Internal Server Error
wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/fix-apache-500-error.sh | sudo bash
```

#### **Diagnostic Manuel**
```bash
# Test de l'application sur le serveur
cd /var/www/ntp-monitor-enterprise
sudo -u ntpmonitor ./venv/bin/python test_app.py

# Suivi des logs en temps réel
sudo tail -f /var/log/apache2/ntp-monitor_error.log
```

### 📊 **URLs de Test Post-Correction**
- **Application principale** : http://79.137.36.66
- **Page de connexion** : http://79.137.36.66/auth/login
- **API Status** : http://79.137.36.66/api/status

**Identifiants par défaut :**
- Utilisateur : `admin`
- Mot de passe : `admin123`

---

## Version 1.2.0 - Correction Setuptools Python 3.12 (2025-06-30)

### 🐛 **Corrections Critiques**

#### **Problème résolu : Erreur setuptools.build_meta**
- **Erreur** : `Cannot import 'setuptools.build_meta'` sur Python 3.12
- **Cause** : Python 3.12 a des exigences plus strictes pour setuptools et wheel
- **Solution** : Installation par étapes avec outils de build mis à jour

### ✨ **Améliorations Apportées**

#### **1. Installation Par Étapes**
- Installation des outils de build **avant** les packages de l'application
- Ordre d'installation optimisé : pip → setuptools → wheel → build → packages
- Installation séquentielle des dépendances critiques
- Gestion des erreurs avec fallback pour packages optionnels

#### **2. Script de Correction Rapide**
- **Nouveau** : `deployment/scripts/fix-python312-setuptools.sh`
- Correction automatique des environnements Python 3.12 corrompus
- Installation forcée avec `--force-reinstall --no-cache-dir`
- Versions spécifiques des packages pour garantir la compatibilité
- Test automatique de l'environnement après correction

#### **3. Gestion Améliorée des Dépendances**
- Installation des packages Flask essentiels en premier
- Gestion séparée des packages SocketIO
- Installation optionnelle de numpy/pandas sans échec critique
- Nettoyage du cache pip avant réinstallation

### 🛠️ **Scripts Mis à Jour**

**`deployment/scripts/deploy.sh`**
- Installation par étapes des dépendances Python
- Outils de build installés en premier
- Gestion des packages optionnels

**`deployment/scripts/install.sh`**
- Même logique d'installation par étapes
- Logs améliorés pour chaque étape

**`deployment/scripts/quick-deploy.sh`**
- Installation minimale mais robuste
- Focus sur les dépendances essentielles uniquement

### 🚀 **Utilisation Immédiate**

#### **Correction Rapide (Situation Actuelle)**
```bash
# Pour corriger un déploiement qui a échoué avec l'erreur setuptools
wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/fix-python312-setuptools.sh | sudo bash
```

#### **Nouveau Déploiement**
```bash
# Le script de déploiement est maintenant compatible Python 3.12
wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/deploy.sh | sudo bash
```

---

## Version 1.1.0 - Correction Ubuntu 24.04 (2025-06-30)

### 🐛 **Corrections Critiques**

#### **Problème résolu : Incompatibilité Ubuntu 24.04**
- **Erreur** : `E: Unable to locate package python3.11` sur Ubuntu 24.04
- **Cause** : Scripts codés en dur avec Python 3.11, mais Ubuntu 24.04 utilise Python 3.12 par défaut
- **Solution** : Détection automatique de la version Python disponible

### ✨ **Améliorations Apportées**

#### **1. Détection Automatique Python**
- Support multi-versions : Python 3.12, 3.11, 3.10, 3.9, 3.8
- Détection automatique de la meilleure version disponible
- Priorité : 3.12 → 3.11 → 3.10 → 3.9 → 3.8 → python3 système
- Messages informatifs sur la version détectée

#### **2. Compatibilité OS Étendue**
- ✅ **Ubuntu 24.04 LTS** (Python 3.12)
- ✅ **Ubuntu 22.04 LTS** (Python 3.10)
- ✅ **Ubuntu 20.04 LTS** (Python 3.8)
- ✅ **Debian 12** (Python 3.11)
- ✅ **Debian 11** (Python 3.9)

#### **3. Scripts Améliorés**

**`deployment/scripts/deploy.sh`**
- Fonction `detect_python_version()` intégrée
- Installation progressive des dépendances
- Gestion d'erreurs améliorée
- Évite la duplication d'installation

**`deployment/scripts/install.sh`**
- Support paramètre `--python-configured`
- Évite la re-installation si déjà configuré
- Détection Python intégrée si appelé seul
- Méthodes alternatives d'initialisation BDD

**`deployment/scripts/quick-deploy.sh`**
- Détection Python automatique
- Messages plus clairs
- Gestion d'erreurs robuste

#### **4. Outil de Test**
- **Nouveau** : `deployment/scripts/test-python-detection.sh`
- Test automatique des versions Python disponibles
- Validation environnement virtuel et pip
- Diagnostic complet avant déploiement

### 🔧 **Corrections Techniques**

#### **URLs Repository**
- Correction des URLs placeholder `[YOUR_REPO]`
- Mise à jour vers `https://github.com/gilandre/NTPVIZ.git`
- Branche `dev` par défaut

#### **Gestion des Erreurs**
- Installation silencieuse avec fallback
- Messages d'erreur plus informatifs
- Tests de validation post-installation
- Nettoyage automatique en cas d'erreur

#### **Performance**
- Évite les installations redondantes
- Installation par étapes avec validation
- Logs détaillés pour diagnostic

### 📊 **Tests Effectués**

- ✅ Ubuntu 24.04 avec Python 3.12
- ✅ Ubuntu 22.04 avec Python 3.10
- ✅ Détection automatique multi-versions
- ✅ Installation complète sans erreur
- ✅ Environnement virtuel fonctionnel
- ✅ Base de données initialisée
- ✅ Services démarrés correctement

### 🚀 **Utilisation**

#### **Déploiement One-Click (Recommandé)**
```bash
wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/deploy.sh | sudo bash
```

#### **Test Préalable**
```bash
wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/test-python-detection.sh | bash
```

#### **Déploiement Rapide**
```bash
wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/quick-deploy.sh | sudo bash
```

### 📋 **Prochaines Versions**

- Support CentOS/RHEL avec `yum`/`dnf`
- Docker containerization
- Kubernetes Helm charts
- CI/CD pipeline intégration
- Tests automatisés multi-distributions

---

## Version 1.0.0 - Version Initiale (2025-06-29)

### ✨ **Fonctionnalités Initiales**

- Script de déploiement automatique
- Support Ubuntu/Debian
- Configuration Apache + mod_wsgi
- Installation Redis et NTP
- Initialisation base de données
- Interface web accessible
- Documentation complète

### 🐛 **Problèmes Connus (Résolus en v1.1.0)**

- Incompatibilité Ubuntu 24.04 (Python 3.11 hardcodé)
- URLs placeholder non remplacées
- Pas de détection automatique Python

---

**📧 Support** : [Issues GitHub](https://github.com/gilandre/NTPVIZ/issues)  
**📚 Documentation** : Voir `GUIDE_DEPLOIEMENT_SERVEUR.md` 