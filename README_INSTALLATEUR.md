# 📦 Guide d'Installation EXE - NTP Monitor Enterprise

## 🎯 Création de l'Installateur EXE

### Prérequis
- Python 3.8+ installé sur la machine de développement
- Toutes les dépendances de l'application déjà installées

### 🚀 Processus de Build Automatisé

#### Option 1 : Script Batch (Recommandé)
```bash
# Double-cliquez sur le fichier ou exécutez dans un terminal
build_quick.bat
```

#### Option 2 : Script Python Direct  
```bash
python build_installer.py
```

### 📋 Processus de Construction

Le script automatise les étapes suivantes :

1. **Installation des outils de build** : PyInstaller, cx-freeze
2. **Création des répertoires** : dist, build, installer
3. **Copie des fichiers** : backend, frontend, config, instance
4. **Génération du lanceur** : Point d'entrée unique pour l'EXE
5. **Configuration PyInstaller** : Fichier .spec avec toutes les dépendances
6. **Création des ressources** : Icônes, version info, scripts de démarrage
7. **Build de l'exécutable** : Compilation en EXE autonome
8. **Script d'installation** : Installateur Windows automatique

### 📦 Fichiers Générés

Après la construction, vous trouverez dans `installer/dist/` :

```
installer/dist/
├── NTP_Monitor_Enterprise.exe    # Application principale (50-80 MB)
├── start_ntp_monitor.bat         # Script de démarrage convivial
└── INSTALLER.bat                 # Installateur automatique Windows
```

## 🖥️ Installation sur Windows 11

### 🔧 Installation Automatique (Recommandée)

1. **Copier les fichiers** sur la machine Windows 11 cible
2. **Clic droit** sur `INSTALLER.bat` → "Exécuter en tant qu'administrateur"
3. **Suivre les instructions** à l'écran

L'installateur créera automatiquement :
- 📁 Répertoire : `C:\Program Files\NTP Monitor Enterprise\`
- 🖥️ Raccourci Bureau : `NTP Monitor Enterprise.bat`
- 📋 Menu Démarrer : `NTP Monitor Enterprise`

### 🔧 Installation Manuelle

1. **Créer un dossier** : `C:\NTP_Monitor\`
2. **Copier les fichiers** :
   - `NTP_Monitor_Enterprise.exe`
   - `start_ntp_monitor.bat`
3. **Créer un raccourci** vers `start_ntp_monitor.bat`

## 🚀 Démarrage de l'Application

### Via les Raccourcis
- **Double-clic** sur le raccourci du bureau
- **Menu Démarrer** → Chercher "NTP Monitor"

### Démarrage Manuel
```bash
# Dans le dossier d'installation
start_ntp_monitor.bat
```

### Démarrage Direct
```bash
# Exécution directe de l'EXE
NTP_Monitor_Enterprise.exe
```

## 🌐 Accès à l'Application

Une fois démarrée, l'application sera accessible :

- **URL** : http://127.0.0.1:5000
- **Login** : admin
- **Password** : admin123

## 📁 Répertoires de Données

L'application EXE crée automatiquement :

```
%USERPROFILE%/NTP_Monitor_Data/
├── ntp_monitor_prod.db          # Base de données SQLite
└── logs/                        # Fichiers de logs
    ├── app.log
    └── ntp_monitor.log
```

## 🔧 Configuration des Serveurs NTP

La configuration inclut par défaut :

### 🌐 Serveurs Globaux (4 Pools)
- **Pool NTP 0** : 0.pool.ntp.org
- **Pool NTP 1** : 1.pool.ntp.org  
- **Pool NTP 2** : 2.pool.ntp.org
- **Pool NTP 3** : 3.pool.ntp.org

### 🏠 Serveurs Locaux (2 Serveurs)
- **SRV-NTP-01** : 192.168.10.28
- **SRV-NTP-02** : 192.168.10.45

## 🛠️ Fonctionnalités de l'EXE

### ✅ Avantages
- **Autonome** : Toutes les dépendances intégrées
- **Portable** : Aucune installation Python requise
- **Sécurisé** : Environnement isolé
- **Facile** : Double-clic pour démarrer

### 📋 Inclus dans l'EXE
- Python 3.x runtime complet
- Flask et toutes les dépendances web
- SQLite pour la base de données
- Toutes les bibliothèques NTP
- Interface web complète
- Système d'alertes
- Modules d'administration

## 🐛 Dépannage

### L'EXE ne démarre pas
```bash
# Vérifier les privilèges
- Clic droit → "Exécuter en tant qu'administrateur"

# Vérifier l'antivirus
- Ajouter une exception pour le dossier d'installation

# Vérifier Windows Defender
- Autoriser l'application dans la protection en temps réel
```

### Port 5000 déjà utilisé
```bash
# Arrêter les autres services sur le port 5000
netstat -ano | findstr :5000
taskkill /PID [PID_NUMBER] /F
```

### Problèmes de réseau
```bash
# Vérifier la connectivité des serveurs NTP locaux
ping 192.168.10.28
ping 192.168.10.45

# Tester les ports NTP
telnet 192.168.10.28 123
```

## 🔄 Mise à Jour

Pour mettre à jour l'application :

1. **Arrêter** l'application existante
2. **Sauvegarder** le dossier `%USERPROFILE%/NTP_Monitor_Data/`
3. **Remplacer** l'EXE par la nouvelle version
4. **Redémarrer** l'application

## 📞 Support

En cas de problème :

1. **Vérifier les logs** : `%USERPROFILE%/NTP_Monitor_Data/logs/`
2. **Tester en mode développement** : Installation Python classique
3. **Reconstruire l'EXE** : Script `build_installer.py`

## 🏗️ Construction Avancée

### Personnalisation du Build

Modifiez `build_installer.py` pour :
- **Changer l'icône** : Remplacez `resources/icon.ico`
- **Modifier les métadonnées** : Éditez `version_info.txt`
- **Ajouter des dépendances** : Section `hiddenimports`
- **Exclure des fichiers** : Section `excludes`

### Options PyInstaller

```python
# Build avec debug activé
--debug=all

# Build sans console
--windowed

# Build avec icône personnalisée
--icon=mon_icone.ico

# Build avec taille optimisée
--onefile --optimize=2
```

---

**🎉 Votre application NTP Monitor Enterprise est maintenant prête pour un déploiement professionnel sur Windows 11 !** 