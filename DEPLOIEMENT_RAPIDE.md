# 🚀 Guide de Déploiement Rapide

## ⚡ Déploiement en 5 minutes

### **1. Préparation du serveur Ubuntu 24.04**

```bash
# Connexion au serveur
ssh root@votre-serveur-ip

# Mise à jour du système
apt update && apt upgrade -y
```

### **2. Téléchargement et exécution du script de déploiement**

```bash
# Téléchargement du script
wget https://raw.githubusercontent.com/votre-username/NTPVIZ/MacDev/deploy_ubuntu_complete.sh

# Rendre exécutable et lancer
chmod +x deploy_ubuntu_complete.sh
./deploy_ubuntu_complete.sh
```

### **3. Vérification du déploiement**

```bash
# Statut du service
systemctl status ntp-monitor

# Test de l'application
curl -I http://localhost

# Accès au dashboard
# Ouvrir dans le navigateur : http://votre-serveur-ip
```

## 🔄 Mise à jour depuis GitHub

### **Mise à jour automatique**

```bash
# Téléchargement du script de mise à jour
wget https://raw.githubusercontent.com/votre-username/NTPVIZ/MacDev/update_from_github.sh

# Exécution
chmod +x update_from_github.sh
./update_from_github.sh
```

## 🚨 Rollback en cas de problème

```bash
# Téléchargement du script de rollback
wget https://raw.githubusercontent.com/votre-username/NTPVIZ/MacDev/rollback.sh

# Exécution
chmod +x rollback.sh
./rollback.sh
```

## 📊 Commandes utiles

### **Monitoring**
```bash
# Statut du service
systemctl status ntp-monitor

# Logs en temps réel
journalctl -u ntp-monitor -f

# Redémarrage
systemctl restart ntp-monitor
```

### **Base de données**
```bash
# Connexion MySQL
mysql -u ntp_user -p ntp_monitor

# Sauvegarde
mysqldump -u ntp_user -p ntp_monitor > backup.sql
```

### **Logs et debugging**
```bash
# Logs de l'application
tail -f /opt/ntp-monitor/logs/app.log

# Logs d'erreur
tail -f /opt/ntp-monitor/logs/error.log

# Test de l'application
cd /opt/ntp-monitor
python quick_verification.py
```

## 🌐 Accès à l'application

- **Dashboard principal** : `http://votre-serveur-ip`
- **Port par défaut** : 80 (HTTP) / 443 (HTTPS)
- **Port de développement** : 5001

## 🔧 Configuration avancée

### **SSL avec Let's Encrypt**
```bash
# Installation Certbot
apt install -y certbot python3-certbot-nginx

# Obtention du certificat
certbot --nginx -d votre-domaine.com
```

### **Monitoring avancé**
```bash
# Installation des outils
apt install -y htop iotop nethogs

# Surveillance en temps réel
htop
```

## 📋 Checklist de déploiement

### ✅ **Pré-déploiement**
- [ ] Serveur Ubuntu 24.04 configuré
- [ ] Accès root disponible
- [ ] Connexion Internet active
- [ ] Repository GitHub accessible

### ✅ **Post-déploiement**
- [ ] Service ntp-monitor démarré
- [ ] Application accessible sur le port 80
- [ ] Base de données connectée
- [ ] Tests de vérification réussis
- [ ] Firewall configuré
- [ ] Nginx fonctionnel

### ✅ **Vérifications finales**
- [ ] Dashboard accessible
- [ ] Connexion utilisateur possible
- [ ] Logs sans erreur critique
- [ ] Performance acceptable

## 🎯 URLs importantes

- **Application** : `http://votre-serveur-ip`
- **Dashboard** : `http://votre-serveur-ip/dashboard`
- **Admin** : `http://votre-serveur-ip/admin`
- **API** : `http://votre-serveur-ip/api`

## 🚨 Dépannage rapide

### **Service ne démarre pas**
```bash
# Vérification des logs
journalctl -u ntp-monitor -n 50

# Test manuel
cd /opt/ntp-monitor
source .venv/bin/activate
python app.py
```

### **Erreur de base de données**
```bash
# Test de connexion
mysql -u ntp_user -p -e "SELECT 1;"

# Correction du schéma
python fix_database_schema.py
```

### **Erreur de permissions**
```bash
# Correction des permissions
chown -R root:root /opt/ntp-monitor
chmod -R 755 /opt/ntp-monitor
```

## 📞 Support

En cas de problème :
1. Vérifiez les logs : `journalctl -u ntp-monitor -f`
2. Testez l'application : `python quick_verification.py`
3. Consultez la documentation complète : `PROCEDURE_DEPLOIEMENT_GITHUB.md`

---

**🎉 L'application NTP Monitor Enterprise est prête pour la production !** 