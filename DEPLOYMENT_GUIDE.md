# 🚀 Guide de Déploiement NTP Monitor Enterprise

## 📋 Vue d'ensemble

Ce guide détaille le déploiement complet de NTP Monitor Enterprise sur un serveur Ubuntu 24.04, incluant la mise à jour automatique depuis GitHub et la correction des problèmes de schéma de base de données.

## 🎯 Fonctionnalités du déploiement

- ✅ **Déploiement automatique** depuis GitHub
- ✅ **Correction automatique** du schéma de base de données
- ✅ **Harmonisation des modèles** et suppression des redondances
- ✅ **Service systemd** pour la gestion automatique
- ✅ **Firewall configuré** pour la sécurité
- ✅ **Sauvegarde automatique** lors des mises à jour
- ✅ **Rollback** en cas de problème

## 📦 Prérequis

### Système
- Ubuntu 24.04 LTS
- Accès sudo
- Connexion Internet

### Packages requis
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git curl wget mysql-server
```

## 🚀 Déploiement initial

### Option 1 : Déploiement automatique (Recommandé)

```bash
# 1. Télécharger le script de déploiement
wget https://raw.githubusercontent.com/gilandre/NTPVIZ/MacDev/deployment/scripts/deploy_ubuntu_complete.sh

# 2. Rendre le script exécutable
chmod +x deploy_ubuntu_complete.sh

# 3. Exécuter le déploiement
./deploy_ubuntu_complete.sh
```

### Option 2 : Déploiement manuel

```bash
# 1. Configuration MySQL
sudo mysql_secure_installation
sudo mysql -u root -p
```

**Dans MySQL :**
```sql
CREATE DATABASE IF NOT EXISTS ntp_monitor;
CREATE USER 'ntp_user'@'localhost' IDENTIFIED BY 'NTP_Monitor_2025!';
GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

```bash
# 2. Téléchargement du code source
git clone -b MacDev https://github.com/gilandre/NTPVIZ.git /opt/ntp-monitor
cd /opt/ntp-monitor

# 3. Configuration de l'environnement Python
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configuration de l'environnement
cp env.example .env
sed -i 's/FLASK_ENV=development/FLASK_ENV=production/' .env
sed -i 's/DEBUG=True/DEBUG=False/' .env
sed -i 's/HOST=127.0.0.1/HOST=0.0.0.0/' .env

# 5. Correction du schéma de base de données
python fix_database_schema.py

# 6. Harmonisation des modèles
python harmonize_models.py

# 7. Initialisation de la base de données
python initialiser_database.py

# 8. Test de l'application
python -c "from backend.app import create_app; app = create_app(); print('✅ Application OK')"

# 9. Configuration du service systemd
sudo tee /etc/systemd/system/ntp-monitor.service > /dev/null <<EOF
[Unit]
Description=NTP Monitor Enterprise
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/opt/ntp-monitor
Environment=PATH=/opt/ntp-monitor/.venv/bin
ExecStart=/opt/ntp-monitor/.venv/bin/python /opt/ntp-monitor/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 10. Activation et démarrage du service
sudo systemctl daemon-reload
sudo systemctl enable ntp-monitor
sudo systemctl start ntp-monitor

# 11. Configuration du firewall
sudo ufw allow ssh
sudo ufw allow 5001/tcp
sudo ufw --force enable
```

## 🔄 Mise à jour du déploiement

### Option 1 : Mise à jour automatique

```bash
# Télécharger le script de mise à jour
wget https://raw.githubusercontent.com/gilandre/NTPVIZ/MacDev/deployment/scripts/update_deployment.sh
chmod +x update_deployment.sh

# Exécuter la mise à jour
./update_deployment.sh
```

### Option 2 : Mise à jour manuelle

```bash
cd /opt/ntp-monitor

# Sauvegarder la configuration
cp .env .env.backup

# Mettre à jour depuis GitHub
git fetch origin
git reset --hard origin/MacDev
git checkout MacDev

# Restaurer la configuration
cp .env.backup .env

# Mettre à jour l'environnement Python
source .venv/bin/activate
pip install -r requirements.txt --upgrade

# Corriger le schéma et harmoniser les modèles
python fix_database_schema.py
python harmonize_models.py

# Redémarrer le service
sudo systemctl restart ntp-monitor
```

## 🛠️ Commandes de gestion

### Service systemd
```bash
# Voir le statut
sudo systemctl status ntp-monitor

# Redémarrer
sudo systemctl restart ntp-monitor

# Arrêter
sudo systemctl stop ntp-monitor

# Voir les logs
sudo journalctl -u ntp-monitor -f
```

### Scripts de déploiement
```bash
# Déploiement complet
./deploy_ubuntu_complete.sh

# Mise à jour
./update_deployment.sh

# Commandes spécifiques
./deploy_ubuntu_complete.sh logs      # Voir les logs
./deploy_ubuntu_complete.sh restart   # Redémarrer
./deploy_ubuntu_complete.sh status    # Statut
./deploy_ubuntu_complete.sh test      # Test de l'application

./update_deployment.sh rollback       # Rollback vers la version précédente
```

## 🔧 Dépannage

### Problèmes courants

#### 1. Erreur de schéma de base de données
```bash
cd /opt/ntp-monitor
source .venv/bin/activate
python fix_database_schema.py
```

#### 2. Erreur de modèles incohérents
```bash
cd /opt/ntp-monitor
source .venv/bin/activate
python harmonize_models.py
```

#### 3. Service ne démarre pas
```bash
# Vérifier les logs
sudo journalctl -u ntp-monitor -n 50

# Vérifier la configuration
sudo systemctl status ntp-monitor

# Redémarrer MySQL si nécessaire
sudo systemctl restart mysql
```

#### 4. Port déjà utilisé
```bash
# Identifier le processus
sudo lsof -i :5001

# Tuer le processus
sudo pkill -f "python.*app.py"
```

### Rollback en cas de problème
```bash
# Utiliser le script de mise à jour
./update_deployment.sh rollback

# Ou manuellement
sudo systemctl stop ntp-monitor
sudo cp -r /opt/ntp-monitor-backup-YYYYMMDD-HHMMSS /opt/ntp-monitor
sudo systemctl start ntp-monitor
```

## 📊 Vérification du déploiement

### Test de l'application
```bash
# Test de création de l'application
cd /opt/ntp-monitor
source .venv/bin/activate
python -c "from backend.app import create_app; app = create_app(); print('✅ Application OK')"

# Test de connexion à la base de données
python -c "
from backend.database_manager import get_db_session_with_context
from backend.models.user import User
with get_db_session_with_context() as session:
    users = session.query(User).count()
    print(f'✅ {users} utilisateurs trouvés')
"
```

### Vérification des services
```bash
# Vérifier MySQL
sudo systemctl status mysql

# Vérifier l'application
sudo systemctl status ntp-monitor

# Vérifier le firewall
sudo ufw status

# Vérifier l'accessibilité
curl -s http://localhost:5001/ | head -5
```

## 🔐 Sécurité

### Configuration recommandée
1. **Changer les mots de passe par défaut**
   - Utilisateur MySQL : `ntp_user`
   - Application : `admin/admin123`

2. **Configuration du firewall**
   - SSH : Port 22
   - Application : Port 5001
   - MySQL : Port 3306 (local uniquement)

3. **Sécurisation MySQL**
   ```bash
   sudo mysql_secure_installation
   ```

### Monitoring
```bash
# Vérifier l'utilisation des ressources
htop

# Vérifier l'espace disque
df -h

# Vérifier la mémoire
free -h

# Vérifier les processus
ps aux | grep python
```

## 📈 Maintenance

### Sauvegarde automatique
Les scripts de mise à jour créent automatiquement des sauvegardes dans `/opt/ntp-monitor-backup-*`

### Nettoyage des sauvegardes
```bash
# Supprimer les sauvegardes anciennes (plus de 7 jours)
find /opt/ntp-monitor-backup-* -type d -mtime +7 -exec rm -rf {} \;
```

### Mise à jour des dépendances
```bash
cd /opt/ntp-monitor
source .venv/bin/activate
pip install -r requirements.txt --upgrade
```

## 🎯 Accès à l'application

### Informations de connexion
- **URL** : `http://votre-serveur-ip:5001`
- **Utilisateur** : `admin`
- **Mot de passe** : `admin123`

### Utilisateurs par défaut
- `admin` : Administrateur complet
- `operator` : Opérateur avec permissions limitées
- `viewer` : Lecteur uniquement

## 📞 Support

En cas de problème :
1. Vérifier les logs : `sudo journalctl -u ntp-monitor -f`
2. Tester l'application : `./deploy_ubuntu_complete.sh test`
3. Effectuer un rollback : `./update_deployment.sh rollback`

## 🎉 Succès !

L'application NTP Monitor Enterprise est maintenant déployée et fonctionnelle avec :
- ✅ **Interface web** complète
- ✅ **Monitoring NTP** en temps réel
- ✅ **Système d'alertes** configurable
- ✅ **Gestion des utilisateurs** complète
- ✅ **Service systemd** pour la gestion automatique
- ✅ **Sauvegarde et rollback** automatiques 