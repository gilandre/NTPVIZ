# 🔬 GUIDE DE DÉBOGAGE - ERREUR 500 PERSISTANTE

## 🎯 Situation Actuelle
- ✅ Script de correction exécuté avec succès
- ❌ Erreur 500 "Internal Server Error" persiste
- 🎯 **Objectif** : Identifier la cause racine exacte

## 🚀 SOLUTION AUTOMATIQUE (Recommandée)

### Script de Diagnostic Avancé
```bash
wget -O - https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deployment/scripts/debug-500-advanced.sh | sudo bash
```

**Ce script va :**
1. 🔍 **Capturer l'erreur en temps réel** pendant que vous testez l'accès
2. 🧪 **Tester chaque composant** individuellement (Python, Flask, WSGI)
3. 📋 **Analyser les logs** Apache en détail
4. 🔧 **Appliquer des corrections avancées** basées sur l'erreur détectée
5. 📊 **Générer un rapport complet** pour diagnostic

## 🔍 DIAGNOSTIC MANUEL RAPIDE

Si vous préférez diagnostiquer manuellement :

### 1. Capture de l'Erreur Exacte
```bash
# Vider les logs précédents
sudo truncate -s 0 /var/log/apache2/ntp-monitor_error.log
sudo truncate -s 0 /var/log/apache2/error.log

# Surveiller les logs en temps réel
sudo tail -f /var/log/apache2/ntp-monitor_error.log &
sudo tail -f /var/log/apache2/error.log &

# MAINTENANT : Accédez à http://79.137.36.66 dans votre navigateur
# Puis regardez les erreurs qui apparaissent
```

### 2. Test Direct de l'Application
```bash
cd /var/www/ntp-monitor-enterprise
sudo -u ntpmonitor ./venv/bin/python -c "
import sys
sys.path.insert(0, '/var/www/ntp-monitor-enterprise')
from app import app
print('✅ Application OK')
"
```

### 3. Test du Fichier WSGI
```bash
cd /var/www/ntp-monitor-enterprise
sudo -u ntpmonitor ./venv/bin/python app.wsgi
```

### 4. Vérification Configuration Apache
```bash
# Vérifier la configuration
sudo apache2ctl configtest

# Vérifier les sites activés
sudo a2ensite

# Vérifier le module WSGI
sudo a2enmod wsgi
```

## 🔧 CORRECTIONS FRÉQUENTES

### Problème A : Erreur d'Import Python
```bash
# Si vous voyez "ModuleNotFoundError" ou "ImportError"
cd /var/www/ntp-monitor-enterprise
sudo -u ntpmonitor ./venv/bin/pip install --force-reinstall -r requirements.txt
```

### Problème B : Problème de Base de Données
```bash
# Réinitialiser la base de données
cd /var/www/ntp-monitor-enterprise
sudo -u ntpmonitor ./venv/bin/python init_database.py init
```

### Problème C : Fichier WSGI Corrompu
```bash
# Recréer le fichier WSGI
sudo tee /var/www/ntp-monitor-enterprise/app.wsgi > /dev/null << 'EOF'
#!/usr/bin/python3
import sys
import os

# Configuration du path
sys.path.insert(0, "/var/www/ntp-monitor-enterprise/")
os.chdir("/var/www/ntp-monitor-enterprise")

# Activer l'environnement virtuel
import site
site.addsitedir('/var/www/ntp-monitor-enterprise/venv/lib/python3.12/site-packages')

# Import de l'application
from app import app as application

if __name__ == "__main__":
    application.run()
EOF

sudo chmod +x /var/www/ntp-monitor-enterprise/app.wsgi
sudo chown ntpmonitor:www-data /var/www/ntp-monitor-enterprise/app.wsgi
sudo systemctl restart apache2
```

### Problème D : Permissions Incorrectes
```bash
cd /var/www/ntp-monitor-enterprise
sudo chown -R ntpmonitor:www-data ./
sudo chmod -R 755 ./
sudo chmod +x app.py app.wsgi
sudo mkdir -p logs instance
sudo chmod 775 logs instance
```

## 📊 ERREURS COMMUNES ET SOLUTIONS

### "No module named 'app'"
```bash
# Solution : Vérifier le path Python
cd /var/www/ntp-monitor-enterprise
ls -la app.py  # Doit exister
sudo -u ntpmonitor ./venv/bin/python -c "import sys; print(sys.path)"
```

### "Working outside of application context"
```bash
# Solution : Cette erreur a été corrigée, mettre à jour
cd /var/www/ntp-monitor-enterprise
git pull origin dev
sudo systemctl restart apache2
```

### "Cannot connect to database"
```bash
# Solution : Vérifier la base de données
cd /var/www/ntp-monitor-enterprise
sudo -u ntpmonitor ./venv/bin/python -c "
from app import app
from backend.app import db
with app.app_context():
    db.create_all()
    print('✅ Base de données OK')
"
```

### "Permission denied"
```bash
# Solution : Corriger les permissions
sudo chown -R ntpmonitor:www-data /var/www/ntp-monitor-enterprise
sudo chmod +x /var/www/ntp-monitor-enterprise/app.wsgi
```

## 🎯 ÉTAPES DE VALIDATION

Après chaque correction, testez :

1. **Configuration Apache :**
   ```bash
   sudo apache2ctl configtest
   ```

2. **Redémarrage Apache :**
   ```bash
   sudo systemctl restart apache2
   sudo systemctl status apache2
   ```

3. **Test d'accès :**
   ```bash
   curl -I http://localhost
   ```

4. **Test application :**
   ```bash
   cd /var/www/ntp-monitor-enterprise
   sudo -u ntpmonitor ./venv/bin/python -c "from app import app; print('OK')"
   ```

## 📞 SUPPORT AVANCÉ

Si l'erreur persiste après toutes ces étapes :

1. **Exécutez le script de diagnostic avancé**
2. **Partagez les logs générés** dans `/tmp/ntp-debug-*.log`
3. **Consultez les logs WSGI** : `/var/log/apache2/wsgi-debug.log`

## 🔗 LIENS UTILES

- **Logs en temps réel :** `sudo tail -f /var/log/apache2/ntp-monitor_error.log`
- **Status Apache :** `sudo systemctl status apache2`
- **Configuration Apache :** `sudo apache2ctl -S`
- **Modules Apache :** `sudo apache2ctl -M | grep wsgi`

---

**💡 ASTUCE :** L'erreur 500 indique que l'application Django/Flask tente de se lancer mais rencontre un problème spécifique. Avec le diagnostic avancé, nous identifierons exactement lequel ! 