#!/usr/bin/python3
"""
WSGI script pour Apache mod_wsgi - NTP Monitor Enterprise
"""
import sys
import os
import logging

# Configuration des chemins
project_home = '/var/www/ntp-monitor-enterprise'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Configuration du logging pour production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_home, 'logs/wsgi.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

try:
    # Variables d'environnement
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_APP'] = 'app.py'
    
    # Créer le dossier logs s'il n'existe pas
    logs_dir = os.path.join(project_home, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Importer l'application
    from app import application
    
    logger.info("Application NTP Monitor Enterprise chargée avec succès")
    
except Exception as e:
    logger.error(f"Erreur lors du chargement de l'application: {e}")
    raise

# Point d'entrée WSGI
if __name__ == "__main__":
    application.run() 