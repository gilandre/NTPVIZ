#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'initialisation de la base de données - NTP Monitor Enterprise
Créer une base de données propre avec toutes les données de base nécessaires
"""

import os
import sys
import logging
from datetime import datetime

# Ajouter le répertoire racine au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def init_database():
    """Initialiser la base de données avec toutes les données de base"""
    
    print("=" * 60)
    print("🚀 INITIALISATION BASE DE DONNÉES - NTP MONITOR ENTERPRISE")
    print("=" * 60)
    
    try:
        # Configuration du logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger(__name__)
        
        # Créer l'application Flask
        print("📦 Création de l'application Flask...")
        from backend.app import create_app, db
        app = create_app()
        
        with app.app_context():
            # Importer tous les modèles
            print("📋 Import des modèles de données...")
            from backend.models.user import User
            from backend.models.ntp_server import NTPServer
            from backend.models.ntp_log import NTPLog
            from backend.models.alert import Alert
            from backend.models.system_config import SystemConfig
            
            # Vérifier si la BDD existe déjà avec des données
            try:
                user_count = User.query.count()
                server_count = NTPServer.query.count()
                
                if user_count > 0 or server_count > 0:
                    print(f"⚠️  Base de données existante détectée:")
                    print(f"   - Utilisateurs: {user_count}")
                    print(f"   - Serveurs NTP: {server_count}")
                    
                    response = input("\n❓ Voulez-vous réinitialiser complètement la BDD ? (y/N): ")
                    if response.lower() not in ['y', 'yes', 'oui']:
                        print("✋ Initialisation annulée")
                        return False
                    
                    print("🗑️  Suppression des données existantes...")
                    db.drop_all()
                    
            except Exception:
                # La BDD n'existe pas encore
                pass
            
            # Créer les tables
            print("🏗️  Création des tables de base de données...")
            db.create_all()
            
            # Initialiser les données par défaut
            print("📊 Initialisation des données par défaut...")
            from backend.utils.init_data import init_default_data
            
            if init_default_data():
                print("✅ Données par défaut initialisées avec succès")
                
                # Afficher un résumé
                users = User.query.all()
                servers = NTPServer.query.filter_by(is_active=True).all()
                configs = SystemConfig.query.all()
                
                print("\n" + "=" * 60)
                print("📈 RÉSUMÉ DE L'INITIALISATION")
                print("=" * 60)
                
                print(f"👤 Utilisateurs créés ({len(users)}):")
                for user in users:
                    print(f"   - {user.username} ({user.role}) - {user.email}")
                
                print(f"\n🌐 Serveurs NTP configurés ({len(servers)}):")
                for server in servers:
                    print(f"   - {server.name}: {server.address} ({server.server_type})")
                
                print(f"\n⚙️  Configurations système ({len(configs)}):")
                for config in configs:
                    print(f"   - {config.key_name}: {config.value}")
                
                print("\n" + "=" * 60)
                print("🎉 INITIALISATION TERMINÉE AVEC SUCCÈS")
                print("=" * 60)
                print("🔐 Comptes utilisateur par défaut:")
                print("   - Administrateur: admin / admin123")
                print("💡 Changez le mot de passe après la première connexion!")
                print("🌐 Accès: http://localhost:5000")
                print("=" * 60)
                
                return True
            else:
                print("❌ Erreur lors de l'initialisation des données")
                return False
                
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        logger.error(f"Erreur lors de l'initialisation: {e}")
        return False

def create_sample_data():
    """Créer des données d'exemple pour les tests/démo"""
    
    print("\n🧪 Création de données d'exemple...")
    
    try:
        from backend.app import create_app, db
        app = create_app()
        
        with app.app_context():
            from backend.utils.init_data import create_test_data
            
            if create_test_data():
                print("✅ Données d'exemple créées")
                return True
            else:
                print("❌ Erreur lors de la création des données d'exemple")
                return False
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def check_database():
    """Vérifier l'état de la base de données"""
    
    print("\n🔍 VÉRIFICATION DE LA BASE DE DONNÉES")
    print("-" * 40)
    
    try:
        from backend.app import create_app, db
        app = create_app()
        
        with app.app_context():
            from backend.models.user import User
            from backend.models.ntp_server import NTPServer
            from backend.models.ntp_log import NTPLog
            from backend.models.alert import Alert
            from backend.models.system_config import SystemConfig
            
            print(f"👤 Utilisateurs: {User.query.count()}")
            print(f"🌐 Serveurs NTP: {NTPServer.query.count()}")
            print(f"📊 Logs NTP: {NTPLog.query.count()}")
            print(f"🚨 Alertes: {Alert.query.count()}")
            print(f"⚙️  Configurations: {SystemConfig.query.count()}")
            
            # Vérifier les serveurs actifs
            active_servers = NTPServer.query.filter_by(is_active=True).all()
            print(f"\n🌐 Serveurs NTP actifs ({len(active_servers)}):")
            for server in active_servers:
                print(f"   - {server.name}: {server.address}")
                
    except Exception as e:
        print(f"❌ Impossible de vérifier la BDD: {e}")

if __name__ == '__main__':
    print("NTP Monitor Enterprise - Gestionnaire de Base de Données")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'init':
            init_database()
        elif command == 'check':
            check_database()
        elif command == 'sample':
            if init_database():
                create_sample_data()
        elif command == 'reset':
            print("⚠️  ATTENTION: Ceci va SUPPRIMER toutes les données!")
            response = input("Confirmez-vous la réinitialisation ? (tapez 'CONFIRMER'): ")
            if response == 'CONFIRMER':
                init_database()
            else:
                print("❌ Réinitialisation annulée")
        else:
            print(f"❌ Commande inconnue: {command}")
            print("\nCommandes disponibles:")
            print("  init   - Initialiser la BDD avec les données de base")
            print("  check  - Vérifier l'état de la BDD")
            print("  sample - Initialiser + créer des données d'exemple")
            print("  reset  - Réinitialiser complètement la BDD")
    else:
        print("\nCommandes disponibles:")
        print("  python init_database.py init   - Initialiser la BDD")
        print("  python init_database.py check  - Vérifier la BDD")
        print("  python init_database.py sample - Données d'exemple")
        print("  python init_database.py reset  - Réinitialiser la BDD")
        print("\nExécution par défaut: initialisation...")
        init_database() 