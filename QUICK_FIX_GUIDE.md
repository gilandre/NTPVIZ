# 🚀 Guide de Résolution Rapide - Erreurs de Schéma

## 🚨 Erreur détectée : `Unknown column 'ntp_servers.status' in 'field list'`

### ✅ Solution immédiate :

```bash
# 1. Aller dans le répertoire de l'application
cd /opt/ntp-monitor

# 2. Activer l'environnement virtuel
source .venv/bin/activate

# 3. Exécuter le script de correction du schéma
python fix_database_schema.py

# 4. Redémarrer le service
sudo systemctl restart ntp-monitor

# 5. Vérifier que tout fonctionne
sudo systemctl status ntp-monitor
curl -s http://localhost:5001/ | head -5
```

### 🔧 Si le script de correction n'est pas disponible :

```bash
# 1. Télécharger la dernière version depuis GitHub
cd /opt/ntp-monitor
sudo -u ubuntu git fetch origin
sudo -u ubuntu git reset --hard origin/MacDev

# 2. Exécuter la correction
source .venv/bin/activate
python fix_database_schema.py

# 3. Redémarrer
sudo systemctl restart ntp-monitor
```

### 📊 Vérification que la correction a fonctionné :

```bash
# Test de connexion à la base de données
cd /opt/ntp-monitor
source .venv/bin/activate

python -c "
from backend.database_manager import get_db_session_with_context
from backend.models.ntp_server import NTPServer
with get_db_session_with_context() as session:
    servers = session.query(NTPServer).count()
    print(f'✅ {servers} serveurs NTP trouvés')
"
```

## 🎯 Résultat attendu :

```
✅ Schéma de base de données vérifié et corrigé
✅ Toutes les colonnes requises sont présentes dans ntp_servers
🎉 Base de données prête pour l'application!
```

## 📞 En cas de problème persistant :

1. **Vérifier les logs** : `sudo journalctl -u ntp-monitor -n 20`
2. **Vérifier MySQL** : `sudo systemctl status mysql`
3. **Redémarrer MySQL** : `sudo systemctl restart mysql`
4. **Relancer le déploiement complet** : `sudo ./deploy_ubuntu_complete.sh`

## ✅ Validation finale :

Après la correction, vérifiez que :
- ✅ Le service démarre : `sudo systemctl status ntp-monitor`
- ✅ L'application répond : `curl -s http://localhost:5001/`
- ✅ La base de données fonctionne : Test de connexion réussi

## 🎉 Succès !

L'erreur de schéma de base de données est maintenant résolue et l'application devrait fonctionner correctement ! 