#!/usr/bin/env python3
"""
Script de démarrage NTP Monitor Enterprise
Nettoie le cache Python et démarre l'application
"""
import os
import sys
import subprocess
import shutil

def clean_cache():
    """Nettoyer le cache Python"""
    print("🧹 Nettoyage du cache Python...")
    
    # Supprimer les fichiers .pyc
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                try:
                    os.remove(os.path.join(root, file))
                    print(f"  🗑️  Supprimé: {os.path.join(root, file)}")
                except:
                    pass
    
    # Supprimer les dossiers __pycache__
    for root, dirs, files in os.walk('.'):
        for dir in dirs:
            if dir == '__pycache__':
                try:
                    shutil.rmtree(os.path.join(root, dir))
                    print(f"  🗑️  Supprimé: {os.path.join(root, dir)}")
                except:
                    pass
    
    print("✅ Cache nettoyé")

def start_application():
    """Démarrer l'application"""
    print("🚀 Démarrage de NTP Monitor Enterprise...")
    
    try:
        # Importer et démarrer l'application
        from backend.app import create_app, socketio
        
        app = create_app()
        
        print("✅ Application créée avec succès")
        print("🌐 Démarrage du serveur sur http://localhost:5001")
        print("📊 Interface d'administration: http://localhost:5001 (admin/admin123)")
        print("⏹️  Pour arrêter: Ctrl+C")
        
        # Démarrer le serveur
        socketio.run(app, 
                    host='0.0.0.0', 
                    port=5001, 
                    debug=False,
                    allow_unsafe_werkzeug=True)
                    
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        sys.exit(1)

def main():
    """Fonction principale"""
    print("🚀 NTP Monitor Enterprise - Script de démarrage")
    print("=" * 50)
    
    # Nettoyer le cache
    clean_cache()
    
    # Démarrer l'application
    start_application()

if __name__ == "__main__":
    main() 