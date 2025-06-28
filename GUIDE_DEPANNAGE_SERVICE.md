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