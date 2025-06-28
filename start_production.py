#!/usr/bin/env python3
"""
NTP Monitor Enterprise - Script de démarrage production
"""

import os
import sys
import logging
from datetime import datetime

def setup_production_environment():
    """Configurer l'environnement de production"""
    
    # Forcer l'environnement de production
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'false'
    
    # Configuration par défaut si non définie
    default_config = {
        'SECRET_KEY': os.urandom(32).hex(),
        'HOST': '0.0.0.0',
        'PORT': '5000',
        'LOG_LEVEL': 'INFO',
        'LOG_TO_STDOUT': 'true'
    }
    
    for key, value in default_config.items():
        if not os.environ.get(key):
            os.environ[key] = value
    
    # Vérifications de sécurité
    security_checks = {
        'SECRET_KEY': 'Clé secrète non définie',
        'DATABASE_URL': 'URL de base de données non définie'
    }
    
    warnings = []
    errors = []
    
    for key, message in security_checks.items():
        if not os.environ.get(key):
            if key == 'SECRET_KEY' and os.environ.get('SECRET_KEY') == default_config['SECRET_KEY']:
                warnings.append(f"ATTENTION: {message} - utilisation d'une clé générée automatiquement")
            else:
                errors.append(f"ERREUR: {message}")
    
    # Vérifier les permissions de fichiers
    critical_files = ['config/config.py', 'backend/app/__init__.py']
    for file_path in critical_files:
        if not os.path.exists(file_path):
            errors.append(f"ERREUR: Fichier critique manquant: {file_path}")
    
    return warnings, errors

def check_dependencies():
    """Vérifier les dépendances critiques"""
    critical_imports = [
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'flask_socketio',
        'redis',
        'ntplib',
        'requests'
    ]
    
    missing_deps = []
    for dep in critical_imports:
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(dep)
    
    return missing_deps

def main():
    """Point d'entrée principal"""
    
    print("=" * 60)
    print("NTP MONITOR ENTERPRISE - DÉMARRAGE PRODUCTION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Vérifier les dépendances
    print("1. Vérification des dépendances...")
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"❌ ERREUR: Dépendances manquantes: {', '.join(missing_deps)}")
        print("   Exécutez: pip install -r requirements.txt")
        sys.exit(1)
    print("✅ Toutes les dépendances sont installées")
    
    # Configuration de l'environnement
    print("\n2. Configuration de l'environnement de production...")
    warnings, errors = setup_production_environment()
    
    if errors:
        print("❌ ERREURS CRITIQUES DÉTECTÉES:")
        for error in errors:
            print(f"   {error}")
        sys.exit(1)
    
    if warnings:
        print("⚠️  AVERTISSEMENTS:")
        for warning in warnings:
            print(f"   {warning}")
        print()
    
    print("✅ Environnement de production configuré")
    
    # Configuration du logging
    print("\n3. Configuration du logging...")
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Créer le répertoire logs s'il n'existe pas
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/production_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    print(f"✅ Logging configuré (niveau: {log_level})")
    
    # Affichage de la configuration
    print("\n4. Configuration actuelle:")
    config_items = [
        ('Environnement', os.environ.get('FLASK_ENV', 'production')),
        ('Host', os.environ.get('HOST', '0.0.0.0')),
        ('Port', os.environ.get('PORT', '5000')),
        ('Base de données', os.environ.get('DATABASE_URL', 'sqlite:///ntp_monitor_prod.db')),
        ('Redis', os.environ.get('REDIS_URL', 'redis://localhost:6379/0')),
        ('Log level', log_level)
    ]
    
    for key, value in config_items:
        # Masquer les mots de passe dans l'affichage
        if 'password' in value.lower() or 'secret' in key.lower():
            display_value = '***MASQUÉ***'
        else:
            display_value = value[:50] + ('...' if len(value) > 50 else '')
        print(f"   {key}: {display_value}")
    
    print("\n5. Démarrage de l'application...")
    print("=" * 60)
    
    try:
        # Import de l'application
        from backend.app import create_app, socketio
        
        # Créer l'application
        app = create_app()
        
        # Log de démarrage
        logger.info("=== DÉMARRAGE NTP MONITOR ENTERPRISE PRODUCTION ===")
        logger.info(f"Host: {os.environ.get('HOST', '0.0.0.0')}")
        logger.info(f"Port: {os.environ.get('PORT', '5000')}")
        logger.info("Application prête pour la production")
        
        # Message de sécurité
        print("\n🔒 RAPPELS DE SÉCURITÉ:")
        print("   • Changez le mot de passe admin par défaut")
        print("   • Configurez un SECRET_KEY unique")
        print("   • Utilisez HTTPS en production")
        print("   • Sauvegardez régulièrement la base de données")
        print("   • Surveillez les logs de sécurité")
        print()
        
        # Démarrer avec SocketIO
        socketio.run(
            app,
            host=os.environ.get('HOST', '0.0.0.0'),
            port=int(os.environ.get('PORT', 5000)),
            debug=False,
            use_reloader=False,
            log_output=False
        )
        
    except KeyboardInterrupt:
        logger.info("Arrêt de l'application par l'utilisateur")
        print("\n👋 Application arrêtée proprement")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erreur critique lors du démarrage: {e}")
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        print("Consultez les logs pour plus de détails")
        sys.exit(1)

if __name__ == '__main__':
    main() 