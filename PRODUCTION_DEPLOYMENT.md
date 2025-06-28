# NTP Monitor Enterprise - Guide de Déploiement Production

## 🚀 Préparation pour la Production

Cette version de **NTP Monitor Enterprise** est maintenant **100% prête pour la production** avec des données live et des fonctionnalités complètes d'administration et de configuration.

### ✅ Modifications pour la Production

1. **Suppression des données de test**
   - Les fonctions de test ne créent plus de données factices
   - Tests email et webhook utilisent des vraies APIs
   - Aucune donnée de test créée en mode production

2. **Configuration sécurisée**
   - Variables d'environnement pour tous les paramètres sensibles
   - Séparation claire développement/production
   - Logging approprié pour la production

3. **Fonctionnalités live**
   - Tests d'email réels avec SMTP
   - Tests de webhook avec validation de signature
   - Données de monitoring en temps réel
   - Statistiques et métriques authentiques

## 📋 Prérequis

### Système
- **Python 3.8+**
- **Redis** (pour les sessions et cache)
- **Base de données** (SQLite, PostgreSQL, ou MySQL)

### Services optionnels
- **SMTP Server** (pour les alertes email)
- **Webhook endpoint** (pour les notifications)

## 🏗️ Installation Production

### 1. Clonage et préparation

```bash
# Cloner le repository
git clone <votre-repo-github>
cd ntp-monitor-enterprise

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copier le fichier de configuration exemple
cp production.env.example .env

# Éditer la configuration
nano .env
```

**Variables critiques à configurer :**
```env
# Sécurité
SECRET_KEY=votre-cle-secrete-unique-et-complexe
FLASK_ENV=production

# Base de données (choisir une option)
DATABASE_URL=postgresql://user:pass@localhost/ntp_monitor_prod
# ou
DATABASE_URL=sqlite:///ntp_monitor_prod.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (pour les alertes)
ALERTS_EMAIL_SMTP_HOST=smtp.gmail.com
ALERTS_EMAIL_SMTP_USER=votre-email@gmail.com
ALERTS_EMAIL_SMTP_PASSWORD=votre-mot-de-passe-app
```

### 3. Initialisation de la base de données

```bash
# Utiliser le script de production
python start_production.py
```

## 🔧 Configuration Avancée

### Base de Données PostgreSQL (Recommandé)

```bash
# Installer PostgreSQL
sudo apt install postgresql postgresql-contrib

# Créer la base de données
sudo -u postgres createdb ntp_monitor_prod
sudo -u postgres createuser ntp_user
sudo -u postgres psql -c "ALTER USER ntp_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ntp_monitor_prod TO ntp_user;"

# Configuration .env
DATABASE_URL=postgresql://ntp_user:secure_password@localhost/ntp_monitor_prod
```

### Redis

```bash
# Installer Redis
sudo apt install redis-server

# Démarrer Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### Serveur Web (Nginx + Gunicorn)

```bash
# Installer Gunicorn
pip install gunicorn

# Créer le fichier de service systemd
sudo nano /etc/systemd/system/ntp-monitor.service
```

**Contenu du service :**
```ini
[Unit]
Description=NTP Monitor Enterprise
After=network.target

[Service]
User=ntp-monitor
Group=www-data
WorkingDirectory=/opt/ntp-monitor-enterprise
Environment="PATH=/opt/ntp-monitor-enterprise/venv/bin"
ExecStart=/opt/ntp-monitor-enterprise/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

**Configuration Nginx :**
```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 🔐 Sécurité

### 1. Changement des mots de passe par défaut

**Après le premier démarrage :**
1. Connectez-vous avec `admin / admin123`
2. Allez dans **Administration → Utilisateurs**
3. Modifiez le mot de passe administrateur
4. Supprimez ou désactivez les comptes de test (si présents)

### 2. HTTPS (Recommandé)

```bash
# Installer Certbot pour Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Obtenir un certificat SSL
sudo certbot --nginx -d votre-domaine.com
```

### 3. Firewall

```bash
# Configurer UFW
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## 📊 Monitoring et Maintenance

### Logs

Les logs sont disponibles dans :
- `logs/production_YYYYMMDD.log` (application)
- `/var/log/nginx/` (Nginx)
- `journalctl -u ntp-monitor` (service systemd)

### Backup Automatique

```bash
# Créer un script de backup
cat > /opt/backup-ntp-monitor.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/ntp-monitor"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup base de données
if [[ $DATABASE_URL == postgresql* ]]; then
    pg_dump $DATABASE_URL > $BACKUP_DIR/db_backup_$DATE.sql
elif [[ $DATABASE_URL == sqlite* ]]; then
    cp ntp_monitor_prod.db $BACKUP_DIR/db_backup_$DATE.db
fi

# Backup configuration
cp .env $BACKUP_DIR/config_backup_$DATE.env

# Nettoyer les anciens backups (garder 7 jours)
find $BACKUP_DIR -name "*.sql" -o -name "*.db" -o -name "*.env" | head -n -21 | xargs rm -f
EOF

chmod +x /opt/backup-ntp-monitor.sh

# Ajouter au crontab
echo "0 2 * * * /opt/backup-ntp-monitor.sh" | sudo crontab -
```

## 🚦 Vérifications Post-Déploiement

### 1. Tests de base
- [ ] Application accessible via le navigateur
- [ ] Connexion administrateur fonctionnelle
- [ ] Dashboard affiche des données réelles
- [ ] Tests de connectivité NTP fonctionnels

### 2. Tests de fonctionnalités
- [ ] Ajout/modification de serveurs NTP
- [ ] Configuration des paramètres système
- [ ] Tests d'alertes email/webhook
- [ ] Export/import de données
- [ ] Logs d'audit enregistrés

### 3. Tests de performance
- [ ] Temps de réponse < 2 secondes
- [ ] Monitoring en temps réel fonctionnel
- [ ] Mise à jour automatique des statuts

## 📞 Support et Maintenance

### Commandes utiles

```bash
# Redémarrer l'application
sudo systemctl restart ntp-monitor

# Voir les logs en temps réel
tail -f logs/production_$(date +%Y%m%d).log

# Vérifier le statut
sudo systemctl status ntp-monitor

# Mise à jour
git pull origin main
pip install -r requirements.txt
sudo systemctl restart ntp-monitor
```

### Surveillance

Surveillez ces métriques :
- **CPU/Mémoire** : via `htop` ou monitoring système
- **Espace disque** : croissance des logs et base de données
- **Connectivité NTP** : alertes dans l'application
- **Erreurs applicatives** : logs de production

## 🔄 Mise à jour

```bash
# Sauvegarder
/opt/backup-ntp-monitor.sh

# Mettre à jour le code
git pull origin main

# Mettre à jour les dépendances
pip install -r requirements.txt

# Redémarrer
sudo systemctl restart ntp-monitor
```

---

## ✅ Résumé Production

**NTP Monitor Enterprise** est maintenant **100% production-ready** avec :

- ✅ **Données live uniquement** (plus de données de test)
- ✅ **Tests fonctionnels réels** (email SMTP, webhook HTTP)
- ✅ **Configuration sécurisée** (variables d'environnement)
- ✅ **Monitoring authentique** (métriques temps réel)
- ✅ **Administration complète** (users, servers, config, audit)
- ✅ **Backup et maintenance** (scripts automatisés)

L'application est prête pour un déploiement GitHub et une utilisation en environnement de production professionnel. 