#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Configuration pour EXE
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

# Variables d'environnement
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Répertoire de données utilisateur
data_dir = Path.home() / 'NTP_Monitor_Data'
data_dir.mkdir(exist_ok=True)

# Base de données
db_file = data_dir / 'ntp_monitor_prod.db'
os.environ['DATABASE_URL'] = f'sqlite:///{db_file}'

# Logs
logs_dir = data_dir / 'logs'
logs_dir.mkdir(exist_ok=True)

if __name__ == '__main__':
    try:
        print("🌐 Démarrage de NTP Monitor Enterprise...")
        print("📍 Adresse: http://127.0.0.1:5000")
        print("🔑 Connexion: admin / admin123")
        print("❌ Pour arrêter: Ctrl+C")
        print("-" * 50)
        
        # Importer et démarrer
        from app import app
        app.run(host='127.0.0.1', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de l'application")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        input("Appuyez sur Entrée pour fermer...")
