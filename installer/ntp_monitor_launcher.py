"""
NTP Monitor Enterprise - Lanceur principal pour Windows
Version EXE standalone avec dpendances intgres
"""

import os
import sys
import multiprocessing
from pathlib import Path

# Configuration pour l'environnement EXE
if getattr(sys, 'frozen', False):
    # Mode EXE - PyInstaller
    application_path = sys._MEIPASS
else:
    # Mode dveloppement
    application_path = os.path.dirname(os.path.abspath(__file__))

# Ajouter le chemin de l'application au Python path
sys.path.insert(0, application_path)

def setup_environment():
    """Configurer l'environnement pour l'application"""
    
    # Variables d'environnement
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'False'
    
    # Rpertoire de donnes
    data_dir = Path.home() / 'NTP_Monitor_Data'
    data_dir.mkdir(exist_ok=True)
    
    # Base de donnes
    db_file = data_dir / 'ntp_monitor_prod.db'
    os.environ['DATABASE_URL'] = f'sqlite:///{db_file}'
    
    # Logs
    logs_dir = data_dir / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    print(f" Rpertoire de donnes: {data_dir}")
    print(f" Base de donnes: {db_file}")

def start_application():
    """Dmarrer l'application NTP Monitor"""
    try:
        print(" Dmarrage de NTP Monitor Enterprise...")
        print(" Adresse: http://127.0.0.1:5000")
        print(" Connexion: admin / admin123")
        print(" Pour arrter: Ctrl+C dans cette fentre")
        print("-" * 50)
        
        # Importer et dmarrer l'application
        from app import create_app, socketio
        
        app = create_app('production')
        socketio.run(app, 
                    host='127.0.0.1', 
                    port=5000, 
                    debug=False,
                    use_reloader=False)
                    
    except KeyboardInterrupt:
        print("\n Arrt de NTP Monitor Enterprise")
    except Exception as e:
        print(f" Erreur: {e}")
        input("Appuyez sur Entre pour fermer...")

if __name__ == '__main__':
    multiprocessing.freeze_support()  # Ncessaire pour PyInstaller
    setup_environment()
    start_application()
