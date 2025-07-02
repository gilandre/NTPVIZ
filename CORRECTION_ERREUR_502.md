# Correction Erreur 502 - NTP Monitor Enterprise

## 🔴 Problème Identifié

Le serveur **79.137.36.66** présente une erreur 502 Bad Gateway due à plusieurs problèmes :

1. **Module Python manquant** : `ntplib` non installé
2. **Authentification MySQL** : Erreur d'accès pour l'utilisateur `root`
3. **Configuration manquante** : Fichier `.env` absent
4. **Service inactif** : Le service `ntp-monitor` ne démarre pas

## 🚀 Solution Automatique (Recommandée)

### Option 1 : Correction en Une Ligne

Connectez-vous au serveur et exécutez :

```bash
curl -fsSL https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deploy_fix_502.sh | sudo bash
```

### Option 2 : Téléchargement et Exécution Manuelle

```bash
# Téléchargement du script
wget https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/fix_502_complete.sh

# Rendre exécutable
chmod +x fix_502_complete.sh

# Exécuter la correction
sudo ./fix_502_complete.sh
```

## 🔧 Actions Effectuées par le Script

Le script de correction automatique :

### 1. **Installation des Outils Manquants**
- `net-tools` (pour netstat)
- `curl`, `wget`, `htop`, `tree`

### 2. **Correction des Dépendances Python**
- Installation de `ntplib`
- Réinstallation de `pymysql` et `cryptography`
- Réinstallation complète des requirements

### 3. **Création du Fichier .env**
```env
FLASK_ENV=production
DATABASE_TYPE=mysql
MYSQL_USER=ntp_app
MYSQL_PASSWORD=ntp_secure_2024
# ... autres configurations
```

### 4. **Configuration MySQL/MariaDB**
- Création de l'utilisateur `ntp_app`
- Création de la base de données `ntp_monitor`
- Attribution des privilèges
- **Fallback SQLite** en cas d'échec MySQL

### 5. **Initialisation Base de Données**
- Création des tables
- Ajout des données par défaut
- Comptes utilisateurs :
  - **Admin** : `admin` / `admin123`
  - **Operator** : `operator` / `operator123`
  - **Viewer** : `viewer` / `viewer123`

### 6. **Configuration Système**
- Permissions correctes pour l'utilisateur `ntp-monitor`
- Création des répertoires `logs/` et `instance/`
- Redémarrage du service systemd

## 📊 Vérification Post-Correction

Après exécution du script, vérifiez :

### 1. **Statut du Service**
```bash
systemctl status ntp-monitor
```

### 2. **Port d'Écoute**
```bash
netstat -tlnp | grep :5000
```

### 3. **Logs en Temps Réel**
```bash
journalctl -u ntp-monitor -f
```

### 4. **Test de Connectivité**
```bash
curl -f http://localhost:5000/
```

### 5. **Accès Web**
Ouvrez votre navigateur : **http://79.137.36.66/**

## 🐛 Diagnostic Manuel (Si Problème Persiste)

### Script de Diagnostic Rapide
```bash
# Créer le script de diagnostic
cat > /tmp/diagnostic.sh << 'EOF'
#!/bin/bash
echo "=== DIAGNOSTIC NTP MONITOR ==="
echo "Service:" && systemctl is-active ntp-monitor
echo "Port 5000:" && netstat -tlnp | grep :5000
echo "Processus Python:" && ps aux | grep python | grep -v grep
echo "Derniers logs:" && journalctl -u ntp-monitor -n 10 --no-pager
EOF

chmod +x /tmp/diagnostic.sh
sudo /tmp/diagnostic.sh
```

### Démarrage Manuel (Test)
```bash
cd /opt/ntp-monitor
source .venv/bin/activate
python app.py
```

## 🔄 Redéploiement Complet (Si Nécessaire)

Si la correction ne fonctionne pas, redéploiement complet :

```bash
curl -fsSL https://raw.githubusercontent.com/gilandre/NTPVIZ/dev/deploy_complete_update.sh | sudo bash
```

## 📞 Support et Monitoring

### Logs Importants
- **Service systemd** : `journalctl -u ntp-monitor`
- **Application** : `/opt/ntp-monitor/logs/app.log`
- **Apache** : `/var/log/apache2/error.log`

### Commandes Utiles
```bash
# Redémarrer le service
sudo systemctl restart ntp-monitor

# Voir la configuration
sudo systemctl cat ntp-monitor

# Statut détaillé
sudo systemctl status ntp-monitor -l

# Test de connectivité Apache -> Flask
curl -I http://localhost:5000/
```

## ✅ Résultat Attendu

Après correction réussie :
- ✅ Service `ntp-monitor` actif
- ✅ Port 5000 en écoute
- ✅ Application accessible sur http://79.137.36.66/
- ✅ Base de données fonctionnelle (MySQL ou SQLite)
- ✅ Authentification opérationnelle

## 🛡️ Sécurité

Le script configure automatiquement :
- Utilisateur système dédié `ntp-monitor`
- Base de données avec utilisateur limité `ntp_app`
- Permissions restreintes sur les fichiers
- Logs sécurisés

---

**En cas de problème persistant, contactez le support technique avec les logs complets.** 