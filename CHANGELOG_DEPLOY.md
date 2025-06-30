# 📋 Changelog - Système de Déploiement

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