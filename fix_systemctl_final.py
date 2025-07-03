#!/usr/bin/env python3
"""
CORRECTION FINALE - Problème systemctl
Corrige le service client_monitor_service.py pour utiliser le chemin complet.
"""

import os
import subprocess
import logging

# Configuration
SYSTEMCTL_PATH = "/usr/local/bin/systemctl"
SERVICE_FILE = "/opt/NTPVIZ/backend/services/client_monitor_service.py"
BACKUP_FILE = "/opt/NTPVIZ/backend/services/client_monitor_service.py.backup"

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd):
    """Exécuter une commande"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def fix_systemctl_client_monitor():
    """Corriger le service client_monitor pour systemctl"""
    logger.info("🔧 Correction du problème systemctl dans client_monitor_service")
    
    try:
        # 1. Vérifier que systemctl existe
        if not os.path.exists(SYSTEMCTL_PATH):
            logger.error(f"❌ systemctl non trouvé à {SYSTEMCTL_PATH}")
            return False
        
        logger.info(f"✅ systemctl trouvé: {SYSTEMCTL_PATH}")
        
        # 2. Sauvegarder le fichier original
        if os.path.exists(SERVICE_FILE):
            logger.info("📁 Sauvegarde du fichier original...")
            success, _, _ = run_command(f"sudo cp {SERVICE_FILE} {BACKUP_FILE}")
            if success:
                logger.info("✅ Sauvegarde créée")
            else:
                logger.warning("⚠️ Échec sauvegarde, continuation...")
        
        # 3. Lire le fichier actuel
        with open(SERVICE_FILE, 'r') as f:
            content = f.read()
        
        # 4. Remplacer les appels systemctl
        logger.info("🔄 Correction des appels systemctl...")
        
        # Remplacement 1: systemctl is-active ntpsec
        old_pattern1 = "result = subprocess.run(['systemctl', 'is-active', 'ntpsec'],"
        new_pattern1 = f"result = subprocess.run(['{SYSTEMCTL_PATH}', 'is-active', 'ntpsec'],"
        
        # Remplacement 2: systemctl is-active ntp  
        old_pattern2 = "result = subprocess.run(['systemctl', 'is-active', 'ntp'],"
        new_pattern2 = f"result = subprocess.run(['{SYSTEMCTL_PATH}', 'is-active', 'ntp'],"
        
        # Appliquer les remplacements
        content = content.replace(old_pattern1, new_pattern1)
        content = content.replace(old_pattern2, new_pattern2)
        
        # 5. Écrire le fichier corrigé
        with open(SERVICE_FILE, 'w') as f:
            f.write(content)
        
        logger.info("✅ Fichier client_monitor_service.py corrigé")
        
        # 6. Vérifier les corrections
        logger.info("🔍 Vérification des corrections...")
        with open(SERVICE_FILE, 'r') as f:
            corrected_content = f.read()
        
        if SYSTEMCTL_PATH in corrected_content:
            logger.info("✅ Corrections appliquées avec succès")
            return True
        else:
            logger.error("❌ Échec application des corrections")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur correction systemctl: {e}")
        return False

def verify_systemctl_fix():
    """Vérifier que la correction systemctl fonctionne"""
    logger.info("🧪 Test de la correction systemctl...")
    
    try:
        # Test systemctl direct
        success, stdout, stderr = run_command(f"{SYSTEMCTL_PATH} --version")
        if success:
            logger.info(f"✅ systemctl fonctionne: {stdout.split()[1]}")
        else:
            logger.error(f"❌ Erreur systemctl: {stderr}")
            return False
        
        # Test avec Python (simulation)
        test_cmd = f"python3 -c \"import subprocess; result = subprocess.run(['{SYSTEMCTL_PATH}', '--version'], capture_output=True); print('OK' if result.returncode == 0 else 'FAIL')\""
        success, stdout, stderr = run_command(test_cmd)
        
        if success and 'OK' in stdout:
            logger.info("✅ Test Python/systemctl réussi")
            return True
        else:
            logger.error(f"❌ Test Python/systemctl échoué: {stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test systemctl: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🚀 Démarrage correction systemctl finale")
    
    # 1. Corriger client_monitor_service
    if not fix_systemctl_client_monitor():
        logger.error("❌ Échec correction client_monitor_service")
        return False
    
    # 2. Vérifier la correction
    if not verify_systemctl_fix():
        logger.error("❌ Échec vérification systemctl")
        return False
    
    logger.info("🎉 Correction systemctl terminée avec succès !")
    logger.info("📝 Actions à effectuer:")
    logger.info("   1. sudo systemctl restart ntp-monitor")
    logger.info("   2. Vérifier les logs pour confirmer l'absence d'erreurs systemctl")
    
    return True

if __name__ == "__main__":
    main() 