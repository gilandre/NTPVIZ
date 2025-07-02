# 🚨 SOLUTION URGENCE - Erreur 502 NTP Monitor

## Problème Identifié
Modules Python manquants : `python-dotenv` et `pytz`

## ⚡ Solution Rapide (5 minutes)

Connectez-vous au serveur et exécutez ces commandes **dans l'ordre** :

### 1. Arrêt du service
```bash
systemctl stop ntp-monitor
```

### 2. Installation des modules manquants
```bash
cd /opt/ntp-monitor
source .venv/bin/activate
pip install python-dotenv pytz --force-reinstall --no-cache-dir
```

### 3. Test rapide des modules
```bash
python -c "import dotenv, pytz; print('✅ Modules OK')"
```

### 4. Test de l'application
```bash
python -c "from backend.app import create_app; app = create_app(); print('✅ App OK')"
```

### 5. Redémarrage du service
```bash
systemctl start ntp-monitor
systemctl enable ntp-monitor
```

### 6. Vérification
```bash
# Attendre 10 secondes
sleep 10

# Vérifier le service
systemctl status ntp-monitor

# Vérifier le port
netstat -tlnp | grep :5000

# Test web
curl -I http://localhost:5000/
```

## 🎯 Résultat Attendu

- ✅ Service actif : `Active: active (running)`
- ✅ Port ouvert : `tcp 0.0.0.0:5000`
- ✅ Application accessible : `HTTP/1.1 200 OK`

## 🌐 Accès Final

Si tout fonctionne :
- **URL** : http://79.137.36.66/
- **Admin** : admin / admin123
- **Operator** : operator / operator123
- **Viewer** : viewer / viewer123

## 🚀 Solution Automatique (Alternative)

Si vous préférez un script automatique :

```bash
curl -fsSL https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deploy_fix_final.sh | sudo bash
```

## 📞 Support

Si problème persiste :
```bash
journalctl -u ntp-monitor -n 20
```

---
**⏱ Temps estimé : 5 minutes maximum** 