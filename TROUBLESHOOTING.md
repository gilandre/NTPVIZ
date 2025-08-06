# 🔧 Guide de Dépannage NTPVIZ

## Erreurs Courantes et Solutions

### 1. Erreurs de Connexion à la Base de Données

#### Problème : "Database Manager non initialisé"
```
ERROR - Database Manager non initialisé après 3 tentatives
```

**Solutions :**
```bash
# 1. Vérifier que MySQL est démarré
sudo systemctl status mysql  # Linux
brew services list | grep mysql  # macOS

# 2. Tester la connexion MySQL
mysql -u ntp_user -p'NTP_Monitor_2025!' -e "USE ntp_monitor; SHOW TABLES;"

# 3. Réinitialiser la base de données
python3 -c "
from backend.database_manager import db_manager
from backend.database import Base
from backend.utils.init_data import init_default_data

db_manager.initialize()
Base.metadata.create_all(db_manager.engine)
init_default_data()
print('Base de données réinitialisée')
"
```

### 2. Erreurs de Port Occupé

#### Problème : "Address already in use"
```
Port 5000 is in use by another program
```

**Solutions :**
```bash
# 1. Identifier le processus qui utilise le port
lsof -i:5000  # ou lsof -i:5001

# 2. Arrêter le processus
kill -9 <PID>

# 3. Ou utiliser un port différent
export PORT=5001
python3 app.py
```

### 3. Erreurs NTP Tools

#### Problème : "ntpq non disponible"
```
INFO - ntpq non disponible sur ce système
```

**Solutions :**
```bash
# 1. Installer les outils NTP
./install_ntp_tools.sh

# 2. Vérifier l'installation
which ntpq
ntpq --version

# 3. Démarrer le service NTP (Linux)
sudo systemctl start ntp
sudo systemctl enable ntp
```

### 4. Erreurs de Processus

#### Problème : "Erreur lors de la récupération des connexions: (pid=XXXXX)"
```
ERROR - Erreur lors de la récupération des connexions: (pid=17009)
```

**Cause :** Le service essaie d'accéder à un processus qui n'existe plus ou n'est pas accessible.

**Solutions :**
- ✅ **Corrigé automatiquement** : Le code vérifie maintenant l'existence des processus
- L'erreur est maintenant en mode DEBUG et n'affecte pas le fonctionnement
- L'application utilise des méthodes alternatives si les processus ne sont pas accessibles

### 5. Erreurs de Permissions

#### Problème : "Permission denied"
```
ERROR - Permission denied
```

**Solutions :**
```bash
# 1. Vérifier les permissions des fichiers
ls -la

# 2. Corriger les permissions
chmod +x *.sh
chmod 755 frontend/static/

# 3. Vérifier les permissions de la base de données
sudo chown -R ntp-monitor:ntp-monitor /opt/ntp-monitor  # Linux
```

### 6. Erreurs de Dépendances

#### Problème : "Module not found"
```
ModuleNotFoundError: No module named 'flask'
```

**Solutions :**
```bash
# 1. Installer les dépendances
pip install -r requirements_simple.txt

# 2. Ou utiliser l'environnement virtuel
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_simple.txt
```

### 7. Erreurs de Configuration

#### Problème : "Configuration error"
```
ERROR - Configuration error
```

**Solutions :**
```bash
# 1. Vérifier le fichier de configuration
cat config/config.py

# 2. Créer un fichier .env
cp env.example .env

# 3. Modifier les variables d'environnement
nano .env
```

## 🔍 Diagnostic Automatique

### Script de Diagnostic
```bash
#!/bin/bash
echo "🔍 Diagnostic NTPVIZ..."

# Vérifier Python
echo "Python: $(python3 --version)"

# Vérifier les dépendances
echo "Dépendances installées:"
pip list | grep -E "(Flask|SQLAlchemy|PyMySQL)"

# Vérifier MySQL
echo "MySQL:"
mysql -u ntp_user -p'NTP_Monitor_2025!' -e "SELECT 1;" 2>/dev/null && echo "✅ Connecté" || echo "❌ Erreur connexion"

# Vérifier les ports
echo "Ports utilisés:"
lsof -i:5001 2>/dev/null || echo "Port 5001 libre"

# Vérifier les outils NTP
echo "Outils NTP:"
which ntpq 2>/dev/null && echo "✅ ntpq disponible" || echo "❌ ntpq manquant"
```

## 📋 Logs et Debug

### Niveaux de Log
```python
# Dans .env ou config
LOG_LEVEL=DEBUG  # Pour plus de détails
LOG_LEVEL=INFO   # Niveau normal
LOG_LEVEL=WARNING  # Seulement les avertissements
```

### Emplacement des Logs
- **Logs application** : `logs/app.log`
- **Logs système** : `journalctl -u ntp-monitor` (Linux)
- **Logs Nginx** : `/var/log/nginx/` (production)

### Commandes de Debug
```bash
# Voir les logs en temps réel
tail -f logs/app.log

# Tester l'API
curl http://localhost:5001/api/health

# Vérifier les processus
ps aux | grep python

# Tester la base de données
python3 -c "from backend.database_manager import db_manager; db_manager.initialize(); print('OK')"
```

## 🚀 Redémarrage Propre

### Séquence de Redémarrage
```bash
# 1. Arrêter l'application
pkill -f "python3.*app.py"

# 2. Vérifier qu'aucun processus ne reste
ps aux | grep python

# 3. Redémarrer avec le script robuste
python3 start_app.py

# 4. Vérifier le statut
curl http://localhost:5001/
```

## 📞 Support

### Informations à Fournir
En cas de problème persistant, fournissez :

1. **Système d'exploitation** : `uname -a`
2. **Version Python** : `python3 --version`
3. **Logs d'erreur** : `tail -50 logs/app.log`
4. **Configuration** : `cat .env` (sans les mots de passe)
5. **Statut des services** : `systemctl status mysql` (Linux)

### Ressources
- **Documentation API** : http://localhost:5001/api/docs
- **Guide Ubuntu** : `README_UBUNTU.md`
- **Issues GitHub** : [Repository Issues](https://github.com/gilandre/NTPVIZ/issues)

---

**NTPVIZ - Support Technique**  
Dernière mise à jour : 2025-01-06 