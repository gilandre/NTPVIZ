# Solution mod_wsgi pour Ubuntu 24.04

## 🚨 **Problème Identifié**

Sur Ubuntu 24.04, l'installation de `mod_wsgi==5.0.0` via pip échoue avec l'erreur :
```
RuntimeError: The 'apxs' command appears not to be installed
```

## 🔧 **Cause du Problème**

- `mod_wsgi` dans `requirements.txt` essaie de se compiler depuis les sources
- Il manque les headers Apache de développement
- Sur Ubuntu, `mod_wsgi` doit être installé via `apt`, pas `pip`

## ✅ **Solutions Disponibles**

### **Solution 1 : Déploiement Complet (Recommandé)**

Pour une nouvelle installation :
```bash
# Télécharger le script final
wget https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deploy_ubuntu24_final.sh
chmod +x deploy_ubuntu24_final.sh
sudo ./deploy_ubuntu24_final.sh
```

**Avantages :**
- Installation mod_wsgi système automatique
- Requirements.txt corrigé automatiquement
- Gestion complète Ubuntu 24.04 (Python 3.12, chrony, etc.)
- Configuration Apache optimisée

### **Solution 2 : Correction Rapide**

Si vous avez déjà le projet cloné :
```bash
# Exécuter le script de correction
sudo ./fix_mod_wsgi_ubuntu.sh
```

**Ce que fait ce script :**
1. Installe `libapache2-mod-wsgi-py3` via apt
2. Crée `requirements_ubuntu.txt` sans mod_wsgi
3. Réinstalle les dépendances Python
4. Active mod_wsgi dans Apache

### **Solution 3 : Manuelle**

Si vous préférez faire les corrections manuellement :

```bash
# 1. Installer mod_wsgi système
sudo apt update
sudo apt install -y libapache2-mod-wsgi-py3 apache2-dev

# 2. Créer requirements sans mod_wsgi
cp requirements.txt requirements_ubuntu.txt
sed -i '/mod_wsgi/d' requirements_ubuntu.txt

# 3. Réinstaller dépendances
cd /home/ntp-monitor/ntp-monitor-enterprise
source venv/bin/activate
pip install -r requirements_ubuntu.txt

# 4. Activer mod_wsgi
sudo a2enmod wsgi
sudo systemctl restart apache2
```

## 🔍 **Vérification Installation**

Après correction, vérifiez que mod_wsgi est bien chargé :
```bash
# Vérifier module Apache
sudo apache2ctl -M | grep wsgi

# Sortie attendue :
# wsgi_module (shared)
```

## 📋 **Requirements.txt Corrigé**

Le fichier `requirements_ubuntu.txt` exclut mod_wsgi :
```python
# mod_wsgi est installé via apt, pas pip
Flask==2.3.3
Werkzeug==2.3.7
SQLAlchemy==2.0.21
PyMySQL==1.1.0
# ... autres dépendances
```

## 🛠️ **Configuration Apache**

Le mod_wsgi système est configuré dans le Virtual Host :
```apache
<VirtualHost *:80>
    # ...
    WSGIDaemonProcess ntp-monitor-enterprise python-home=/home/ntp-monitor/ntp-monitor-enterprise/venv
    WSGIProcessGroup ntp-monitor-enterprise
    WSGIScriptAlias / /home/ntp-monitor/ntp-monitor-enterprise/app.wsgi
    # ...
</VirtualHost>
```

## 🧪 **Tests**

Après installation, testez :
```bash
# Status services
sudo systemctl status ntp-monitor-enterprise
sudo systemctl status apache2

# Test accès web
curl http://localhost
```

## 🎯 **Avantages Solution Système**

- **Performance** : Module compilé optimisé
- **Stabilité** : Testé avec Ubuntu 24.04
- **Maintenance** : Mises à jour automatiques via apt
- **Sécurité** : Pas de compilation sur serveur production

## 🔄 **Redémarrage Services**

Après correction :
```bash
sudo systemctl restart ntp-monitor-enterprise
sudo systemctl restart apache2
```

## 📊 **Monitoring**

Surveillez les logs Apache :
```bash
sudo tail -f /var/log/apache2/ntp-monitor-enterprise_error.log
```

## 🎉 **Résultat**

✅ mod_wsgi système fonctionnel
✅ Application accessible via Apache
✅ Performances optimisées
✅ Compatible Ubuntu 24.04 