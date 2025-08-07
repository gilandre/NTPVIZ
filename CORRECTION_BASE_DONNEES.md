# 🔧 Correction des Erreurs de Base de Données

## Problème identifié
L'application NTPVIZ fonctionne mais génère des erreurs de base de données liées à des colonnes manquantes.

## Solution

### 1. Connexion au serveur
```bash
ssh gaegnakou@79.137.36.66
cd /opt/ntp-monitor
source .venv/bin/activate
```

### 2. Script de correction automatique
Créez le fichier `fix_database.py` :

```python
#!/usr/bin/env python3
import pymysql

def fix_database():
    try:
        print("🔌 Connexion à la base de données...")
        connection = pymysql.connect(
            host='localhost',
            user='ntp_user',
            password='NtpMonitor2024!',
            database='ntp_monitor',
            charset='utf8mb4'
        )
        cursor = connection.cursor()
        
        # Correction system_config
        print("🔧 Correction system_config...")
        try:
            cursor.execute("ALTER TABLE system_config ADD COLUMN value_type VARCHAR(20) DEFAULT 'string' AFTER value")
            print("✅ value_type ajouté")
        except:
            print("✅ value_type existe déjà")
            
        try:
            cursor.execute("ALTER TABLE system_config ADD COLUMN category VARCHAR(50) DEFAULT 'general' AFTER value_type")
            print("✅ category ajouté")
        except:
            print("✅ category existe déjà")
            
        try:
            cursor.execute("ALTER TABLE system_config ADD COLUMN is_public BOOLEAN DEFAULT TRUE AFTER category")
            print("✅ is_public ajouté")
        except:
            print("✅ is_public existe déjà")
            
        try:
            cursor.execute("ALTER TABLE system_config ADD COLUMN updated_by INT NULL AFTER updated_at")
            print("✅ updated_by ajouté")
        except:
            print("✅ updated_by existe déjà")
        
        # Correction ntp_logs
        print("🔧 Correction ntp_logs...")
        try:
            cursor.execute("ALTER TABLE ntp_logs ADD COLUMN server_id INT NOT NULL")
            print("✅ server_id ajouté")
        except:
            print("✅ server_id existe déjà")
            
        try:
            cursor.execute("ALTER TABLE ntp_logs ADD COLUMN timestamp DATETIME NOT NULL")
            print("✅ timestamp ajouté")
        except:
            print("✅ timestamp existe déjà")
            
        try:
            cursor.execute("ALTER TABLE ntp_logs ADD COLUMN status VARCHAR(20) DEFAULT 'unknown'")
            print("✅ status ajouté")
        except:
            print("✅ status existe déjà")
            
        try:
            cursor.execute("ALTER TABLE ntp_logs ADD COLUMN offset FLOAT NULL")
            print("✅ offset ajouté")
        except:
            print("✅ offset existe déjà")
            
        try:
            cursor.execute("ALTER TABLE ntp_logs ADD COLUMN delay FLOAT NULL")
            print("✅ delay ajouté")
        except:
            print("✅ delay existe déjà")
            
        try:
            cursor.execute("ALTER TABLE ntp_logs ADD COLUMN latency FLOAT NULL")
            print("✅ latency ajouté")
        except:
            print("✅ latency existe déjà")
            
        try:
            cursor.execute("ALTER TABLE ntp_logs ADD COLUMN stratum INT NULL")
            print("✅ stratum ajouté")
        except:
            print("✅ stratum existe déjà")
            
        try:
            cursor.execute("ALTER TABLE ntp_logs ADD COLUMN error_message TEXT NULL")
            print("✅ error_message ajouté")
        except:
            print("✅ error_message existe déjà")
            
        try:
            cursor.execute("ALTER TABLE ntp_logs ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            print("✅ created_at ajouté")
        except:
            print("✅ created_at existe déjà")
        
        connection.commit()
        print("🎉 Toutes les corrections terminées!")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    fix_database()
```

### 3. Exécution du script
```bash
python fix_database.py
```

### 4. Redémarrage du service
```bash
sudo systemctl restart ntp-monitor
sudo systemctl status ntp-monitor
```

### 5. Vérification
```bash
# Vérifier les logs
sudo journalctl -u ntp-monitor --no-pager | tail -20

# Tester l'application
curl http://localhost:5001
```

## Commandes utiles

### Vérifier le statut du service
```bash
sudo systemctl status ntp-monitor
```

### Voir les logs en temps réel
```bash
sudo journalctl -u ntp-monitor -f
```

### Redémarrer le service
```bash
sudo systemctl restart ntp-monitor
```

### Tester l'application
```bash
curl http://localhost:5001
curl http://79.137.36.66:5001
```

## Accès à l'application
- **URL locale** : http://localhost:5001
- **URL externe** : http://79.137.36.66:5001
- **Identifiants par défaut** :
  - Admin : admin / admin123
  - Operator : operator / operator123
  - Viewer : viewer / viewer123 