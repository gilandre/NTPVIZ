#!/usr/bin/env python3
"""
Script de nettoyage du projet NTPVIZ
Supprime les fichiers de tests et de documentation inutiles
"""
import os
import shutil
from pathlib import Path

def cleanup_project():
    """Nettoyer le projet en supprimant les fichiers inutiles"""
    print("🧹 Nettoyage du projet NTPVIZ")
    print("=" * 60)
    
    # Fichiers à conserver
    keep_files = {
        'README.md',
        'CHANGELOG.md', 
        'LICENSE',
        'DEPLOY.md',
        'INSTALLATION_RAPIDE.md',
        'TROUBLESHOOTING.md',
        'README_FINAL.md',
        'README_TEST_UTILISATEURS.md'
    }
    
    # Patterns de fichiers à supprimer
    patterns_to_remove = [
        'RAPPORT_*.md',
        'ANALYSE_*.md', 
        'CORRECTION_*.md',
        'AMELIORATION_*.md',
        'AMELIORATIONS_*.md',
        'RESOLUTION_*.md',
        'SUPPRESSION_*.md',
        'VERIFICATION_*.md',
        'DESCENTE_*.md',
        'POSITIONNEMENT_*.md',
        'ETAT_*.md',
        'GESTION_*.md',
        'DIAGNOSTIC_*.md',
        'RESUME_*.md',
        'test_*.py',
        'test_*.html',
        'test_*.js',
        'analyse_*.py',
        'correction_*.py',
        'cookies.txt'
    ]
    
    files_removed = []
    files_kept = []
    
    # Parcourir tous les fichiers du projet
    for root, dirs, files in os.walk('.'):
        # Ignorer les dossiers .git et autres
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
        
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, '.')
            
            # Vérifier si le fichier doit être conservé
            if file in keep_files:
                files_kept.append(relative_path)
                continue
            
            # Vérifier si le fichier correspond à un pattern à supprimer
            should_remove = False
            for pattern in patterns_to_remove:
                if pattern.startswith('*'):
                    if file.endswith(pattern[1:]):
                        should_remove = True
                        break
                elif pattern.endswith('*'):
                    if file.startswith(pattern[:-1]):
                        should_remove = True
                        break
                elif pattern.startswith('*') and pattern.endswith('*'):
                    if pattern[1:-1] in file:
                        should_remove = True
                        break
                else:
                    if file == pattern:
                        should_remove = True
                        break
            
            if should_remove:
                try:
                    os.remove(file_path)
                    files_removed.append(relative_path)
                    print(f"🗑️  Supprimé: {relative_path}")
                except Exception as e:
                    print(f"❌ Erreur suppression {relative_path}: {e}")
    
    print(f"\n📊 Résumé du nettoyage:")
    print(f"  ✅ Fichiers conservés: {len(files_kept)}")
    print(f"  🗑️  Fichiers supprimés: {len(files_removed)}")
    
    if files_kept:
        print(f"\n📁 Fichiers conservés:")
        for file in files_kept:
            print(f"  ✅ {file}")
    
    print(f"\n🎉 Nettoyage terminé !")
    return len(files_removed)

def verify_cleanup():
    """Vérifier que les fichiers essentiels sont toujours présents"""
    print("\n🔍 Vérification post-nettoyage...")
    
    essential_files = [
        'app.py',
        'backend/',
        'frontend/',
        'config/',
        'deployment/',
        'README.md',
        'CHANGELOG.md',
        'LICENSE'
    ]
    
    missing_files = []
    for file in essential_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Fichiers essentiels manquants: {missing_files}")
        return False
    else:
        print("✅ Tous les fichiers essentiels sont présents")
        return True

def main():
    """Fonction principale"""
    print("🧹 Script de nettoyage du projet NTPVIZ")
    print("=" * 60)
    
    # Demander confirmation
    response = input("⚠️  Êtes-vous sûr de vouloir supprimer les fichiers de tests et de documentation ? (y/N): ")
    if response.lower() != 'y':
        print("❌ Nettoyage annulé")
        return
    
    # Effectuer le nettoyage
    files_removed = cleanup_project()
    
    # Vérifier le résultat
    if verify_cleanup():
        print(f"\n🎉 Nettoyage réussi ! {files_removed} fichiers supprimés")
    else:
        print(f"\n❌ Problème détecté lors du nettoyage")

if __name__ == "__main__":
    main() 