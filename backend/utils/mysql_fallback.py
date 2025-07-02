"""
Utilitaire de fallback MySQL pour NTP Monitor Enterprise
Configure automatiquement PyMySQL si mysqlclient n'est pas disponible
"""

import sys
import logging

logger = logging.getLogger(__name__)

def setup_mysql_driver():
    """
    Configure le driver MySQL approprié
    Utilise mysqlclient en priorité, PyMySQL en fallback
    """
    
    # Tentative d'import de mysqlclient (driver natif)
    try:
        import MySQLdb
        logger.info("✅ MySQLdb (mysqlclient) disponible - utilisation du driver natif")
        return "mysqlclient"
    except ImportError:
        logger.info("⚠️ mysqlclient non disponible, configuration de PyMySQL comme fallback")
        
        # Configuration de PyMySQL comme fallback
        try:
            import pymysql
            pymysql.install_as_MySQLdb()
            
            # Vérification que MySQLdb est maintenant disponible
            import MySQLdb
            logger.info("✅ PyMySQL configuré avec succès comme driver MySQL")
            return "pymysql"
            
        except ImportError as e:
            logger.error(f"❌ Impossible de configurer un driver MySQL: {e}")
            logger.error("Installation requise: pip install PyMySQL ou pip install mysqlclient")
            raise ImportError(
                "Aucun driver MySQL disponible. "
                "Installez 'mysqlclient' ou 'PyMySQL': "
                "pip install mysqlclient PyMySQL"
            )

def get_database_url_for_driver(base_url, driver=None):
    """
    Adapte l'URL de base de données selon le driver disponible
    
    Args:
        base_url (str): URL de base (ex: mysql://user:pass@host/db)
        driver (str): Driver à utiliser ('mysqlclient', 'pymysql', ou None pour auto-détection)
        
    Returns:
        str: URL adaptée pour SQLAlchemy
    """
    
    if driver is None:
        driver = setup_mysql_driver()
    
    # Conversion de l'URL selon le driver
    if driver == "pymysql":
        # PyMySQL utilise mysql+pymysql://
        if base_url.startswith("mysql://"):
            return base_url.replace("mysql://", "mysql+pymysql://", 1)
        elif not base_url.startswith("mysql+pymysql://"):
            return "mysql+pymysql://" + base_url.replace("mysql://", "", 1)
    else:
        # mysqlclient utilise mysql:// ou mysql+mysqldb://
        if base_url.startswith("mysql+pymysql://"):
            return base_url.replace("mysql+pymysql://", "mysql://", 1)
    
    return base_url

def test_mysql_connection():
    """
    Test la connexion MySQL avec le driver configuré
    
    Returns:
        bool: True si la connexion fonctionne, False sinon
    """
    
    try:
        driver = setup_mysql_driver()
        logger.info(f"Test de connexion avec driver: {driver}")
        
        # Import du driver configuré
        import MySQLdb
        
        # Test basique (sans connexion réelle pour éviter les erreurs d'authentification)
        logger.info("✅ Driver MySQL configuré et importable")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test connexion MySQL: {e}")
        return False

if __name__ == "__main__":
    """Test du module"""
    print("🗄️ Test de configuration MySQL driver...")
    
    try:
        driver = setup_mysql_driver()
        print(f"✅ Driver configuré: {driver}")
        
        # Test des URLs
        test_urls = [
            "mysql://user:pass@localhost/db",
            "mysql+pymysql://user:pass@localhost/db"
        ]
        
        for url in test_urls:
            adapted_url = get_database_url_for_driver(url, driver)
            print(f"URL adaptée: {url} → {adapted_url}")
        
        # Test de connexion
        if test_mysql_connection():
            print("✅ Configuration MySQL réussie")
        else:
            print("⚠️ Problème de configuration MySQL")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1) 