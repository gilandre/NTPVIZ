#!/usr/bin/env python3
"""
CORRECTION FINALE - Problème authentification load_user
"""

import os
import subprocess
import logging

# Configuration
APP_FILE = "/opt/NTPVIZ/backend/app.py"
BACKUP_FILE = "/opt/NTPVIZ/backend/app.py.backup_auth"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd):
    """Exécuter une commande"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def fix_load_user_function():
    """Corriger la fonction load_user pour compatibilité"""
    logger.info("🔧 Correction de la fonction load_user")
    
    try:
        # Sauvegarder le fichier
        if os.path.exists(APP_FILE):
            success, _, _ = run_command(f"sudo cp {APP_FILE} {BACKUP_FILE}")
            if success:
                logger.info("✅ Sauvegarde créée")
        
        # Créer la correction directe avec sed
        sed_commands = [
            # Remplacer la ligne problématique qui cause l'erreur NoneType
            "sudo sed -i 's/self.login_count = user_data.login_count/self.login_count = getattr(user_data, \"login_count\", 0)/g' " + APP_FILE,
            "sudo sed -i 's/self.last_login = user_data.last_login/self.last_login = getattr(user_data, \"last_login\", None)/g' " + APP_FILE,
            "sudo sed -i 's/self.preferences = user_data.preferences/self.preferences = getattr(user_data, \"preferences\", {})/g' " + APP_FILE,
            
            # Ajouter une vérification de sécurité au début de SimpleUser.__init__
            "sudo sed -i '/def __init__(self, user_data):/a\\                        if not user_data:\\n                            raise ValueError(\"user_data is None\")' " + APP_FILE
        ]
        
        for cmd in sed_commands:
            success, stdout, stderr = run_command(cmd)
            if not success:
                logger.warning(f"Commande sed échouée: {stderr}")
        
        logger.info("✅ Corrections sed appliquées")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur correction load_user: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🚀 Démarrage correction authentification finale")
    
    if not fix_load_user_function():
        logger.error("❌ Échec correction load_user")
        return False
    
    logger.info("🎉 Correction authentification terminée !")
    return True

if __name__ == "__main__":
    main() 