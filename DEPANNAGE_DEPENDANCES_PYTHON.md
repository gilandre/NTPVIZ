# 🔧 Dépannage des Dépendances Python

## 🚨 Problème rencontré

**Erreur** : `No module named 'flask_login'`

**Cause** : Les dépendances Python ne sont pas correctement installées dans l'environnement virtuel.

## ⚡ Solution rapide

### **1. Correction manuelle sur le serveur :**

```bash
# Connexion au serveur
ssh root@votre-serveur-ip

# Accès au répertoire de l'application
cd /opt/ntp-monitor

# Activation de l'environnement virtuel
source .venv/bin/activate

# Vérification de l'environnement
which python
python --version

# Installation des dépendances manquantes
pip install flask-login flask-socketio

# Test de l'application
python quick_verification.py
```

### **2. Utilisation du script de correction :**

```bash
# Téléchargement du script de correction
wget https://raw.githubusercontent.com/votre-username/NTPVIZ/MacDev/fix_python_dependencies.sh

# Exécution
chmod +x fix_python_dependencies.sh
./fix_python_dependencies.sh
```

## 🔍 Diagnostic

### **Vérification de l'environnement virtuel :**

```bash
# Vérifier si l'environnement virtuel est activé
echo $VIRTUAL_ENV

# Vérifier le chemin Python
which python

# Vérifier les modules installés
pip list | grep flask
```

### **Vérification des dépendances :**

```bash
# Lister toutes les dépendances installées
pip list

# Vérifier les modules spécifiques
python -c "import flask_login; print('✅ Flask-Login OK')"
python -c "import flask_socketio; print('✅ Flask-SocketIO OK')"
```

## 🛠️ Solutions détaillées

### **Solution 1 : Réinstallation complète des dépendances**

```bash
cd /opt/ntp-monitor
source .venv/bin/activate

# Suppression et recréation de l'environnement virtuel
deactivate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate

# Installation des dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

### **Solution 2 : Installation manuelle des modules manquants**

```bash
cd /opt/ntp-monitor
source .venv/bin/activate

# Installation des modules spécifiques
pip install flask-login
pip install flask-socketio
pip install sqlalchemy
pip install pymysql
```

### **Solution 3 : Vérification du fichier requirements.txt**

```bash
# Vérifier le contenu du fichier requirements.txt
cat requirements.txt

# S'assurer que flask-login est présent
grep flask-login requirements.txt
```

## 📋 Checklist de vérification

### ✅ **Avant l'exécution :**
- [ ] Environnement virtuel activé
- [ ] Répertoire de l'application accessible
- [ ] Fichier requirements.txt présent

### ✅ **Après l'installation :**
- [ ] Flask installé : `python -c "import flask"`
- [ ] Flask-Login installé : `python -c "import flask_login"`
- [ ] Flask-SocketIO installé : `python -c "import flask_socketio"`
- [ ] SQLAlchemy installé : `python -c "import sqlalchemy"`
- [ ] PyMySQL installé : `python -c "import pymysql"`

### ✅ **Test final :**
- [ ] Script de vérification rapide : `python quick_verification.py`
- [ ] Application démarre : `python app.py`

## 🚨 Problèmes courants

### **1. Environnement virtuel non activé**
```bash
# Symptôme : python pointe vers /usr/bin/python au lieu de .venv/bin/python
# Solution :
source .venv/bin/activate
```

### **2. Permissions insuffisantes**
```bash
# Symptôme : Permission denied lors de l'installation
# Solution :
sudo chown -R $USER:$USER /opt/ntp-monitor/.venv
```

### **3. Cache pip corrompu**
```bash
# Symptôme : Erreurs d'installation répétées
# Solution :
pip cache purge
pip install --no-cache-dir -r requirements.txt
```

### **4. Version Python incompatible**
```bash
# Symptôme : Erreurs de compilation
# Solution :
python3 --version  # Vérifier la version
# Si nécessaire, installer Python 3.9+ :
sudo apt install python3.9 python3.9-venv
```

## 📞 Support avancé

### **Logs détaillés :**
```bash
# Activer les logs détaillés
pip install -v flask-login

# Vérifier les logs d'erreur
tail -f /opt/ntp-monitor/logs/error.log
```

### **Test de connectivité :**
```bash
# Test de la base de données
python -c "from backend.database_manager import get_db_session_with_context; print('✅ DB OK')"

# Test de l'application
python -c "from backend.app import create_app; print('✅ App OK')"
```

---

**🎯 Objectif :** Assurer que toutes les dépendances Python sont correctement installées dans l'environnement virtuel.

**✅ Résultat attendu :** L'application démarre sans erreur de module manquant. 