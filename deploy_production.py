#!/usr/bin/env python3
"""
Script de déploiement production - NTP Monitor Enterprise
Compatible Ubuntu 24.04
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_requirements():
    """Vérifier les prérequis"""
    logger.info("🔍 Vérification des prérequis...")
    
    # Python
    try:
        version = subprocess.check_output(['python3', '--version'], text=True).strip()
        logger.info(f"✅ Python: {version}")
    except:
        logger.error("❌ Python3 non trouvé")
        return False
    
    # MySQL
    try:
        version = subprocess.check_output(['mysql', '--version'], text=True).strip()
        logger.info(f"✅ MySQL: {version}")
    except:
        logger.warning("⚠️ MySQL non trouvé - Installez: sudo apt install mysql-server")
    
    return True

def setup_environment():
    """Configurer l'environnement"""
    logger.info("⚙️ Configuration de l'environnement...")
    
    app_dir = Path(__file__).parent
    venv_path = app_dir / '.venv'
    env_file = app_dir / '.env'
    env_example = app_dir / 'env.example'
    
    # Créer venv si nécessaire
    if not venv_path.exists():
        subprocess.run(['python3', '-m', 'venv', '.venv'], check=True)
        logger.info("✅ Environnement virtuel créé")
    
    # Configurer .env
    if not env_file.exists() and env_example.exists():
        import shutil
        shutil.copy(env_example, env_file)
        logger.info("✅ Fichier .env créé")
    
    return True

def install_dependencies():
    """Installer les dépendances"""
    logger.info("📦 Installation des dépendances...")
    
    pip_cmd = '.venv/bin/pip'
    subprocess.run([pip_cmd, 'install', '--upgrade', 'pip'], check=True)
    subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], check=True)
    logger.info("✅ Dépendances installées")
    
    return True

def setup_database():
    """Configurer la base de données"""
    logger.info("🗄️ Configuration de la base de données...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from backend.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        if db_manager.initialize():
            logger.info("✅ Base de données initialisée")
            
            # Créer les données par défaut
            from backend.utils.init_data import init_default_data
            if init_default_data():
                logger.info("✅ Données par défaut créées")
                return True
        
        logger.error("❌ Échec initialisation base de données")
        return False
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return False

def test_application():
    """Tester l'application"""
    logger.info("🧪 Test de l'application...")
    
    try:
        result = subprocess.run([
            '.venv/bin/python', '-c',
            'from backend.app import create_app; app = create_app(); print("✅ OK")'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Application testée avec succès")
            return True
        else:
            logger.error(f"❌ Test échoué: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test: {e}")
        return False

def main():
    """Déploiement principal"""
    logger.info("🚀 DÉPLOIEMENT PRODUCTION - NTP Monitor Enterprise")
    
    steps = [
        ("Vérification prérequis", check_requirements),
        ("Configuration environnement", setup_environment),
        ("Installation dépendances", install_dependencies),
        ("Configuration base de données", setup_database),
        ("Test application", test_application)
    ]
    
    for name, func in steps:
        logger.info(f"\n📋 {name}...")
        if not func():
            logger.error(f"❌ Échec: {name}")
            return False
        logger.info(f"✅ {name} terminé")
    
    logger.info("\n🎉 DÉPLOIEMENT RÉUSSI!")
    logger.info("📋 Prochaines étapes:")
    logger.info("   1. Démarrer: python app.py")
    logger.info("   2. Accéder: http://localhost:5001")
    logger.info("   3. Se connecter: admin/admin123")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 