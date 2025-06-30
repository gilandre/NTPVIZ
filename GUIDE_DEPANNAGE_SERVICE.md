# 🛠️ GUIDE DE DÉPANNAGE - NTP MONITOR ENTERPRISE

## 🔧 Erreur 500 - Internal Server Error

### 🎯 Symptômes
- Page d'erreur Apache : "Internal Server Error"
- Message : "The server encountered an internal error or misconfiguration"
- Code d'erreur HTTP 500

### 🚀 Solution Automatique (Recommandée)

**Script de diagnostic et correction complet :**
```bash
wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/fix-apache-500-error.sh | sudo bash
```

### 🔍 Diagnostic Manuel

#### 1. Vérification des logs Apache
```bash
# Logs spécifiques à l'application
sudo tail -f /var/log/apache2/ntp-monitor_error.log

# Logs généraux Apache
sudo tail -f /var/log/apache2/error.log
```

#### 2. Test de l'environnement Python
```bash
cd /var/www/ntp-monitor-enterprise
sudo -u ntpmonitor ./venv/bin/python --version
sudo -u ntpmonitor ./venv/bin/python -c "import flask; print('Flask OK')"
```

#### 3. Test des imports de l'application
```bash
cd /var/www/ntp-monitor-enterprise
sudo -u ntpmonitor ./venv/bin/python -c "from app import app; print('App OK')"
```

### 🔧 Corrections Étape par Étape

#### Étape 1 : Vérification du fichier WSGI
```bash
# Vérifier l'existence
ls -la /var/www/ntp-monitor-enterprise/app.wsgi

# Recréer si nécessaire
sudo tee /var/www/ntp-monitor-enterprise/app.wsgi > /dev/null << 'EOF'
#!/usr/bin/python3
import sys
import os

# Ajouter le répertoire de l'application au path
sys.path.insert(0, "/var/www/ntp-monitor-enterprise/")

# Activer l'environnement virtuel
import site
site.addsitedir('/var/www/ntp-monitor-enterprise/venv/lib/python3.12/site-packages')

try:
    from app import app as application
except ImportError as e:
    import logging
    logging.basicConfig(filename='/var/log/apache2/wsgi-error.log', level=logging.ERROR)
    logging.error(f"Erreur import dans WSGI: {e}")
    raise

if __name__ == "__main__":
    application.run()
EOF

sudo chmod +x /var/www/ntp-monitor-enterprise/app.wsgi
sudo chown ntpmonitor:www-data /var/www/ntp-monitor-enterprise/app.wsgi
```

#### Étape 2 : Correction des permissions
```bash
cd /var/www/ntp-monitor-enterprise
sudo chown -R ntpmonitor:www-data ./
sudo chmod -R 755 ./
sudo chmod +x app.py app.wsgi
sudo mkdir -p logs instance
sudo chmod 775 logs instance
```

#### Étape 3 : Vérification de la base de données
```bash
cd /var/www/ntp-monitor-enterprise
sudo -u ntpmonitor ./venv/bin/python init_database.py check
# Si erreur :
sudo -u ntpmonitor ./venv/bin/python init_database.py init
```

#### Étape 4 : Test du module WSGI d'Apache
```bash
sudo a2enmod wsgi
sudo apache2ctl configtest
sudo systemctl restart apache2
```

### 🧪 Script de Test Intégré

Le script de correction crée automatiquement un fichier de test :
```bash
cd /var/www/ntp-monitor-enterprise
sudo -u ntpmonitor ./venv/bin/python test_app.py
```

## 🔧 Autres Problèmes Courants

### 🐍 Erreur "Working outside of application context"
```bash
# Visible dans les logs
sudo tail -f /var/log/apache2/ntp-monitor_error.log | grep "Working outside"
```

**Solution :** Cette erreur a été corrigée dans la version actuelle. Si elle persiste :
```bash
cd /var/www/ntp-monitor-enterprise
git pull origin dev
sudo systemctl restart apache2
```

### 📦 Erreur "Cannot import 'setuptools.build_meta'"
```bash
# Lancer le script de correction setuptools
wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/fix-python312-setuptools.sh | sudo bash
```

### 🔌 Problème de connexion à la base de données
```bash
# Vérifier la base de données
cd /var/www/ntp-monitor-enterprise
sudo -u ntpmonitor ./venv/bin/python -c "
from app import app
from backend.app import db
with app.app_context():
    db.create_all()
    print('Base de données OK')
"
```

### 🌐 Module WSGI non activé
```bash
sudo a2enmod wsgi
sudo systemctl restart apache2
```

## 🔍 Commandes de Diagnostic Utiles

### Logs en temps réel
```bash
# Logs spécifiques de l'application
sudo tail -f /var/log/apache2/ntp-monitor_error.log

# Logs généraux Apache
sudo tail -f /var/log/apache2/error.log

# Logs système
sudo journalctl -u apache2 -f
```

### Status des services
```bash
# Apache
sudo systemctl status apache2
sudo systemctl is-active apache2

# Processus Python
ps aux | grep python
ps aux | grep wsgi
```

### Test de connectivité
```bash
# Test local
curl -I http://localhost
curl -I http://$(hostname -I | awk '{print $1}')

# Test depuis l'extérieur
curl -I http://79.137.36.66
```

### Vérification des ports
```bash
sudo netstat -tulpn | grep :80
sudo ss -tulpn | grep :80
```

## 🚨 Procédure d'Urgence

Si l'application ne répond toujours pas après toutes les corrections :

### 1. Redémarrage complet
```bash
sudo systemctl stop apache2
sudo systemctl start apache2
sudo systemctl status apache2
```

### 2. Vérification de la configuration Apache
```bash
sudo apache2ctl configtest
sudo a2ensite ntp-monitor.conf
sudo a2dissite 000-default.conf
sudo systemctl reload apache2
```

### 3. Réinstallation de l'environnement Python
```bash
cd /var/www/ntp-monitor-enterprise
sudo rm -rf venv
sudo -u ntpmonitor python3 -m venv venv
sudo -u ntpmonitor ./venv/bin/pip install --upgrade pip setuptools wheel
sudo -u ntpmonitor ./venv/bin/pip install -r requirements.txt
sudo systemctl restart apache2
```

### 4. Contact Support
Si le problème persiste, fournir ces informations :
```bash
# Collecter les informations de debug
echo "=== INFORMATIONS SYSTÈME ===" > debug_info.txt
uname -a >> debug_info.txt
echo "=== PYTHON VERSION ===" >> debug_info.txt
python3 --version >> debug_info.txt
echo "=== APACHE STATUS ===" >> debug_info.txt
sudo systemctl status apache2 >> debug_info.txt
echo "=== LOGS RÉCENTS ===" >> debug_info.txt
sudo tail -20 /var/log/apache2/ntp-monitor_error.log >> debug_info.txt
echo "=== CONFIGURATION SITES ===" >> debug_info.txt
sudo apache2ctl -S >> debug_info.txt
```

## 📋 Checklist de Vérification

Avant de déclarer l'application fonctionnelle :

- [ ] Apache démarre sans erreur
- [ ] Module WSGI activé
- [ ] Fichier WSGI existe et est exécutable
- [ ] Permissions correctes sur tous les fichiers
- [ ] Base de données initialisée
- [ ] Environnement virtuel Python fonctionnel
- [ ] Imports Python fonctionnent
- [ ] Configuration Apache valide
- [ ] Site ntp-monitor activé
- [ ] Site default désactivé
- [ ] Logs sans erreur critique
- [ ] Page d'accueil accessible

## 🎯 URLs de Test

Une fois l'application fonctionnelle :
- **Page principale :** http://79.137.36.66
- **Page de connexion :** http://79.137.36.66/auth/login
- **API Status :** http://79.137.36.66/api/status

**Identifiants par défaut :**
- Utilisateur : `admin`
- Mot de passe : `admin123`

# Guide de Dépannage - "Service inactif / Port undefined"

## 🚨 Problème Identifié

L'interface NTP Monitor Enterprise affiche :
- "Service inactif"
- "Port undefined"

## 🔧 Solutions Rapides (par ordre de probabilité)

### 1. Solution Simple - Actualiser la Page
**⏱️ Temps : 5 secondes**

Dans votre navigateur :
- Appuyez sur `F5` ou `Ctrl+F5`
- Ou cliquez sur le bouton actualiser

### 2. Redémarrer l'Application NTP Monitor
**⏱️ Temps : 1 minute**

1. Fermez la fenêtre de l'application NTP Monitor
2. Double-cliquez sur le raccourci bureau "NTP Monitor Enterprise"
3. Attendez le chargement complet
4. Connectez-vous avec admin/admin123

### 3. Diagnostic Automatique
**⏱️ Temps : 2 minutes**

Exécutez le script de diagnostic :

```bash
python fix_service_port_issue.py
```

Ce script va :
- ✅ Vérifier si l'application est accessible
- ✅ Tester l'endpoint de service
- ✅ Contrôler le port NTP 123
- ✅ Vérifier les services système
- ✅ Générer un rapport détaillé

## 🔍 Diagnostic Manuel

### Étape 1 : Vérifier l'Application
Ouvrez votre navigateur et allez sur :
```
http://127.0.0.1:5000
```

**Si la page ne charge pas :**
- L'application n'est pas démarrée
- ➡️ Solution : Redémarrer l'application

### Étape 2 : Tester l'API
Dans votre navigateur, allez sur :
```
http://127.0.0.1:5000/api/ntp/service/status
```

**Réponse attendue :**
```json
{
  "service_status": "active",
  "port": 123,
  "port_listening": true,
  "active_connections": 0
}
```

**Si "port": null ou undefined :**
- Problème dans le backend
- ➡️ Solution : Redémarrer l'application

### Étape 3 : Vérifier le Service NTP Système
```bash
# Vérifier les services NTP
systemctl status ntpsec
systemctl status ntp
systemctl status systemd-timesyncd

# Vérifier le port 123
netstat -tulpn | grep :123
```

## 🛠️ Solutions Avancées

### Service NTP Manquant

**Sur Ubuntu/Debian :**
```bash
# Option 1 : Installer ntpsec
sudo apt update
sudo apt install ntpsec
sudo systemctl enable --now ntpsec

# Option 2 : Utiliser systemd-timesyncd
sudo systemctl enable --now systemd-timesyncd
```

**Sur CentOS/RHEL :**
```bash
# Installer chrony
sudo dnf install chrony
sudo systemctl enable --now chronyd
```

### Problème de Permissions
```bash
# Donner les permissions pour lire les connexions réseau
sudo setcap cap_net_raw+ep /usr/bin/python3
```

### Réinitialiser la Configuration
```bash
# Sauvegarder et réinitialiser la base de données
mv instance/ntp_monitor_dev.db instance/ntp_monitor_dev.db.bak
python -c "from backend.app import create_app; from backend.utils.init_data import init_database; app = create_app(); app.app_context().push(); init_database()"
```

## 📊 Logs de Débogage

### Consulter les Logs
```bash
# Logs application
tail -f logs/app.log

# Logs système NTP
sudo journalctl -u ntpsec -f
sudo journalctl -u systemd-timesyncd -f
```

### Activer le Mode Debug
Modifier `app.py` :
```python
# Changer DEBUG à True temporairement
app.config['DEBUG'] = True
```

## ⚡ Solutions par Symptôme

| Symptôme | Cause Probable | Solution |
|----------|----------------|----------|
| Application inaccessible | App non démarrée | Redémarrer l'application |
| "Port undefined" | Endpoint défaillant | Actualiser la page + redémarrer |
| "Service inactif" | Service NTP absent | Installer ntpsec/ntp |
| Erreur 500 API | Erreur backend | Consulter logs/app.log |
| Connexion refusée | Port 5000 occupé | Changer de port ou redémarrer |

## 🆘 Contact Support

Si le problème persiste :

1. **Exécutez le diagnostic :**
   ```bash
   python fix_service_port_issue.py
   ```

2. **Collectez les informations :**
   - Fichier `diagnostic_report.json`
   - Logs dans `logs/app.log`
   - Version du système d'exploitation

3. **Informations système :**
   ```bash
   python --version
   pip list | grep -E "(flask|psutil|ntplib)"
   systemctl --version
   ```

## 📋 Checklist de Vérification

- [ ] Application NTP Monitor démarrée
- [ ] Page web accessible (http://127.0.0.1:5000)
- [ ] Endpoint API répond correctement
- [ ] Service NTP système actif
- [ ] Port 123 en écoute
- [ ] Connectivité réseau vers serveurs NTP
- [ ] Permissions système suffisantes
- [ ] Logs sans erreur critique

## 🔄 Remise à Zéro Complète

En dernier recours :

```bash
# 1. Arrêter l'application
# (Fermer la fenêtre)

# 2. Sauvegarder les données
cp -r instance/ instance_backup/

# 3. Réinstaller les dépendances
pip install --force-reinstall -r requirements.txt

# 4. Réinitialiser la base de données
rm -f instance/ntp_monitor_dev.db
python -c "from backend.app import create_app; from backend.utils.init_data import init_database; app = create_app(); app.app_context().push(); init_database()"

# 5. Redémarrer l'application
python app.py
```

---

**🎯 Dans 90% des cas, un simple `F5` dans le navigateur ou un redémarrage de l'application résout le problème !** 