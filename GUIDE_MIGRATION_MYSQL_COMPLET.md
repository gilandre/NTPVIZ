# 🚀 Guide Migration Complète SQLite → MySQL

## 🎯 **OBJECTIF PRINCIPAL**
Résoudre définitivement les erreurs SQLite :
- ✅ 0 erreur `database is locked`
- ✅ 0 erreur `A transaction is already begun`
- ✅ Synchronisation NTP stable et continue
- ✅ Performance optimale avec pool de connexions

---

## 📋 **PRÉ-REQUIS**

### 1. MySQL Installé et Fonctionnel
```bash
# Vérifier que MySQL est installé
mysql --version

# Se connecter en tant que root
mysql -u root -p
```

### 2. Environnement Python Préparé
```bash
# Créer un nouvel environnement virtuel
python -m venv .venv_mysql

# Activer l'environnement (Windows)
.venv_mysql\Scripts\activate

# Installer les nouvelles dépendances
pip install -r requirements.txt
```

---

## 🔄 **ÉTAPES DE MIGRATION**

### **ÉTAPE 1 : MIGRATION AUTOMATIQUE**

Exécuter le script de migration complet :
```bash
python migrate_to_mysql.py
```

Le script effectue automatiquement :
1. 💾 Sauvegarde de la base SQLite existante
2. 🗃️ Création de la base MySQL `ntp_monitor`
3. 👤 Création de l'utilisateur `ntp_user`
4. 📋 Création de toutes les tables MySQL
5. 📦 Migration complète des données
6. ⚙️ Mise à jour de la configuration
7. ✅ Validation de la migration

### **ÉTAPE 2 : VALIDATION MANUELLE**

Vérifier la migration :
```bash
# Se connecter à MySQL
mysql -u ntp_user -p

# Utiliser la base ntp_monitor
USE ntp_monitor;

# Lister les tables
SHOW TABLES;

# Vérifier les données
SELECT COUNT(*) FROM ntp_logs;
SELECT COUNT(*) FROM ntp_servers;
SELECT COUNT(*) FROM users;
```

### **ÉTAPE 3 : TEST DE L'APPLICATION**

Redémarrer l'application :
```bash
python app.py
```

Vérifications attendues :
- ✅ Message "🚀 NTP Monitor Enterprise - VERSION MYSQL"
- ✅ "Database Manager MySQL initialisé avec succès"
- ✅ Absence d'erreurs SQLite dans les logs
- ✅ Synchronisation NTP fonctionnelle

---

## 🔧 **ARCHITECTURE TECHNIQUE**

### **Database Manager Centralisé**
```python
# Utilisation dans les services
from backend.database_manager import get_db_session_with_context

# Context manager thread-safe avec gestion automatique
with get_db_session_with_context() as session:
    # Opérations sur la base
    server = session.query(NTPServer).first()
    # Commit automatique si succès
    # Rollback automatique si erreur
```

### **Configuration MySQL Optimisée**
- **Pool de connexions** : 20 connexions principales + 30 supplémentaires
- **Isolation** : READ_COMMITTED pour la concurrence
- **Recyclage** : Connexions recyclées toutes les heures
- **Health Check** : Vérification automatique avant utilisation

### **Services Refactorisés**
1. **NTP Service** : Utilise le database manager pour toutes les opérations
2. **Alert Service** : Gestion centralisée des alertes avec MySQL
3. **Monitoring** : Pas de contexte Flask requis pour les threads

---

## 📊 **BÉNÉFICES ATTENDUS**

### **Avant (SQLite)**
```
❌ 1032 erreurs "database is locked"
❌ 296 erreurs "A transaction is already begun"
❌ Synchronisation NTP interrompue
❌ Performance dégradée
```

### **Après (MySQL)**
```
✅ 0 erreur de base de données
✅ Synchronisation NTP continue
✅ Performance optimale
✅ Monitoring stable 24/7
```

---

## 🐛 **RÉSOLUTION D'ERREURS**

### **Erreur : "Access denied for user 'ntp_user'"**
```bash
# Se connecter en root MySQL
mysql -u root -p

# Recréer l'utilisateur
DROP USER IF EXISTS 'ntp_user'@'localhost';
CREATE USER 'ntp_user'@'localhost' IDENTIFIED BY 'ntp_password';
GRANT ALL PRIVILEGES ON ntp_monitor.* TO 'ntp_user'@'localhost';
FLUSH PRIVILEGES;
```

### **Erreur : "Can't connect to MySQL server"**
```bash
# Vérifier le service MySQL
# Windows
net start mysql

# Linux
sudo systemctl start mysql
sudo systemctl enable mysql
```

### **Erreur : "Table doesn't exist"**
```bash
# Relancer la création des tables
python -c "
from backend.app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Tables créées')
"
```

---

## 🔄 **ROLLBACK (SI NÉCESSAIRE)**

Si problème avec MySQL, revenir temporairement à SQLite :

### 1. Restaurer la Configuration SQLite
```python
# Dans config/config.py
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR}/instance/ntp_monitor_dev.db'
# SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://ntp_user:ntp_password@localhost/ntp_monitor'
```

### 2. Restaurer la Sauvegarde SQLite
```bash
# Copier la sauvegarde
cp backups/ntp_monitor_sqlite_backup_YYYYMMDD_HHMMSS.db instance/ntp_monitor_dev.db

# Redémarrer l'application
python app.py
```

---

## 📈 **MONITORING MYSQL**

### **Supervision des Connexions**
```sql
-- Voir les connexions actives
SHOW PROCESSLIST;

-- Statistiques de connexions
SHOW STATUS LIKE 'Connections';
SHOW STATUS LIKE 'Threads_connected';
```

### **Performance des Requêtes**
```sql
-- Requêtes lentes
SHOW VARIABLES LIKE 'slow_query_log';
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;
```

### **Maintenance Automatique**
```sql
-- Optimiser les tables périodiquement
OPTIMIZE TABLE ntp_logs;
OPTIMIZE TABLE alerts;

-- Analyser les index
ANALYZE TABLE ntp_logs;
```

---

## ⚡ **OPTIMISATIONS AVANCÉES**

### **Index Recommandés**
```sql
-- Index pour améliorer les performances
CREATE INDEX idx_ntp_logs_timestamp ON ntp_logs(timestamp);
CREATE INDEX idx_ntp_logs_server_timestamp ON ntp_logs(server_id, timestamp);
CREATE INDEX idx_alerts_status_severity ON alerts(status, severity);
CREATE INDEX idx_alerts_server_type ON alerts(server_id, alert_type);
```

### **Configuration MySQL Optimisée**
```ini
# /etc/mysql/mysql.conf.d/mysqld.cnf ou my.cnf
[mysqld]
innodb_buffer_pool_size = 256M
max_connections = 200
query_cache_size = 64M
query_cache_type = 1
expire_logs_days = 7
```

---

## 📝 **VALIDATION FINALE**

### **Checklist de Migration Réussie**
- [ ] Base MySQL `ntp_monitor` créée
- [ ] Utilisateur `ntp_user` configuré
- [ ] Toutes les tables présentes
- [ ] Données migrées avec succès
- [ ] Application démarre sans erreur
- [ ] Logs ne contiennent plus d'erreurs SQLite
- [ ] Synchronisation NTP fonctionnelle
- [ ] Interface web accessible
- [ ] Alertes opérationnelles

### **Tests de Performance**
```bash
# Test de charge des connexions
python -c "
from backend.database_manager import db_manager
info = db_manager.get_connection_info()
print('Pool MySQL:', info)
"

# Vérifier les logs d'application
Get-Content logs/app.log -Tail 50 | Select-String -Pattern "error|locked|transaction"
```

---

## 🎉 **MIGRATION TERMINÉE**

Une fois la migration réussie :

1. **Supprimer l'ancienne base SQLite** (optionnel)
2. **Configurer la sauvegarde MySQL** automatique
3. **Mettre à jour la documentation** de déploiement
4. **Informer l'équipe** des changements

### **Nouvelle Commande de Démarrage**
```bash
# L'application utilise maintenant MySQL par défaut
python app.py
```

### **Monitoring Continu**
- Surveiller les logs MySQL : `/var/log/mysql/`
- Vérifier les performances : Interface web → Statistiques
- Alertes automatiques en cas de problème

---

## 📞 **SUPPORT**

En cas de problème :
1. Consulter les logs : `logs/app.log` et `mysql_migration.log`
2. Vérifier la configuration MySQL
3. Utiliser le rollback si nécessaire
4. Contacter l'équipe technique avec les logs d'erreur

**La migration MySQL garantit une stabilité 24/7 du monitoring NTP !** 🚀 