# 🔧 Guide de Dépannage - Déploiement NTP Monitor Enterprise

## 🚨 Problèmes courants et solutions

### 1. Erreur de permissions Git

**Symptôme :**
```bash
error: cannot open '.git/FETCH_HEAD': Permission denied
```

**Solution :**
```bash
# Corriger les permissions du répertoire Git
sudo chown -R ubuntu:ubuntu /opt/ntp-monitor/.git/
sudo chown -R ubuntu:ubuntu /opt/ntp-monitor/

# Puis relancer le script
sudo ./deploy_ubuntu_complete.sh
```

### 2. Script refuse l'exécution en tant que root

**Symptôme :**
```bash
[ERROR] Ce script ne doit pas être exécuté en tant que root
```

**Solution :**
Le script a été corrigé pour supporter l'exécution en tant que root. Utilisez la dernière version :

```bash
# Télécharger la version corrigée
wget https://raw.githubusercontent.com/gilandre/NTPVIZ/MacDev/deployment/scripts/deploy_ubuntu_complete.sh
chmod +x deploy_ubuntu_complete.sh
sudo ./deploy_ubuntu_complete.sh
```

### 3. Erreur de schéma de base de données

**Symptôme :**
```bash
Unknown column 'users.last_login' in 'field list'
Unknown column 'ntp_servers.server_type' in 'field list'
```

**Solution :**
```bash
cd /opt/ntp-monitor
source .venv/bin/activate
python fix_database_schema.py
```

### 4. Service systemd ne démarre pas

**Vérification :**
```bash
sudo systemctl status ntp-monitor
sudo journalctl -u ntp-monitor -n 50
```

**Solutions possibles :**
```bash
# Vérifier les permissions
sudo chown -R ubuntu:ubuntu /opt/ntp-monitor/

# Redémarrer le service
sudo systemctl restart ntp-monitor

# Vérifier la configuration
sudo systemctl daemon-reload
```

### 5. Port 5001 déjà utilisé

**Vérification :**
```bash
sudo lsof -i :5001
```

**Solution :**
```bash
# Tuer le processus existant
sudo pkill -f "python.*app.py"

# Ou redémarrer le service
sudo systemctl restart ntp-monitor
```

### 6. Erreur de dépendances Python

**Symptôme :**
```bash
ModuleNotFoundError: No module named 'flask_login.test_client'
```

**Solution :**
```bash
cd /opt/ntp-monitor
source .venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### 7. Erreur de connexion MySQL

**Vérification :**
```bash
sudo systemctl status mysql
sudo mysql -u ntp_user -p
```

**Solution :**
```bash
# Redémarrer MySQL
sudo systemctl restart mysql

# Vérifier la configuration
sudo mysql -e "SHOW DATABASES;"
```

## 🛠️ Commandes de diagnostic

### Vérification complète du système
```bash
# Statut des services
sudo systemctl status ntp-monitor mysql

# Logs récents
sudo journalctl -u ntp-monitor -n 20

# Vérification de l'application
curl -s http://localhost:5001/ | head -5

# Test de l'environnement Python
cd /opt/ntp-monitor
source .venv/bin/activate
python -c "from backend.app import create_app; app = create_app(); print('✅ OK')"
```

### Vérification de la base de données
```bash
cd /opt/ntp-monitor
source .venv/bin/activate

# Test de connexion
python -c "
from backend.database_manager import get_db_session_with_context
from backend.models.user import User
with get_db_session_with_context() as session:
    users = session.query(User).count()
    print(f'✅ {users} utilisateurs trouvés')
"
```

### Correction automatique
```bash
# Script de correction du schéma
python fix_database_schema.py

# Script d'harmonisation des modèles
python harmonize_models.py

# Script de vérification
python verify_deployment_scripts.py
```

## 🔄 Procédure de récupération

### En cas de problème majeur
```bash
# 1. Arrêter le service
sudo systemctl stop ntp-monitor

# 2. Sauvegarder la configuration
cp /opt/ntp-monitor/.env /opt/ntp-monitor/.env.backup

# 3. Nettoyer et redéployer
sudo rm -rf /opt/ntp-monitor
sudo ./deploy_ubuntu_complete.sh

# 4. Restaurer la configuration
cp /opt/ntp-monitor/.env.backup /opt/ntp-monitor/.env
```

### Rollback vers une version précédente
```bash
# Utiliser le script de mise à jour avec rollback
./update_deployment.sh rollback
```

## 📞 Support

### Informations utiles
- **URL de l'application** : `http://votre-serveur-ip:5001`
- **Utilisateur par défaut** : `admin`
- **Mot de passe par défaut** : `admin123`
- **Répertoire de l'application** : `/opt/ntp-monitor`
- **Logs du service** : `sudo journalctl -u ntp-monitor -f`

### Commandes de gestion
```bash
# Redémarrer le service
sudo systemctl restart ntp-monitor

# Voir les logs en temps réel
sudo journalctl -u ntp-monitor -f

# Vérifier le statut
sudo systemctl status ntp-monitor

# Arrêter le service
sudo systemctl stop ntp-monitor
```

## ✅ Validation finale

Après résolution des problèmes, vérifiez que :

1. ✅ **Le service démarre** : `sudo systemctl status ntp-monitor`
2. ✅ **L'application répond** : `curl -s http://localhost:5001/`
3. ✅ **La base de données fonctionne** : Test de connexion réussi
4. ✅ **Les logs sont propres** : `sudo journalctl -u ntp-monitor -n 20`

## 🎯 Résolution rapide

Pour la plupart des problèmes, cette séquence résout 90% des cas :

```bash
# 1. Corriger les permissions
sudo chown -R ubuntu:ubuntu /opt/ntp-monitor/

# 2. Corriger le schéma de base de données
cd /opt/ntp-monitor
source .venv/bin/activate
python fix_database_schema.py

# 3. Redémarrer le service
sudo systemctl restart ntp-monitor

# 4. Vérifier
sudo systemctl status ntp-monitor
curl -s http://localhost:5001/ | head -5
``` 